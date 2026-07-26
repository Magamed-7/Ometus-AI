from datetime import date, timedelta

import pytest
from sqlalchemy import select

import app.ai.assistant as assistant
from app.ai import mcp_tools
from app.models.model_ai_log import AiQueryLog

from tests.conftest import verify_email

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
ASK_URL = "/api/ai/ask"
PATIENT_URL = "/api/users/me/patient"
MY_SCHEDULE_URL = "/api/schedules/me"
ADMIN_FILIALS_URL = "/api/admin/filials"
ADMIN_DEPARTMENTS_URL = "/api/admin/departments"
ADMIN_DOCTORS_URL = "/api/admin/doctors"

FILIAL_DATA = {"name": "Ometus Центр", "city": "Душанбе", "address": "ул. Рудаки 100"}

DOCTOR_DATA = {
    "email": "doctor@ometus.test",
    "password": "secret1234",
    "full_name": "Иванова Мария",
    "specialization": "Кардиолог",
}

WORKDAY = {"weekday": 0, "start_time": "09:00:00", "end_time": "10:00:00", "slot_duration": 20}


def next_workday():
    today = date.today()
    return today + timedelta(days=(WORKDAY["weekday"] - today.weekday()) % 7 or 7)


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    async def fake_ask_llm(message, context, history=None, language="ru", system_prompt=None):
        return None

    monkeypatch.setattr(assistant, "ask_llm", fake_ask_llm)


async def register(client, email, password="secret1234", **extra):
    response = await client.post(
        REGISTER_URL, json={"email": email, "password": password, **extra}
    )
    if response.status_code == 200:
        await verify_email(client, email)

    return response


async def auth_headers(client, email, password="secret1234"):
    login_response = await client.post(LOGIN_URL, json={"email": email, "password": password})
    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


async def admin_headers(client, db, email="admin@ometus.test"):
    from app.models.model_user import User

    await register(client, email)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.role = "admin"
    await db.commit()

    return await auth_headers(client, email)


async def setup_doctor(client, db, email=DOCTOR_DATA["email"], with_schedule=True):
    admin = await admin_headers(client, db)

    filial = await client.post(ADMIN_FILIALS_URL, json=FILIAL_DATA, headers=admin)
    department = await client.post(
        ADMIN_DEPARTMENTS_URL,
        json={"filial_id": filial.json()["id"], "name": "Кардиология"},
        headers=admin,
    )
    department_id = department.json()["id"]

    doctor = await client.post(
        ADMIN_DOCTORS_URL, json={**DOCTOR_DATA, "email": email}, headers=admin
    )
    doctor_id = doctor.json()["id"]

    await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor_id}/departments",
        json={"department_id": department_id},
        headers=admin,
    )

    headers = await auth_headers(client, email)

    if with_schedule:
        await client.post(
            MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
        )

    return doctor_id, department_id, headers


async def setup_patient(client, email="patient@ometus.test"):
    await register(client, email)
    headers = await auth_headers(client, email)
    profile = await client.get(PATIENT_URL, headers=headers)
    return profile.json()["id"], headers


async def ask(client, headers, message, **extra):
    return await client.post(ASK_URL, json={"message": message, **extra}, headers=headers)


async def make_appointment(db, patient_id, doctor_id, department_id, slot_time, status):
    from datetime import datetime

    from app.models.model_appointment import Appointment

    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department_id,
        date=date.today() - timedelta(days=7),
        time=datetime.strptime(slot_time, "%H:%M:%S").time(),
        status=status,
    )

    db.add(appointment)
    await db.commit()
    return appointment


async def test_emergency_message_blocks_booking_flow(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "У отца сильная боль в груди, он теряет сознание")

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "emergency"
    assert "скорую" in body["reply"]
    assert body["doctors"] is None


async def test_emergency_wins_over_specialization(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "болит сердце, кровотечение не останавливается")

    assert response.json()["action"] == "emergency"


async def test_unclear_request_asks_for_clarification(client, db):
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "мне нужен врач")

    assert response.status_code == 200
    assert response.json()["action"] == "clarify"


async def test_ambiguous_symptoms_ask_for_clarification(client, db):
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "болит живот и глаза")

    body = response.json()
    assert body["action"] == "clarify"
    assert "гастроэнтеролог" in body["reply"]
    assert "офтальмолог" in body["reply"]


