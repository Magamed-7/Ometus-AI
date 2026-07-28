import json
from datetime import date, time

from app.ai import staff
from app.models.model_appointment import Appointment

from tests.conftest import verify_email

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
PATIENT_URL = "/api/users/me/patient"
ADMIN_FILIALS_URL = "/api/admin/filials"
ADMIN_DEPARTMENTS_URL = "/api/admin/departments"
ADMIN_DOCTORS_URL = "/api/admin/doctors"
DOCTOR_ASK_URL = "/api/ai/doctor/ask"
ADMIN_ASK_URL = "/api/ai/admin/ask"

FILIAL_DATA = {"name": "Ometus Центр", "city": "Душанбе", "address": "ул. Рудаки 100"}


async def register(client, email, password="secret1234"):
    response = await client.post(REGISTER_URL, json={"email": email, "password": password})
    if response.status_code == 200:
        await verify_email(client, email)

    return response


async def auth_headers(client, email, password="secret1234"):
    login = await client.post(LOGIN_URL, json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def admin_headers(client, db):
    from sqlalchemy import select

    from app.models.model_user import User

    await register(client, "admin@ometus.test")
    user = (
        await db.execute(select(User).where(User.email == "admin@ometus.test"))
    ).scalar_one()
    user.role = "admin"
    await db.commit()
    return await auth_headers(client, "admin@ometus.test")


async def setup_clinic(client, db):
    admin = await admin_headers(client, db)
    filial = await client.post(ADMIN_FILIALS_URL, json=FILIAL_DATA, headers=admin)
    department = await client.post(
        ADMIN_DEPARTMENTS_URL,
        json={"filial_id": filial.json()["id"], "name": "Кардиология"},
        headers=admin,
    )
    department_id = department.json()["id"]

    first = await client.post(
        ADMIN_DOCTORS_URL,
        json={
            "email": "doctor@ometus.test",
            "password": "secret1234",
            "full_name": "Иванова Мария",
            "specialization": "Кардиолог",
        },
        headers=admin,
    )
    second = await client.post(
        ADMIN_DOCTORS_URL,
        json={
            "email": "doctor2@ometus.test",
            "password": "secret1234",
            "full_name": "Каримов Ахмад",
            "specialization": "Невролог",
        },
        headers=admin,
    )

    await register(client, "patient@ometus.test")
    patient_headers = await auth_headers(client, "patient@ometus.test")
    patient = await client.get(PATIENT_URL, headers=patient_headers)

    return {
        "admin": admin,
        "department_id": department_id,
        "first_doctor": first.json()["id"],
        "second_doctor": second.json()["id"],
        "patient_id": patient.json()["id"],
    }


def stub_llm(monkeypatch, intent_payload, reply="Готовый ответ модели"):
    async def fake_ask_llm(message, context, history=None, language="ru", system_prompt=None):
        if system_prompt and "JSON" in system_prompt:
            return json.dumps(intent_payload)

        return reply

    monkeypatch.setattr(staff, "ask_llm", fake_ask_llm)


async def add_appointment(db, clinic, doctor_id, day, slot_time, status="booked"):
    db.add(
        Appointment(
            patient_id=clinic["patient_id"],
            doctor_id=doctor_id,
            department_id=clinic["department_id"],
            date=day,
            time=slot_time,
            status=status,
        )
    )
    await db.commit()


async def test_doctor_asks_who_is_booked_today(client, db, monkeypatch):
    from app.core.clock import clinic_today

    clinic = await setup_clinic(client, db)
    await add_appointment(db, clinic, clinic["first_doctor"], clinic_today(), time(9, 0))
    stub_llm(monkeypatch, {"intent": "today", "confidence": 0.9})
    headers = await auth_headers(client, "doctor@ometus.test")

    response = await client.post(DOCTOR_ASK_URL, json={"message": "кто у меня сегодня"}, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "day"
    assert body["data"]["всего_записей"] == 1


async def test_doctor_never_sees_another_doctors_patients(client, db, monkeypatch):
    from app.core.clock import clinic_today

    clinic = await setup_clinic(client, db)
    await add_appointment(db, clinic, clinic["second_doctor"], clinic_today(), time(10, 0))
    stub_llm(monkeypatch, {"intent": "today", "confidence": 0.9})
    headers = await auth_headers(client, "doctor@ometus.test")

    response = await client.post(DOCTOR_ASK_URL, json={"message": "кто у меня сегодня"}, headers=headers)

    body = response.json()
    assert body["data"]["всего_записей"] == 0
    assert body["data"]["приёмы"] == []


async def test_patient_names_are_not_sent_to_the_model(client, db, monkeypatch):
    from app.core.clock import clinic_today

    clinic = await setup_clinic(client, db)
    await add_appointment(db, clinic, clinic["first_doctor"], clinic_today(), time(9, 0))

    seen = {}

    async def fake_ask_llm(message, context, history=None, language="ru", system_prompt=None):
        if system_prompt and "JSON" in system_prompt:
            return json.dumps({"intent": "today", "confidence": 0.9})

        seen["context"] = context
        return "Ответ"

    monkeypatch.setattr(staff, "ask_llm", fake_ask_llm)
    headers = await auth_headers(client, "doctor@ometus.test")

    await client.post(DOCTOR_ASK_URL, json={"message": "кто у меня сегодня"}, headers=headers)

    sent = json.dumps(seen["context"], ensure_ascii=False, default=str)
    assert "patient_name" not in sent
    assert "приёмы" not in sent


async def test_doctor_gets_a_clarifying_answer_when_intent_is_unclear(client, db, monkeypatch):
    await setup_clinic(client, db)
    stub_llm(monkeypatch, {"intent": "today", "confidence": 0.2})
    headers = await auth_headers(client, "doctor@ometus.test")

    response = await client.post(DOCTOR_ASK_URL, json={"message": "ну это самое"}, headers=headers)

    assert response.json()["action"] == "clarify"


async def test_doctor_assistant_is_closed_to_patients(client, db):
    await setup_clinic(client, db)
    headers = await auth_headers(client, "patient@ometus.test")

    response = await client.post(DOCTOR_ASK_URL, json={"message": "кто у меня сегодня"}, headers=headers)

    assert response.status_code == 403


async def test_admin_asks_for_the_busiest_doctors(client, db, monkeypatch):
    from app.core.clock import clinic_today

    clinic = await setup_clinic(client, db)
    await add_appointment(db, clinic, clinic["first_doctor"], clinic_today(), time(9, 0), "completed")
    await add_appointment(db, clinic, clinic["first_doctor"], clinic_today(), time(9, 30), "completed")
    stub_llm(monkeypatch, {"intent": "busiest", "confidence": 0.9, "days": 7})

    response = await client.post(
        ADMIN_ASK_URL, json={"message": "кто больше всех принимал"}, headers=clinic["admin"]
    )

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "busiest"
    assert body["data"]["врачи"][0]["имя"] == "Иванова Мария"
    assert body["data"]["врачи"][0]["приёмов"] == 2


async def test_admin_asks_how_much_the_assistant_costs(client, db, monkeypatch):
    clinic = await setup_clinic(client, db)
    stub_llm(monkeypatch, {"intent": "ai_spend", "confidence": 0.9, "days": 30})

    response = await client.post(
        ADMIN_ASK_URL, json={"message": "сколько потратили на ии"}, headers=clinic["admin"]
    )

    body = response.json()
    assert body["action"] == "ai_spend"
    assert "запросов" in body["data"]
    assert "потрачено_usd" in body["data"]


async def test_admin_assistant_is_closed_to_doctors(client, db):
    await setup_clinic(client, db)
    headers = await auth_headers(client, "doctor@ometus.test")

    response = await client.post(ADMIN_ASK_URL, json={"message": "сводка"}, headers=headers)

    assert response.status_code == 403


async def test_staff_answer_falls_back_to_plain_numbers_without_the_model(client, db, monkeypatch):
    from app.core.clock import clinic_today

    clinic = await setup_clinic(client, db)
    await add_appointment(db, clinic, clinic["first_doctor"], clinic_today(), time(9, 0))

    async def dead_llm(message, context, history=None, language="ru", system_prompt=None):
        if system_prompt and "JSON" in system_prompt:
            return json.dumps({"intent": "today", "confidence": 0.9})

        return None

    monkeypatch.setattr(staff, "ask_llm", dead_llm)
    headers = await auth_headers(client, "doctor@ometus.test")

    response = await client.post(DOCTOR_ASK_URL, json={"message": "кто сегодня"}, headers=headers)

    assert response.status_code == 200
    assert "1" in response.json()["reply"]


async def test_period_is_capped_to_a_year():
    date_from, date_to, days = staff.period({"days": 5000})

    assert days == 366
    assert (date_to - date_from).days == 365


async def test_hallucinated_date_from_the_model_is_ignored():
    from datetime import timedelta

    from app.core.clock import clinic_today

    today = clinic_today()

    assert staff.parse_date("2024-03-16") is None
    assert staff.parse_date("не дата") is None
    assert staff.parse_date(None) is None
    assert staff.parse_date(today.isoformat()) == today
    assert staff.parse_date((today + timedelta(days=5)).isoformat()) == today + timedelta(days=5)


async def test_doctor_free_slots_use_today_when_the_model_invents_a_date(client, db, monkeypatch):
    from app.core.clock import clinic_today

    await setup_clinic(client, db)
    stub_llm(monkeypatch, {"intent": "free", "confidence": 0.9, "date": "2024-03-16"})
    headers = await auth_headers(client, "doctor@ometus.test")

    response = await client.post(DOCTOR_ASK_URL, json={"message": "где свободные окна"}, headers=headers)

    assert response.json()["data"]["дата"] == clinic_today().isoformat()
