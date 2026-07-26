from tests.conftest import verify_email

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
SCHEDULES_URL = "/api/schedules"
MY_SCHEDULE_URL = "/api/schedules/me"
MY_ABSENCES_URL = "/api/schedules/me/absences"
MY_DATES_URL = "/api/schedules/me/dates"
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


async def register(client, email, password="secret1234"):
    response = await client.post(REGISTER_URL, json={"email": email, "password": password})
    if response.status_code == 200:
        await verify_email(client, email)

    return response


async def auth_headers(client, email, password="secret1234"):
    login_response = await client.post(LOGIN_URL, json={"email": email, "password": password})
    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


async def admin_headers(client, db):
    from sqlalchemy import select

    from app.models.model_user import User

    await register(client, "admin@ometus.test")

    result = await db.execute(select(User).where(User.email == "admin@ometus.test"))
    user = result.scalar_one()
    user.role = "admin"
    await db.commit()

    return await auth_headers(client, "admin@ometus.test")


async def setup_doctor(client, db, email=DOCTOR_DATA["email"], assign=True):
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

    if assign:
        await client.post(
            f"{ADMIN_DOCTORS_URL}/{doctor_id}/departments",
            json={"department_id": department_id},
            headers=admin,
        )

    headers = await auth_headers(client, email)
    return doctor_id, department_id, headers


async def test_create_schedule(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)

    response = await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["doctor_id"] == doctor_id
    assert body["weekday"] == 0
    assert body["slot_duration"] == 20


