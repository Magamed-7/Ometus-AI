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
    async def fake_ask_llm(message, context, history=None):
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


async def admin_headers(client, db):
    from app.models.model_user import User

    await register(client, "admin@ometus.test")

    result = await db.execute(select(User).where(User.email == "admin@ometus.test"))
    user = result.scalar_one()
    user.role = "admin"
    await db.commit()

    return await auth_headers(client, "admin@ometus.test")


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
    assert body["slots"][0]["date"] == str(next_workday())


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

    async def fake_ask_llm(message, context, history=None):
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
