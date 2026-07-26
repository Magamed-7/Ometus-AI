from datetime import date, time, timedelta

from tests.conftest import verify_email

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
APPOINTMENTS_URL = "/api/appointments"
DOCTOR_APPOINTMENTS_URL = "/api/appointments/doctor/me"
MY_SCHEDULE_URL = "/api/schedules/me"
SLOTS_URL = "/api/schedules/doctors"
PATIENT_URL = "/api/users/me/patient"
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
    from sqlalchemy import select

    from app.models.model_user import User

    await register(client, "admin@ometus.test")

    result = await db.execute(select(User).where(User.email == "admin@ometus.test"))
    user = result.scalar_one()
    user.role = "admin"
    await db.commit()

    return await auth_headers(client, "admin@ometus.test")


async def setup_doctor(client, db, email=DOCTOR_DATA["email"]):
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
    await client.post(
        MY_SCHEDULE_URL, json={**WORKDAY, "department_id": department_id}, headers=headers
    )

    return doctor_id, department_id, headers


async def setup_patient(client, email="patient@ometus.test", **extra):
    await register(client, email, **extra)
    headers = await auth_headers(client, email)
    profile = await client.get(PATIENT_URL, headers=headers)
    return profile.json()["id"], headers


async def book(client, headers, doctor_id, slot_time="09:00:00", day=None):
    return await client.post(
        APPOINTMENTS_URL,
        json={"doctor_id": doctor_id, "date": str(day or next_workday()), "time": slot_time},
        headers=headers,
    )