async def test_symptom_maps_to_specialization_and_finds_doctors(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "у меня болит сердце и скачет давление")

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "doctors"
    assert body["specialization"] == "кардиолог"
    assert body["doctors"][0]["doctor_id"] == doctor_id
    assert body["doctors"][0]["full_name"] == "Иванова Мария"


async def test_direct_specialization_request(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "Найди свободного кардиолога завтра")

    body = response.json()
    assert body["action"] == "doctors"
    assert body["specialization"] == "кардиолог"


async def setup_therapist(client, db, email="therapist@ometus.test"):
    admin = await admin_headers(client, db)

    filial = await client.post(ADMIN_FILIALS_URL, json=FILIAL_DATA, headers=admin)
    department = await client.post(
        ADMIN_DEPARTMENTS_URL,
        json={"filial_id": filial.json()["id"], "name": "Терапия"},
        headers=admin,
    )
    department_id = department.json()["id"]

    doctor = await client.post(
        ADMIN_DOCTORS_URL,
        json={**DOCTOR_DATA, "email": email, "full_name": "Петров Пётр", "specialization": "Терапевт"},
        headers=admin,
    )
    doctor_id = doctor.json()["id"]

    await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor_id}/departments",
        json={"department_id": department_id},
        headers=admin,
    )

    return doctor_id, department_id


async def test_missing_specialist_offers_alternative(client, db):
    await setup_therapist(client, db)
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "нужен кардиолог")

    body = response.json()
    assert body["action"] == "clarify"
    assert body["alternatives"] == ["терапевт"]
    assert "терапевт" in body["reply"]


async def test_missing_specialist_without_alternatives_returns_error(client, db):
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "нужен стоматолог")

    body = response.json()
    assert body["action"] == "error"
    assert body["error_code"] == "DOCTORS_NOT_FOUND"


async def test_no_doctors_for_specialization(client, db):
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "нужен кардиолог")

    body = response.json()
    assert body["action"] == "error"
    assert body["error_code"] == "DOCTORS_NOT_FOUND"


async def test_slots_for_chosen_doctor(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await ask(
        client, headers, "какое время свободно", doctor_id=doctor_id, date=str(next_workday())
    )

    body = response.json()
    assert body["action"] == "slots"
    assert [slot["time"] for slot in body["slots"]] == ["09:00:00", "09:20:00", "09:40:00"]


async def test_slots_without_date_look_ahead(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "когда можно прийти", doctor_id=doctor_id)

    body = response.json()
    assert body["action"] == "slots"

    first_day = date.fromisoformat(body["slots"][0]["date"])
    assert first_day.weekday() == WORKDAY["weekday"]
    assert first_day >= date.today()


async def test_no_slots_for_doctor_without_schedule(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db, with_schedule=False)
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "когда можно прийти", doctor_id=doctor_id)

    body = response.json()
    assert body["action"] == "error"
    assert body["error_code"] == "NO_SLOTS"


async def test_unknown_doctor(client, db):
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "когда можно прийти", doctor_id=999)

    assert response.json()["error_code"] == "DOCTOR_NOT_FOUND"


