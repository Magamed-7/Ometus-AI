import pytest
from sqlalchemy import select

import app.ai.assistant as assistant
from app.models.model_ai_log import AiQueryLog

from tests.test_ai_tools import (
    admin_headers,
    ask,
    setup_doctor,
    setup_patient,
)

RECORDS_URL = "/api/patients/me/medical-records"
CONSENT_URL = "/api/patients/me/ai-consent"

CONDITION = {"kind": "condition", "name": "гипертония", "note": "с 2020 года"}
ALLERGY = {"kind": "allergy", "name": "пенициллин"}


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    async def fake_ask_llm(message, context, history=None, language="ru", system_prompt=None):
        return None

    monkeypatch.setattr(assistant, "ask_llm", fake_ask_llm)


async def test_patient_manages_own_records(client, db):
    patient_id, headers = await setup_patient(client)

    created = await client.post(RECORDS_URL, json=CONDITION, headers=headers)
    assert created.status_code == 200
    assert created.json()["name"] == "гипертония"

    listed = (await client.get(RECORDS_URL, headers=headers)).json()
    assert [record["name"] for record in listed] == ["гипертония"]

    deleted = await client.delete(f"{RECORDS_URL}/{created.json()['id']}", headers=headers)
    assert deleted.status_code == 200
    assert (await client.get(RECORDS_URL, headers=headers)).json() == []


async def test_foreign_record_cannot_be_deleted(client, db):
    owner_id, owner_headers = await setup_patient(client, "owner@ometus.test")
    other_id, other_headers = await setup_patient(client, "other@ometus.test")

    created = await client.post(RECORDS_URL, json=CONDITION, headers=owner_headers)
    record_id = created.json()["id"]

    response = await client.delete(f"{RECORDS_URL}/{record_id}", headers=other_headers)

    assert response.status_code == 404
    assert (await client.get(RECORDS_URL, headers=owner_headers)).json() != []


async def test_records_are_not_visible_to_other_patients(client, db):
    owner_id, owner_headers = await setup_patient(client, "owner@ometus.test")
    other_id, other_headers = await setup_patient(client, "other@ometus.test")

    await client.post(RECORDS_URL, json=CONDITION, headers=owner_headers)

    assert (await client.get(RECORDS_URL, headers=other_headers)).json() == []


async def test_admin_has_no_access_to_medical_records(client, db):
    admin = await admin_headers(client, db, "records.admin@ometus.test")

    response = await client.get(RECORDS_URL, headers=admin)

    assert response.status_code == 403


async def test_consent_is_off_by_default(client, db):
    patient_id, headers = await setup_patient(client)

    assert (await client.get(CONSENT_URL, headers=headers)).json()["ai_consent"] is False


async def test_consent_can_be_switched(client, db):
    patient_id, headers = await setup_patient(client)

    granted = await client.put(CONSENT_URL, json={"allowed": True}, headers=headers)
    assert granted.json()["ai_consent"] is True

    revoked = await client.put(CONSENT_URL, json={"allowed": False}, headers=headers)
    assert revoked.json()["ai_consent"] is False


async def test_emr_not_used_without_consent(client, db, monkeypatch):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await client.post(RECORDS_URL, json=CONDITION, headers=headers)

    seen = []

    async def spy_ask_llm(message, context, history=None, language="ru", system_prompt=None):
        seen.append(context)
        return None

    monkeypatch.setattr(assistant, "ask_llm", spy_ask_llm)

    body = (await ask(client, headers, "болит сердце")).json()

    assert body["emr_used"] is False
    assert all(assistant.EMR_CONTEXT_KEY not in context for context in seen)


async def test_emr_passed_to_model_with_consent(client, db, monkeypatch):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await client.post(RECORDS_URL, json=CONDITION, headers=headers)
    await client.post(RECORDS_URL, json=ALLERGY, headers=headers)
    await client.put(CONSENT_URL, json={"allowed": True}, headers=headers)

    seen = []

    async def spy_ask_llm(message, context, history=None, language="ru", system_prompt=None):
        seen.append(context)
        return None

    monkeypatch.setattr(assistant, "ask_llm", spy_ask_llm)

    body = (await ask(client, headers, "болит сердце")).json()

    emr = seen[-1][assistant.EMR_CONTEXT_KEY]
    assert body["emr_used"] is True
    assert emr["condition"] == ["гипертония (с 2020 года)"]
    assert emr["allergy"] == ["пенициллин"]


async def test_emr_content_never_reaches_audit_log(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await client.post(RECORDS_URL, json=CONDITION, headers=headers)
    await client.put(CONSENT_URL, json={"allowed": True}, headers=headers)

    await ask(client, headers, "болит сердце")

    logs = (await db.execute(select(AiQueryLog))).scalars().all()
    dumped = str([log.params_json for log in logs])

    assert "гипертония" not in dumped
    assert logs[0].params_json["emr_used"] is True


async def test_prompt_forbids_commenting_on_diagnoses(client, db):
    prompt = assistant.build_system_prompt("ru", with_emr=True)

    assert "запрещено комментировать заболевания" in prompt
    assert assistant.EMR_PROMPT_NOTE not in assistant.build_system_prompt("ru")