async def test_book_appointment(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await book(client, headers, doctor_id)

    assert response.status_code == 200
    body = response.json()
    assert body["patient_id"] == patient_id
    assert body["doctor_id"] == doctor_id
    assert body["department_id"] == department_id
    assert body["time"] == "09:00:00"
    assert body["status"] == "booked"


async def test_book_unknown_doctor(client, db):
    patient_id, headers = await setup_patient(client)

    response = await book(client, headers, 999)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCTOR_NOT_FOUND"


async def test_book_in_past(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await book(client, headers, doctor_id, day=date.today() - timedelta(days=7))

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "SLOT_IN_PAST"


async def test_book_time_outside_schedule(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await book(client, headers, doctor_id, "15:00:00")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SLOT_NOT_AVAILABLE"


async def test_book_slot_taken_by_another_patient(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    first_id, first_headers = await setup_patient(client)
    second_id, second_headers = await setup_patient(client, "patient2@ometus.test")

    await book(client, first_headers, doctor_id)
    response = await book(client, second_headers, doctor_id)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SLOT_NOT_AVAILABLE"


async def test_book_twice_to_same_doctor_in_one_day(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await book(client, headers, doctor_id)
    response = await book(client, headers, doctor_id, "09:20:00")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ALREADY_BOOKED"


async def test_book_forbidden_for_doctor(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)

    response = await book(client, doctor_headers, doctor_id)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_booked_slot_disappears_from_available(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    day = next_workday()

    await book(client, headers, doctor_id)
    response = await client.get(f"{SLOTS_URL}/{doctor_id}/slots", params={"day": str(day)})

    assert [slot["time"] for slot in response.json()] == ["09:20:00", "09:40:00"]


async def test_cancelled_slot_becomes_available_again(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    day = next_workday()

    created = await book(client, headers, doctor_id)
    await client.delete(f"{APPOINTMENTS_URL}/{created.json()['id']}", headers=headers)

    response = await client.get(f"{SLOTS_URL}/{doctor_id}/slots", params={"day": str(day)})

    assert [slot["time"] for slot in response.json()] == ["09:00:00", "09:20:00", "09:40:00"]


async def test_cancelled_slot_can_be_booked_by_another_patient(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    first_id, first_headers = await setup_patient(client)
    second_id, second_headers = await setup_patient(client, "patient2@ometus.test")

    created = await book(client, first_headers, doctor_id)
    await client.delete(f"{APPOINTMENTS_URL}/{created.json()['id']}", headers=first_headers)

    response = await book(client, second_headers, doctor_id)

    assert response.status_code == 200
    assert response.json()["patient_id"] == second_id


async def test_my_appointments(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    await book(client, headers, doctor_id)

    response = await client.get(f"{APPOINTMENTS_URL}/me", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["doctor_id"] == doctor_id


async def test_patient_does_not_see_foreign_appointment(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    first_id, first_headers = await setup_patient(client)
    second_id, second_headers = await setup_patient(client, "patient2@ometus.test")
    created = await book(client, first_headers, doctor_id)

    response = await client.get(
        f"{APPOINTMENTS_URL}/{created.json()['id']}", headers=second_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "APPOINTMENT_NOT_FOUND"


async def test_cancel_appointment(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    created = await book(client, headers, doctor_id)

    response = await client.delete(
        f"{APPOINTMENTS_URL}/{created.json()['id']}", headers=headers
    )

    assert response.status_code == 200

    listed = await client.get(f"{APPOINTMENTS_URL}/me", params={"status": "cancelled"}, headers=headers)
    assert len(listed.json()) == 1


async def test_cancel_appointment_twice(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    created = await book(client, headers, doctor_id)
    await client.delete(f"{APPOINTMENTS_URL}/{created.json()['id']}", headers=headers)

    response = await client.delete(
        f"{APPOINTMENTS_URL}/{created.json()['id']}", headers=headers
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "APPOINTMENT_NOT_ACTIVE"


async def test_cancel_foreign_appointment(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    first_id, first_headers = await setup_patient(client)
    second_id, second_headers = await setup_patient(client, "patient2@ometus.test")
    created = await book(client, first_headers, doctor_id)

    response = await client.delete(
        f"{APPOINTMENTS_URL}/{created.json()['id']}", headers=second_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "APPOINTMENT_NOT_FOUND"


async def test_reschedule_appointment(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    created = await book(client, headers, doctor_id)

    response = await client.put(
        f"{APPOINTMENTS_URL}/{created.json()['id']}/reschedule",
        json={"date": str(next_workday()), "time": "09:40:00"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["time"] == "09:40:00"


async def test_reschedule_to_taken_slot(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    first_id, first_headers = await setup_patient(client)
    second_id, second_headers = await setup_patient(client, "patient2@ometus.test")
    created = await book(client, first_headers, doctor_id)
    await book(client, second_headers, doctor_id, "09:20:00")

    response = await client.put(
        f"{APPOINTMENTS_URL}/{created.json()['id']}/reschedule",
        json={"date": str(next_workday()), "time": "09:20:00"},
        headers=first_headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SLOT_NOT_AVAILABLE"


async def test_reschedule_to_past(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    created = await book(client, headers, doctor_id)

    response = await client.put(
        f"{APPOINTMENTS_URL}/{created.json()['id']}/reschedule",
        json={"date": str(date.today() - timedelta(days=7)), "time": "09:00:00"},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "SLOT_IN_PAST"


async def test_doctor_sees_appointments_with_patient_contacts(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(
        client, first_name="Aziz", last_name="Negmatov", phone="+992900000000"
    )
    await book(client, headers, doctor_id)

    response = await client.get(
        DOCTOR_APPOINTMENTS_URL, params={"day": str(next_workday())}, headers=doctor_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["patient_name"] == "Aziz Negmatov"
    assert body[0]["patient_phone"] == "+992900000000"


async def test_doctor_appointments_forbidden_for_patient(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await client.get(DOCTOR_APPOINTMENTS_URL, headers=headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_doctor_today_list(client, db):
    from app.models.model_appointment import Appointment

    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    await book(client, headers, doctor_id)

    db.add(
        Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            department_id=department_id,
            date=date.today(),
            time=time(11, 0),
            status="booked",
        )
    )
    await db.commit()

    response = await client.get(f"{DOCTOR_APPOINTMENTS_URL}/today", headers=doctor_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["time"] == "11:00:00"


async def test_complete_appointment(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    created = await book(client, headers, doctor_id)

    response = await client.put(
        f"{DOCTOR_APPOINTMENTS_URL}/{created.json()['id']}/complete", headers=doctor_headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


async def test_complete_appointment_twice(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    created = await book(client, headers, doctor_id)
    await client.put(
        f"{DOCTOR_APPOINTMENTS_URL}/{created.json()['id']}/complete", headers=doctor_headers
    )

    response = await client.put(
        f"{DOCTOR_APPOINTMENTS_URL}/{created.json()['id']}/complete", headers=doctor_headers
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "APPOINTMENT_NOT_ACTIVE"


async def test_complete_foreign_appointment(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    other_id, other_department_id, other_headers = await setup_doctor(
        client, db, "doctor2@ometus.test"
    )
    patient_id, headers = await setup_patient(client)
    created = await book(client, headers, doctor_id)

    response = await client.put(
        f"{DOCTOR_APPOINTMENTS_URL}/{created.json()['id']}/complete", headers=other_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "APPOINTMENT_NOT_FOUND"


async def test_mark_appointment_no_show(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    created = await book(client, headers, doctor_id)

    response = await client.put(
        f"{DOCTOR_APPOINTMENTS_URL}/{created.json()['id']}/no-show", headers=doctor_headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "no_show"


async def test_completed_slot_stays_taken(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    first_id, first_headers = await setup_patient(client)
    second_id, second_headers = await setup_patient(client, "patient2@ometus.test")
    created = await book(client, first_headers, doctor_id)
    await client.put(
        f"{DOCTOR_APPOINTMENTS_URL}/{created.json()['id']}/complete", headers=doctor_headers
    )

    response = await book(client, second_headers, doctor_id)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SLOT_NOT_AVAILABLE"


EMERGENCY_URL = "/api/appointments/emergency"


async def registrar_headers(client, db):
    from sqlalchemy import select

    from app.models.model_user import User

    await register(client, "registrar@ometus.test")

    result = await db.execute(select(User).where(User.email == "registrar@ometus.test"))
    user = result.scalar_one()
    user.role = "registrar"
    await db.commit()

    return await auth_headers(client, "registrar@ometus.test")


async def book_emergency(
    client, headers, patient_id, doctor_id, department_id, slot_time="08:00:00", day=None
):
    return await client.post(
        EMERGENCY_URL,
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": department_id,
            "date": str(day or next_workday()),
            "time": slot_time,
        },
        headers=headers,
    )


async def test_registrar_books_emergency_off_grid(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, _ = await setup_patient(client)
    headers = await registrar_headers(client, db)

    response = await book_emergency(client, headers, patient_id, doctor_id, department_id)

    assert response.status_code == 200
    body = response.json()
    assert body["is_emergency"] is True
    assert body["patient_id"] == patient_id
    assert body["time"] == "08:00:00"


async def test_admin_books_emergency(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, _ = await setup_patient(client)
    headers = await admin_headers(client, db)

    response = await book_emergency(client, headers, patient_id, doctor_id, department_id)

    assert response.status_code == 200
    assert response.json()["is_emergency"] is True


async def test_patient_cannot_book_emergency(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    response = await book_emergency(client, headers, patient_id, doctor_id, department_id)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_emergency_doctor_not_in_department(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, _ = await setup_patient(client)
    headers = await registrar_headers(client, db)

    response = await book_emergency(client, headers, patient_id, doctor_id, 999)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DOCTOR_NOT_IN_DEPARTMENT"


async def test_double_emergency_same_time_conflicts(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, _ = await setup_patient(client)
    headers = await registrar_headers(client, db)

    await book_emergency(client, headers, patient_id, doctor_id, department_id)
    response = await book_emergency(client, headers, patient_id, doctor_id, department_id)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SLOT_TAKEN"


DEPENDENTS_URL = "/api/users/me/dependents"


async def test_book_for_own_dependent(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    dependent = await client.post(
        DEPENDENTS_URL, json={"full_name": "Малыш"}, headers=headers
    )
    dependent_id = dependent.json()["id"]

    response = await client.post(
        APPOINTMENTS_URL,
        json={
            "doctor_id": doctor_id,
            "date": str(next_workday()),
            "time": "09:00:00",
            "patient_id": dependent_id,
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["patient_id"] == dependent_id


async def test_cannot_book_for_others_dependent(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    owner_id, owner_headers = await setup_patient(client)
    dependent = await client.post(
        DEPENDENTS_URL, json={"full_name": "Малыш"}, headers=owner_headers
    )
    dependent_id = dependent.json()["id"]
    stranger_id, stranger_headers = await setup_patient(client, "stranger@ometus.test")

    response = await client.post(
        APPOINTMENTS_URL,
        json={
            "doctor_id": doctor_id,
            "date": str(next_workday()),
            "time": "09:00:00",
            "patient_id": dependent_id,
        },
        headers=stranger_headers,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