async def test_create_schedule_invalid_time_range(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)

    response = await client.post(
        MY_SCHEDULE_URL,
        json={**WORKDAY, "department_id": department_id, "start_time": "18:00:00", "end_time": "09:00:00"},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_TIME_RANGE"


async def test_create_schedule_in_foreign_department(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db, assign=False)

    response = await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DOCTOR_NOT_IN_DEPARTMENT"


async def test_create_schedule_twice_on_same_weekday(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )

    response = await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SCHEDULE_ALREADY_EXISTS"


async def test_create_schedule_forbidden_for_patient(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    await register(client, "patient@ometus.test")
    patient_headers = await auth_headers(client, "patient@ometus.test")

    response = await client.post(
        MY_SCHEDULE_URL,
        json={**WORKDAY, "department_id": department_id},
        headers=patient_headers,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_update_schedule(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    created = await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )
    schedule_id = created.json()["id"]

    response = await client.put(
        f"{MY_SCHEDULE_URL}/{schedule_id}", json={"end_time": "12:00:00"}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["end_time"] == "12:00:00"
    assert response.json()["start_time"] == "09:00:00"


async def test_update_foreign_schedule(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    created = await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )
    schedule_id = created.json()["id"]

    other_doctor_id, other_department_id, other_headers = await setup_doctor(
        client, db, "doctor2@ometus.test"
    )

    response = await client.put(
        f"{MY_SCHEDULE_URL}/{schedule_id}", json={"end_time": "12:00:00"}, headers=other_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SCHEDULE_NOT_FOUND"


async def test_delete_schedule(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    created = await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )

    response = await client.delete(
        f"{MY_SCHEDULE_URL}/{created.json()['id']}", headers=headers
    )

    assert response.status_code == 200

    listed = await client.get(MY_SCHEDULE_URL, headers=headers)
    assert listed.json() == []


async def test_available_slots(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )

    response = await client.get(
        f"{SCHEDULES_URL}/doctors/{doctor_id}/slots", params={"day": "2026-07-27"}
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert [slot["time"] for slot in body] == ["09:00:00", "09:20:00", "09:40:00"]
    assert body[0]["department_id"] == department_id


async def test_available_slots_on_day_off(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )

    response = await client.get(
        f"{SCHEDULES_URL}/doctors/{doctor_id}/slots", params={"day": "2026-07-28"}
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_available_slots_during_absence(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )
    await client.post(
        MY_ABSENCES_URL,
        json={"date_from": "2026-07-27", "date_to": "2026-07-31", "reason": "Отпуск"},
        headers=headers,
    )

    response = await client.get(
        f"{SCHEDULES_URL}/doctors/{doctor_id}/slots", params={"day": "2026-07-27"}
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_slots_for_unknown_doctor(client):
    response = await client.get(
        f"{SCHEDULES_URL}/doctors/999/slots", params={"day": "2026-07-27"}
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCTOR_NOT_FOUND"


async def test_create_absence_invalid_range(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)

    response = await client.post(
        MY_ABSENCES_URL,
        json={"date_from": "2026-07-31", "date_to": "2026-07-27"},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"


async def test_delete_absence(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    created = await client.post(
        MY_ABSENCES_URL,
        json={"date_from": "2026-07-27", "date_to": "2026-07-31"},
        headers=headers,
    )

    response = await client.delete(
        f"{MY_ABSENCES_URL}/{created.json()['id']}", headers=headers
    )

    assert response.status_code == 200

    listed = await client.get(MY_ABSENCES_URL, headers=headers)
    assert listed.json() == []


async def test_create_schedule_defaults_buffer_to_zero(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)

    response = await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )

    assert response.json()["buffer_duration"] == 0


async def test_buffer_widens_gap_between_slots(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    await client.post(
        MY_SCHEDULE_URL,
        json={**WORKDAY, "department_id": department_id, "buffer_duration": 20},
        headers=headers,
    )

    response = await client.get(
        f"{SCHEDULES_URL}/doctors/{doctor_id}/slots", params={"day": "2026-07-27"}
    )

    assert response.status_code == 200
    assert [slot["time"] for slot in response.json()] == ["09:00:00", "09:40:00"]


async def test_date_schedule_opens_a_day_off(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)

    response = await client.post(
        MY_DATES_URL,
        json={
            "department_id": department_id,
            "date": "2026-07-28",
            "start_time": "11:00:00",
            "end_time": "12:00:00",
            "slot_duration": 30,
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["date"] == "2026-07-28"

    slots = await client.get(
        f"{SCHEDULES_URL}/doctors/{doctor_id}/slots", params={"day": "2026-07-28"}
    )
    assert [slot["time"] for slot in slots.json()] == ["11:00:00", "11:30:00"]


async def test_date_schedule_overrides_weekday_grid(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )
    await client.post(
        MY_DATES_URL,
        json={
            "department_id": department_id,
            "date": "2026-07-27",
            "start_time": "14:00:00",
            "end_time": "15:00:00",
            "slot_duration": 30,
        },
        headers=headers,
    )

    slots = await client.get(
        f"{SCHEDULES_URL}/doctors/{doctor_id}/slots", params={"day": "2026-07-27"}
    )

    assert [slot["time"] for slot in slots.json()] == ["14:00:00", "14:30:00"]


async def test_date_schedule_yields_to_absence(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    await client.post(
        MY_DATES_URL,
        json={
            "department_id": department_id,
            "date": "2026-07-28",
            "start_time": "11:00:00",
            "end_time": "12:00:00",
        },
        headers=headers,
    )
    await client.post(
        MY_ABSENCES_URL,
        json={"date_from": "2026-07-28", "date_to": "2026-07-28"},
        headers=headers,
    )

    slots = await client.get(
        f"{SCHEDULES_URL}/doctors/{doctor_id}/slots", params={"day": "2026-07-28"}
    )

    assert slots.json() == []


async def test_date_schedule_duplicate(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    body = {
        "department_id": department_id,
        "date": "2026-07-28",
        "start_time": "11:00:00",
        "end_time": "12:00:00",
    }
    await client.post(MY_DATES_URL, json=body, headers=headers)

    response = await client.post(MY_DATES_URL, json=body, headers=headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DATE_SCHEDULE_ALREADY_EXISTS"


async def test_date_schedule_in_foreign_department(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db, assign=False)

    response = await client.post(
        MY_DATES_URL,
        json={
            "department_id": department_id,
            "date": "2026-07-28",
            "start_time": "11:00:00",
            "end_time": "12:00:00",
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DOCTOR_NOT_IN_DEPARTMENT"


async def test_delete_date_schedule(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    created = await client.post(
        MY_DATES_URL,
        json={
            "department_id": department_id,
            "date": "2026-07-28",
            "start_time": "11:00:00",
            "end_time": "12:00:00",
        },
        headers=headers,
    )

    response = await client.delete(
        f"{MY_DATES_URL}/{created.json()['id']}", headers=headers
    )

    assert response.status_code == 200
    listed = await client.get(MY_DATES_URL, headers=headers)
    assert listed.json() == []


async def test_delete_foreign_date_schedule(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    created = await client.post(
        MY_DATES_URL,
        json={
            "department_id": department_id,
            "date": "2026-07-28",
            "start_time": "11:00:00",
            "end_time": "12:00:00",
        },
        headers=headers,
    )
    _, _, other_headers = await setup_doctor(client, db, "doctor2@ometus.test")

    response = await client.delete(
        f"{MY_DATES_URL}/{created.json()['id']}", headers=other_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DATE_SCHEDULE_NOT_FOUND"


async def test_public_doctor_schedule(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )

    response = await client.get(f"{SCHEDULES_URL}/doctors/{doctor_id}")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["weekday"] == 0


async def add_second_department(client, db, doctor_id):
    admin = await auth_headers(client, "admin@ometus.test")
    filial = await client.get(ADMIN_FILIALS_URL.replace("/admin", ""))
    second = await client.post(
        ADMIN_DEPARTMENTS_URL,
        json={"filial_id": filial.json()[0]["id"], "name": "Неврология"},
        headers=admin,
    )
    second_id = second.json()["id"]
    await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor_id}/departments",
        json={"department_id": second_id},
        headers=admin,
    )
    return second_id


async def test_schedules_cannot_overlap_across_departments(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    second_id = await add_second_department(client, db, doctor_id)

    await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )
    clashing = await client.post(
        MY_SCHEDULE_URL,
        json={**WORKDAY, "department_id": second_id, "start_time": "09:30:00"},
        headers=headers,
    )

    assert clashing.status_code == 409
    assert clashing.json()["error"]["code"] == "SCHEDULE_OVERLAPS"


async def test_second_department_schedule_is_fine_when_time_does_not_clash(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    second_id = await add_second_department(client, db, doctor_id)

    await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )
    later = await client.post(
        MY_SCHEDULE_URL,
        json={
            **WORKDAY,
            "department_id": second_id,
            "start_time": "14:00:00",
            "end_time": "16:00:00",
        },
        headers=headers,
    )

    assert later.status_code == 200


async def test_slots_are_not_duplicated_by_time(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    second_id = await add_second_department(client, db, doctor_id)

    await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )
    # прямо в базу, минуя проверку пересечений: так выглядят данные,
    # заведённые до появления этой проверки
    from datetime import time

    from app.models.model_schedule import DoctorSchedule

    db.add(
        DoctorSchedule(
            doctor_id=doctor_id,
            department_id=second_id,
            weekday=WORKDAY["weekday"],
            start_time=time(9, 0),
            end_time=time(10, 0),
            slot_duration=WORKDAY["slot_duration"],
            buffer_duration=0,
        )
    )
    await db.commit()

    slots = await client.get(
        f"{SCHEDULES_URL}/doctors/{doctor_id}/slots", params={"day": "2026-07-27"}
    )
    times = [slot["time"] for slot in slots.json()]

    assert len(times) == len(set(times))


async def test_update_rejects_department_where_doctor_does_not_work(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    admin = await auth_headers(client, "admin@ometus.test")
    filial = await client.get(ADMIN_FILIALS_URL.replace("/admin", ""))
    foreign = await client.post(
        ADMIN_DEPARTMENTS_URL,
        json={"filial_id": filial.json()[0]["id"], "name": "Чужое отделение"},
        headers=admin,
    )
    created = await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )

    response = await client.put(
        f"{MY_SCHEDULE_URL}/{created.json()['id']}",
        json={"department_id": foreign.json()["id"]},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DOCTOR_NOT_IN_DEPARTMENT"


async def test_absences_cannot_overlap(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    await client.post(
        MY_ABSENCES_URL,
        json={"date_from": "2026-08-01", "date_to": "2026-08-10", "reason": "Отпуск"},
        headers=headers,
    )

    response = await client.post(
        MY_ABSENCES_URL,
        json={"date_from": "2026-08-05", "date_to": "2026-08-15", "reason": "Больничный"},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ABSENCE_OVERLAPS"


async def test_absence_cancels_appointments_on_those_days(client, db):
    from datetime import date, time

    from app.models.model_appointment import Appointment

    doctor_id, department_id, headers = await setup_doctor(client, db)
    await register(client, "booked.patient@ometus.test")
    patient = await client.get(
        "/api/users/me/patient",
        headers=await auth_headers(client, "booked.patient@ometus.test"),
    )

    appointment = Appointment(
        patient_id=patient.json()["id"],
        doctor_id=doctor_id,
        department_id=department_id,
        date=date(2026, 8, 3),
        time=time(9, 0),
        status="booked",
    )
    db.add(appointment)
    await db.commit()

    await client.post(
        MY_ABSENCES_URL,
        json={"date_from": "2026-08-01", "date_to": "2026-08-10", "reason": "Больничный"},
        headers=headers,
    )
    await db.refresh(appointment)

    assert appointment.status == "cancelled"
