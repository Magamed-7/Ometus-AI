import pytest

import app.ai.assistant as assistant

from tests.test_ai_tools import admin_headers, ask, setup_doctor, setup_patient

FEEDBACK_URL = "/api/ai/feedback"
SUMMARY_URL = "/api/admin/ai-feedback"


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    async def fake_ask_llm(message, context, history=None, language="ru", system_prompt=None):
        return None

    monkeypatch.setattr(assistant, "ask_llm", fake_ask_llm)


async def get_history(client, headers, conversation_id):
    return (await client.get(f"/api/ai/history/{conversation_id}", headers=headers)).json()


async def ask_and_get_message_ids(client, db, headers):
    from sqlalchemy import select

    from app.models.model_conversation import Message

    body = (await ask(client, headers, "болит сердце")).json()
    messages = (
        (
            await db.execute(
                select(Message)
                .where(Message.conversation_id == body["conversation_id"])
                .order_by(Message.id)
            )
        )
        .scalars()
        .all()
    )

    return {message.role: message.id for message in messages}


async def test_patient_rates_assistant_reply(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    ids = await ask_and_get_message_ids(client, db, headers)

    response = await client.post(
        FEEDBACK_URL,
        json={"message_id": ids["assistant"], "feedback": "helpful"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["feedback"] == "helpful"


async def test_repeated_feedback_overwrites(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    ids = await ask_and_get_message_ids(client, db, headers)

    first = await client.post(
        FEEDBACK_URL,
        json={"message_id": ids["assistant"], "feedback": "helpful"},
        headers=headers,
    )
    second = await client.post(
        FEEDBACK_URL,
        json={"message_id": ids["assistant"], "feedback": "not_helpful", "reason": "не тот врач"},
        headers=headers,
    )

    assert first.json()["id"] == second.json()["id"]
    assert second.json()["feedback"] == "not_helpful"

    admin = await admin_headers(client, db, "fb1.admin@ometus.test")
    summary = (await client.get(SUMMARY_URL, headers=admin)).json()

    assert summary["total"] == 1
    assert summary["not_helpful"] == 1


async def test_own_message_cannot_be_rated(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    ids = await ask_and_get_message_ids(client, db, headers)

    response = await client.post(
        FEEDBACK_URL, json={"message_id": ids["user"], "feedback": "helpful"}, headers=headers
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "FEEDBACK_NOT_APPLICABLE"


async def test_foreign_message_cannot_be_rated(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    owner_id, owner_headers = await setup_patient(client, "owner@ometus.test")
    other_id, other_headers = await setup_patient(client, "other@ometus.test")

    ids = await ask_and_get_message_ids(client, db, owner_headers)

    response = await client.post(
        FEEDBACK_URL,
        json={"message_id": ids["assistant"], "feedback": "helpful"},
        headers=other_headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MESSAGE_NOT_FOUND"


async def test_invalid_feedback_value_rejected(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    ids = await ask_and_get_message_ids(client, db, headers)

    response = await client.post(
        FEEDBACK_URL,
        json={"message_id": ids["assistant"], "feedback": "отлично"},
        headers=headers,
    )

    assert response.status_code == 422


async def test_summary_shows_rate_and_complaints(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    first_id, first_headers = await setup_patient(client, "one@ometus.test")
    second_id, second_headers = await setup_patient(client, "two@ometus.test")

    good = await ask_and_get_message_ids(client, db, first_headers)
    bad = await ask_and_get_message_ids(client, db, second_headers)

    await client.post(
        FEEDBACK_URL,
        json={"message_id": good["assistant"], "feedback": "helpful"},
        headers=first_headers,
    )
    await client.post(
        FEEDBACK_URL,
        json={
            "message_id": bad["assistant"],
            "feedback": "not_helpful",
            "reason": "нужен был невролог",
        },
        headers=second_headers,
    )

    admin = await admin_headers(client, db, "fb2.admin@ometus.test")
    summary = (await client.get(SUMMARY_URL, headers=admin)).json()

    assert summary["total"] == 2
    assert summary["helpful_rate"] == 0.5
    assert summary["recent_complaints"][0]["reason"] == "нужен был невролог"


async def test_summary_requires_admin(client, db):
    patient_id, headers = await setup_patient(client)

    assert (await client.get(SUMMARY_URL, headers=headers)).status_code == 403