async def test_confirm_books_appointment(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await ask(
        client,
        headers,
        "запиши меня на 09:00",
        doctor_id=doctor_id,
        date=str(next_workday()),
        time="09:00:00",
        confirm=True,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "booked"
    assert body["appointment"]["doctor_name"] == "Иванова Мария"
    assert body["appointment"]["department"] == "Кардиология"
    assert body["appointment"]["time"] == "09:00:00"
    assert "Номер записи" in body["reply"]

    listed = await client.get("/api/appointments/me", headers=headers)
    assert len(listed.json()) == 1


async def test_confirm_without_slot_details(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "запиши меня", doctor_id=doctor_id, confirm=True)

    assert response.json()["action"] == "clarify"


async def test_confirm_taken_slot(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    first_id, first_headers = await setup_patient(client)
    second_id, second_headers = await setup_patient(client, "patient2@ometus.test")
    booking = {
        "doctor_id": doctor_id,
        "date": str(next_workday()),
        "time": "09:00:00",
        "confirm": True,
    }

    await ask(client, first_headers, "запиши меня", **booking)
    response = await ask(client, second_headers, "запиши меня", **booking)

    body = response.json()
    assert body["action"] == "error"
    assert body["error_code"] == "SLOT_NOT_AVAILABLE"


async def test_confirm_past_slot(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await ask(
        client,
        headers,
        "запиши меня",
        doctor_id=doctor_id,
        date=str(date.today() - timedelta(days=7)),
        time="09:00:00",
        confirm=True,
    )

    assert response.json()["error_code"] == "SLOT_IN_PAST"


async def test_tool_refuses_to_book_for_another_patient(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    other_id, other_headers = await setup_patient(client, "patient2@ometus.test")

    from app.services import crud_patient

    patient = await crud_patient.get_by_id(patient_id, db)
    result = await mcp_tools.book_appointment(
        db, patient, doctor_id, other_id, next_workday(), "09:00:00"
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "PERMISSION_DENIED"


async def test_ai_is_forbidden_for_doctor(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)

    response = await ask(client, doctor_headers, "нужен кардиолог")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_ai_requires_auth(client, db):
    response = await client.post(ASK_URL, json={"message": "нужен кардиолог"})

    assert response.status_code == 401


async def test_tool_calls_are_logged(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await ask(client, headers, "нужен кардиолог")
    await ask(
        client,
        headers,
        "запиши меня",
        doctor_id=doctor_id,
        date=str(next_workday()),
        time="09:00:00",
        confirm=True,
    )

    result = await db.execute(select(AiQueryLog).order_by(AiQueryLog.id))
    logs = result.scalars().all()

    assert [log.tool_name for log in logs] == ["find_doctors", "book_appointment"]
    assert [log.status for log in logs] == ["ok", "ok"]
    assert logs[0].params_json == {"specialization": "кардиолог"}
    assert logs[1].params_json["doctor_id"] == doctor_id


async def test_failed_tool_call_is_logged_with_error(client, db):
    patient_id, headers = await setup_patient(client)

    await ask(client, headers, "нужен кардиолог")

    result = await db.execute(select(AiQueryLog))
    log = result.scalars().one()

    assert log.tool_name == "find_doctors"
    assert log.status == "error"
    assert log.message == "DOCTORS_NOT_FOUND"


async def test_emergency_is_logged(client, db):
    patient_id, headers = await setup_patient(client)

    await ask(client, headers, "человек без сознания")

    result = await db.execute(select(AiQueryLog))
    log = result.scalars().one()

    assert log.tool_name == "emergency_guard"
    assert log.status == "error"


async def book(client, headers, doctor_id, slot="09:00:00"):
    response = await ask(
        client,
        headers,
        "запиши меня",
        doctor_id=doctor_id,
        date=str(next_workday()),
        time=slot,
        confirm=True,
    )
    return response.json()["appointment"]["appointment_id"]


async def test_my_appointments_lists_bookings(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    await book(client, headers, doctor_id)

    response = await ask(client, headers, "мои записи", intent="my_appointments")

    body = response.json()
    assert body["action"] == "my_appointments"
    assert len(body["appointments"]) == 1
    assert body["appointments"][0]["doctor_id"] == doctor_id


async def test_my_appointments_empty(client, db):
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "мои записи", intent="my_appointments")

    body = response.json()
    assert body["action"] == "my_appointments"
    assert body["appointments"] == []
    assert "нет записей" in body["reply"]


async def test_cancel_appointment_via_ai(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    appointment_id = await book(client, headers, doctor_id)

    response = await ask(client, headers, "отмени запись", intent="cancel", appointment_id=appointment_id)

    assert response.json()["action"] == "cancelled"

    listed = await client.get("/api/appointments/me", headers=headers)
    assert listed.json()[0]["status"] == "cancelled"


async def test_cancel_frees_the_slot(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    appointment_id = await book(client, headers, doctor_id)

    await ask(client, headers, "отмени запись", intent="cancel", appointment_id=appointment_id)
    slots = await ask(client, headers, "когда можно прийти", doctor_id=doctor_id)

    times = [slot["time"] for slot in slots.json()["slots"]]
    assert "09:00:00" in times


async def test_cancel_unknown_appointment(client, db):
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "отмени запись", intent="cancel", appointment_id=999)

    assert response.json()["error_code"] == "APPOINTMENT_NOT_FOUND"


async def test_cancel_requires_appointment_id(client, db):
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "отмени запись", intent="cancel")

    assert response.json()["action"] == "clarify"


async def test_cancel_refuses_other_patient_appointment(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    owner_id, owner_headers = await setup_patient(client)
    other_id, other_headers = await setup_patient(client, "patient2@ometus.test")
    appointment_id = await book(client, owner_headers, doctor_id)

    response = await ask(
        client, other_headers, "отмени запись", intent="cancel", appointment_id=appointment_id
    )

    assert response.json()["error_code"] == "APPOINTMENT_NOT_FOUND"


async def test_reschedule_appointment_via_ai(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    appointment_id = await book(client, headers, doctor_id)

    response = await ask(
        client,
        headers,
        "перенеси на 09:20",
        intent="reschedule",
        appointment_id=appointment_id,
        date=str(next_workday()),
        time="09:20:00",
    )

    body = response.json()
    assert body["action"] == "rescheduled"
    assert body["appointment"]["time"] == "09:20:00"


async def test_reschedule_requires_details(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    appointment_id = await book(client, headers, doctor_id)

    response = await ask(
        client, headers, "перенеси запись", intent="reschedule", appointment_id=appointment_id
    )

    assert response.json()["action"] == "clarify"


async def test_reschedule_to_taken_slot(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    owner_id, owner_headers = await setup_patient(client)
    other_id, other_headers = await setup_patient(client, "patient2@ometus.test")
    appointment_id = await book(client, owner_headers, doctor_id, slot="09:00:00")
    await book(client, other_headers, doctor_id, slot="09:20:00")

    response = await ask(
        client,
        owner_headers,
        "перенеси на 09:20",
        intent="reschedule",
        appointment_id=appointment_id,
        date=str(next_workday()),
        time="09:20:00",
    )

    assert response.json()["error_code"] == "SLOT_NOT_AVAILABLE"


async def test_doctor_schedule_via_ai(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await ask(
        client, headers, "покажи расписание врача", intent="doctor_schedule", doctor_id=doctor_id
    )

    body = response.json()
    assert body["action"] == "doctor_schedule"
    assert body["schedule"][0]["weekday"] == 0


async def test_doctor_schedule_without_schedule(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db, with_schedule=False)
    patient_id, headers = await setup_patient(client)

    response = await ask(
        client, headers, "покажи расписание врача", intent="doctor_schedule", doctor_id=doctor_id
    )

    assert response.json()["error_code"] == "NO_SCHEDULE"


async def test_doctor_schedule_requires_doctor(client, db):
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "покажи расписание", intent="doctor_schedule")

    assert response.json()["action"] == "clarify"


async def test_tool_refuses_to_list_other_patient(client, db):
    patient_id, headers = await setup_patient(client)
    other_id, other_headers = await setup_patient(client, "patient2@ometus.test")

    from app.services import crud_patient

    patient = await crud_patient.get_by_id(patient_id, db)
    result = await mcp_tools.get_patient_appointments(db, patient, other_id)

    assert result["ok"] is False
    assert result["error"]["code"] == "PERMISSION_DENIED"


async def test_new_tool_calls_are_logged(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    appointment_id = await book(client, headers, doctor_id)

    await ask(client, headers, "отмени запись", intent="cancel", appointment_id=appointment_id)

    result = await db.execute(select(AiQueryLog).order_by(AiQueryLog.id))
    tools = [log.tool_name for log in result.scalars().all()]

    assert tools == ["book_appointment", "cancel_appointment"]


async def test_llm_reply_replaces_template(client, db, monkeypatch):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    async def fake_ask_llm(message, context, history=None, language="ru", system_prompt=None):
        return "Нашла для вас кардиолога, подскажите удобное время."

    monkeypatch.setattr(assistant, "ask_llm", fake_ask_llm)

    response = await ask(client, headers, "болит сердце")

    assert response.json()["reply"] == "Нашла для вас кардиолога, подскажите удобное время."


async def test_template_reply_used_when_llm_unavailable(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "болит сердце")

    assert "Иванова Мария" in response.json()["reply"]
    assert "кардиолог" in response.json()["reply"]


async def test_conversation_belongs_to_patient_not_user(client, db):
    from app.models.model_conversation import Conversation

    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    conversation_id = (await ask(client, headers, "болит сердце")).json()["conversation_id"]

    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))

    assert result.scalar_one().patient_id == patient_id


async def test_same_conversation_reused_between_requests(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    first = (await ask(client, headers, "болит сердце")).json()["conversation_id"]
    second = (await ask(client, headers, "а какое время свободно")).json()["conversation_id"]

    assert first == second


async def test_history_accumulates_messages(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    conversation_id = (await ask(client, headers, "болит сердце")).json()["conversation_id"]
    await ask(client, headers, "а какое время свободно", conversation_id=conversation_id)

    response = await client.get(f"/api/ai/history/{conversation_id}", headers=headers)

    body = response.json()
    assert response.status_code == 200
    assert [message["role"] for message in body["messages"]] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert body["messages"][0]["content"] == "болит сердце"
    assert body["messages"][2]["content"] == "а какое время свободно"


async def test_history_is_passed_to_llm(client, db, monkeypatch):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    seen = []

    async def fake_ask_llm(message, context, history=None, language="ru", system_prompt=None):
        seen.append(history or [])
        return None

    monkeypatch.setattr(assistant, "ask_llm", fake_ask_llm)

    conversation_id = (await ask(client, headers, "болит сердце")).json()["conversation_id"]
    await ask(client, headers, "болит сердце", conversation_id=conversation_id)

    assert seen[0] == []
    assert [message.content for message in seen[-1]][0] == "болит сердце"


async def test_foreign_conversation_id_is_ignored(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    owner_id, owner_headers = await setup_patient(client, "owner@ometus.test")
    other_id, other_headers = await setup_patient(client, "other@ometus.test")

    owner_conversation = (await ask(client, owner_headers, "болит сердце")).json()[
        "conversation_id"
    ]

    response = await ask(
        client, other_headers, "болит сердце", conversation_id=owner_conversation
    )

    assert response.json()["conversation_id"] != owner_conversation


async def test_history_of_foreign_conversation_is_denied(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    owner_id, owner_headers = await setup_patient(client, "owner@ometus.test")
    other_id, other_headers = await setup_patient(client, "other@ometus.test")

    owner_conversation = (await ask(client, owner_headers, "болит сердце")).json()[
        "conversation_id"
    ]

    response = await client.get(
        f"/api/ai/history/{owner_conversation}", headers=other_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"


SUGGESTION_URL = "/api/ai/suggestion"
METRICS_URL = "/api/admin/ai-metrics"


ASK_ASYNC_URL = "/api/ai/ask-async"
TASKS_URL = "/api/ai/tasks"


async def test_async_ask_returns_task_and_completes(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    created = await client.post(
        ASK_ASYNC_URL, json={"message": "болит сердце"}, headers=headers
    )

    task_id = created.json()["id"]
    assert created.status_code == 200

    task = (await client.get(f"{TASKS_URL}/{task_id}", headers=headers)).json()

    assert task["status"] == "done"
    assert task["result_json"]["action"] == "doctors"
    assert task["result_json"]["specialization"] == "кардиолог"
    assert task["finished_at"] is not None


async def test_async_task_records_failure(client, db, monkeypatch):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    async def boom(data, patient, session):
        raise RuntimeError("модель недоступна")

    monkeypatch.setattr(assistant, "ask", boom)

    created = await client.post(
        ASK_ASYNC_URL, json={"message": "болит сердце"}, headers=headers
    )
    task_id = created.json()["id"]

    task = (await client.get(f"{TASKS_URL}/{task_id}", headers=headers)).json()

    assert task["status"] == "failed"
    assert "модель недоступна" in task["error"]


async def test_foreign_task_is_not_visible(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    owner_id, owner_headers = await setup_patient(client, "owner@ometus.test")
    other_id, other_headers = await setup_patient(client, "other@ometus.test")

    created = await client.post(
        ASK_ASYNC_URL, json={"message": "болит сердце"}, headers=owner_headers
    )
    task_id = created.json()["id"]

    response = await client.get(f"{TASKS_URL}/{task_id}", headers=other_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TASK_NOT_FOUND"


async def test_unknown_task_returns_404(client, db):
    patient_id, headers = await setup_patient(client)

    response = await client.get(f"{TASKS_URL}/does-not-exist", headers=headers)

    assert response.status_code == 404


def intent_json(primary, confidence=0.9, **parameters):
    import json as json_module

    return json_module.dumps(
        {"primary": primary, "confidence": confidence, "parameters": parameters}
    )


def use_intent(monkeypatch, raw):
    async def fake_ask_llm(message, context, history=None, language="ru", system_prompt=None):
        return raw if system_prompt else None

    monkeypatch.setattr(assistant, "ask_llm", fake_ask_llm)


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "не json вовсе",
        '{"primary": "нет такого", "confidence": 0.9}',
        '{"primary": "cancel", "confidence": 0.2}',
        '{"primary": "cancel", "confidence": "высокая"}',
        "{битый json",
    ],
)
def test_broken_intent_is_ignored(raw):
    assert assistant.parse_intent(raw) is None


def test_intent_parsed_from_markdown_block():
    raw = '```json\n{"primary": "cancel", "confidence": 0.9, "parameters": {"appointment_id": 5}}\n```'

    parsed = assistant.parse_intent(raw)

    assert parsed["primary"] == "cancel"
    assert parsed["parameters"]["appointment_id"] == 5


async def test_detected_intent_cancels_appointment(client, db, monkeypatch):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    booked = await ask(
        client,
        headers,
        "запиши меня",
        confirm=True,
        doctor_id=doctor_id,
        date=str(next_workday()),
        time="09:00:00",
    )
    appointment_id = booked.json()["appointment"]["appointment_id"]

    use_intent(monkeypatch, intent_json("cancel", appointment_id=appointment_id))

    body = (await ask(client, headers, f"отмени запись номер {appointment_id}")).json()

    assert body["action"] == "cancelled"
    assert body["detected_intent"] == "cancel"
    assert body["intent_confidence"] == 0.9


async def test_detected_cancel_without_id_asks_instead_of_guessing(client, db, monkeypatch):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await ask(
        client,
        headers,
        "запиши меня",
        confirm=True,
        doctor_id=doctor_id,
        date=str(next_workday()),
        time="09:00:00",
    )

    use_intent(monkeypatch, intent_json("cancel"))

    body = (await ask(client, headers, "отмени мою запись")).json()

    assert body["action"] == "clarify"


async def test_detected_intent_never_books(client, db, monkeypatch):
    from app.models.model_appointment import Appointment

    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    use_intent(
        monkeypatch,
        intent_json(
            "find_doctor",
            doctor_id=doctor_id,
            date=str(next_workday()),
            time="09:00:00",
        ),
    )

    body = (await ask(client, headers, "запиши меня к кардиологу на завтра")).json()

    booked = (await db.execute(select(Appointment))).scalars().all()

    assert body["action"] != "booked"
    assert booked == []


async def test_explicit_intent_wins_over_model(client, db, monkeypatch):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    use_intent(monkeypatch, intent_json("cancel", appointment_id=999))

    body = (await ask(client, headers, "мои записи", intent="my_appointments")).json()

    assert body["action"] == "my_appointments"
    assert body["detected_intent"] is None


async def test_llm_calls_are_recorded(client, db, monkeypatch):
    from app.ai import metrics
    from app.models.model_ai_metric import AiLlmCall

    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    async def fake_ask_llm(message, context, history=None, language="ru", system_prompt=None):
        metrics.record_call("groq", "llama-test", True, 42, 100, 20)
        return "ответ модели"

    monkeypatch.setattr(assistant, "ask_llm", fake_ask_llm)

    await ask(client, headers, "болит сердце")

    saved = (await db.execute(select(AiLlmCall))).scalars().all()

    assert len(saved) == 1
    assert saved[0].provider == "groq"
    assert saved[0].model == "llama-test"
    assert saved[0].success is True
    assert saved[0].prompt_tokens == 100


async def test_metrics_summary_for_admin(client, db, monkeypatch):
    from app.ai import metrics

    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    async def fake_ask_llm(message, context, history=None, language="ru", system_prompt=None):
        metrics.record_call("groq", "llama-test", False, 10, error="boom")
        metrics.record_call("gemini", "gemini-test", True, 30, 50, 10)
        return "ответ модели"

    monkeypatch.setattr(assistant, "ask_llm", fake_ask_llm)

    await ask(client, headers, "болит сердце")

    admin = await admin_headers(client, db, "metrics.admin@ometus.test")
    body = (await client.get(METRICS_URL, headers=admin)).json()

    by_provider = {row["provider"]: row for row in body}

    assert by_provider["groq"]["failed"] == 1
    assert by_provider["groq"]["success_rate"] == 0.0
    assert by_provider["gemini"]["succeeded"] == 1
    assert by_provider["gemini"]["completion_tokens"] == 10
    assert by_provider["gemini"]["avg_duration_ms"] == 30


async def test_metrics_require_admin(client, db):
    patient_id, headers = await setup_patient(client)

    assert (await client.get(METRICS_URL, headers=headers)).status_code == 403


async def test_metrics_reject_invalid_range(client, db):
    admin = await admin_headers(client, db, "range.admin@ometus.test")

    response = await client.get(
        f"{METRICS_URL}?date_from=2026-08-01&date_to=2026-07-01", headers=admin
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"


async def make_past_visit(db, patient_id, doctor_id, department_id, days_ago, status="completed"):
    from datetime import time as clock

    from app.models.model_appointment import Appointment

    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department_id,
        date=date.today() - timedelta(days=days_ago),
        time=clock(9, 0),
        status=status,
    )

    db.add(appointment)
    await db.commit()
    return appointment


async def test_no_suggestion_without_visits(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await client.get(SUGGESTION_URL, headers=headers)

    assert response.status_code == 200
    assert response.json() is None


async def test_no_suggestion_for_recent_visit(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await make_past_visit(db, patient_id, doctor_id, department_id, 30)

    assert (await client.get(SUGGESTION_URL, headers=headers)).json() is None


async def test_suggestion_for_overdue_visit(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await make_past_visit(db, patient_id, doctor_id, department_id, 200)

    body = (await client.get(SUGGESTION_URL, headers=headers)).json()

    assert body["doctor_id"] == doctor_id
    assert body["specialization"] == DOCTOR_DATA["specialization"]
    assert "6 мес. назад" in body["reply"]


async def test_no_suggestion_when_already_booked(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await make_past_visit(db, patient_id, doctor_id, department_id, 200)
    await make_past_visit(db, patient_id, doctor_id, department_id, -5, status="booked")

    assert (await client.get(SUGGESTION_URL, headers=headers)).json() is None


async def test_no_suggestion_for_dismissed_doctor(client, db):
    from app.models.model_doctor import Doctor

    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await make_past_visit(db, patient_id, doctor_id, department_id, 200)

    doctor = (await db.execute(select(Doctor).where(Doctor.id == doctor_id))).scalar_one()
    doctor.dismissed_at = date.today()
    await db.commit()

    assert (await client.get(SUGGESTION_URL, headers=headers)).json() is None


async def test_suggestion_is_localised(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await make_past_visit(db, patient_id, doctor_id, department_id, 200)

    body = (await client.get(f"{SUGGESTION_URL}?language=en", headers=headers)).json()

    assert body["reply"].startswith("You saw")


@pytest.mark.parametrize(
    "text, expected",
    [
        ("нужен кардиолог", "ru"),
        ("дилам дард мекунад", "tg"),
        ("ман духтур мехоҳам", "tg"),
        ("i need a cardiologist", "en"),
    ],
)
def test_language_detection(text, expected):
    from app.ai.i18n import detect_language

    assert detect_language(text) == expected


def test_explicit_language_wins_over_detection():
    from app.ai.i18n import pick_language

    assert pick_language("en", "нужен кардиолог") == "en"
    assert pick_language(None, "нужен кардиолог") == "ru"
    assert pick_language("xx", "нужен кардиолог") == "ru"


@pytest.mark.parametrize(
    "text, language",
    [
        ("дилам дард мекунад", "tg"),
        ("my heart hurts", "en"),
        ("болит сердце", "ru"),
    ],
)
def test_specialization_matched_in_every_language(text, language):
    from app.ai.specialization_map import match_specializations

    assert match_specializations(text, language) == ["кардиолог"]


@pytest.mark.parametrize(
    "text",
    ["беҳуш афтод", "he is unconscious", "отец без сознания"],
)
def test_emergency_detected_in_every_language(text):
    from app.ai.emergency_guard import is_emergency

    assert is_emergency(text) is True


async def test_english_request_answered_in_english(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    body = (await ask(client, headers, "my heart hurts")).json()

    assert body["language"] == "en"
    assert body["specialization"] == "кардиолог"
    assert body["reply"].startswith("Doctors for")


async def test_tajik_request_answered_in_tajik(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    body = (await ask(client, headers, "дилам дард мекунад")).json()

    assert body["language"] == "tg"
    assert body["specialization"] == "кардиолог"
    assert "қабул мекунанд" in body["reply"]


async def test_emergency_answered_in_patient_language(client, db):
    patient_id, headers = await setup_patient(client)

    body = (await ask(client, headers, "he is unconscious")).json()

    assert body["action"] == "emergency"
    assert body["language"] == "en"
    assert "ambulance" in body["reply"]


async def test_explicit_language_overrides_text(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    body = (await ask(client, headers, "болит сердце", language="en")).json()

    assert body["language"] == "en"
    assert body["reply"].startswith("Doctors for")


def test_sort_slots_by_preference_puts_liked_hours_first():
    slots = [
        {"date": "2026-08-03", "time": "09:00:00"},
        {"date": "2026-08-03", "time": "15:00:00"},
        {"date": "2026-08-03", "time": "16:00:00"},
    ]

    sorted_slots = assistant.sort_slots_by_preference(slots, {15: 4, 9: -2})

    assert [slot["time"] for slot in sorted_slots] == ["15:00:00", "16:00:00", "09:00:00"]
    assert sorted_slots[0]["preferred"] is True
    assert sorted_slots[2]["preferred"] is False


def test_sort_slots_keeps_order_without_history():
    slots = [
        {"date": "2026-08-03", "time": "09:00:00"},
        {"date": "2026-08-03", "time": "15:00:00"},
    ]

    assert assistant.sort_slots_by_preference(slots, {}) == slots


async def test_hour_preferences_count_visits_and_penalise_cancels(client, db):
    from app.services import crud_appointment

    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await make_appointment(db, patient_id, doctor_id, department_id, "10:00:00", "completed")
    await make_appointment(db, patient_id, doctor_id, department_id, "10:30:00", "booked")
    await make_appointment(db, patient_id, doctor_id, department_id, "17:00:00", "cancelled")

    preferences = await crud_appointment.get_hour_preferences(patient_id, db)

    assert preferences == {10: 3, 17: -1}


async def test_slots_are_reordered_by_patient_habits(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db, with_schedule=False)
    patient_id, headers = await setup_patient(client)

    await client.post(
        MY_SCHEDULE_URL,
        json={
            "weekday": WORKDAY["weekday"],
            "start_time": "09:00:00",
            "end_time": "16:00:00",
            "slot_duration": 60,
            "department_id": department_id,
        },
        headers=doctor_headers,
    )

    await make_appointment(db, patient_id, doctor_id, department_id, "15:00:00", "completed")

    body = (
        await ask(client, headers, "какое время свободно", doctor_id=doctor_id, date=str(next_workday()))
    ).json()

    assert body["slots"][0]["time"] == "15:00:00"
    assert body["slots"][0]["preferred"] is True


@pytest.mark.parametrize(
    "message, expected",
    [
        ("нужен кардиолог", 0),
        ("высокая температура и тошнота", 1),
        ("острая боль в колене", 2),
        ("отец без сознания", 3),
    ],
)
def test_symptom_severity_levels(message, expected):
    from app.ai.emergency_guard import assess_symptom_severity

    assert assess_symptom_severity(message) == expected


async def test_emergency_reports_critical_severity(client, db):
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "отец без сознания")

    assert response.json()["severity"] == 3


async def test_high_severity_adds_note_to_reply(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await ask(client, headers, "острая боль в сердце")

    body = response.json()
    assert body["severity"] == 2
    assert body["reply"].startswith("Судя по описанию, тянуть не стоит")


async def test_low_severity_reply_has_no_note(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    body = (await ask(client, headers, "нужен кардиолог")).json()

    assert body["severity"] == 0
    assert not body["reply"].startswith("Судя по описанию")


async def test_severity_is_logged(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await ask(client, headers, "острая боль в сердце")

    result = await db.execute(select(AiQueryLog).order_by(AiQueryLog.id.desc()))

    assert result.scalars().first().severity == 2


async def test_several_conversations_do_not_break_lookup(client, db):
    from app.services import crud_conversation

    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await crud_conversation.create_conversation(patient_id, db)
    await crud_conversation.create_conversation(patient_id, db)

    response = await ask(client, headers, "болит сердце")

    assert response.status_code == 200
