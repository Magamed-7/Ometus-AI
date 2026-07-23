REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
SCHEDULES_URL = "/api/schedules"
MY_SCHEDULE_URL = "/api/schedules/me"
MY_ABSENCES_URL = "/api/schedules/me/absences"
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
    return await client.post(REGISTER_URL, json={"email": email, "password": password})


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


async def test_public_doctor_schedule(client, db):
    doctor_id, department_id, headers = await setup_doctor(client, db)
    await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )

    response = await client.get(f"{SCHEDULES_URL}/doctors/{doctor_id}")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["weekday"] == 0
