from datetime import date, time

from app.models.model_appointment import Appointment

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
PATIENT_URL = "/api/users/me/patient"
ADMIN_FILIALS_URL = "/api/admin/filials"
ADMIN_DEPARTMENTS_URL = "/api/admin/departments"
ADMIN_DOCTORS_URL = "/api/admin/doctors"
WORKLOAD_URL = "/api/admin/reports/workload"
SUMMARY_URL = "/api/admin/reports/summary"
APPOINTMENTS_URL = "/api/admin/appointments"
USERS_URL = "/api/admin/users"

FILIAL_DATA = {"name": "Ometus Центр", "city": "Душанбе", "address": "ул. Рудаки 100"}

PERIOD = {"date_from": "2026-03-01", "date_to": "2026-03-31"}


async def register(client, email, password="secret1234", **extra):
    return await client.post(
        REGISTER_URL, json={"email": email, "password": password, **extra}
    )


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


async def create_doctor(client, admin, email, full_name, department_id):
    doctor = await client.post(
        ADMIN_DOCTORS_URL,
        json={
            "email": email,
            "password": "secret1234",
            "full_name": full_name,
            "specialization": "Кардиолог",
        },
        headers=admin,
    )
    doctor_id = doctor.json()["id"]

    await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor_id}/departments",
        json={"department_id": department_id},
        headers=admin,
    )

    return doctor_id


async def setup_clinic(client, db):
    admin = await admin_headers(client, db)

    filial = await client.post(ADMIN_FILIALS_URL, json=FILIAL_DATA, headers=admin)
    filial_id = filial.json()["id"]

    cardiology = await client.post(
        ADMIN_DEPARTMENTS_URL, json={"filial_id": filial_id, "name": "Кардиология"}, headers=admin
    )
    neurology = await client.post(
        ADMIN_DEPARTMENTS_URL, json={"filial_id": filial_id, "name": "Неврология"}, headers=admin
    )
    cardiology_id = cardiology.json()["id"]
    neurology_id = neurology.json()["id"]

    first_doctor = await create_doctor(
        client, admin, "doctor@ometus.test", "Иванова Мария", cardiology_id
    )
    second_doctor = await create_doctor(
        client, admin, "doctor2@ometus.test", "Каримов Ахмад", neurology_id
    )

    await register(client, "patient@ometus.test")
    patient_headers = await auth_headers(client, "patient@ometus.test")
    profile = await client.get(PATIENT_URL, headers=patient_headers)

    return {
        "admin": admin,
        "cardiology_id": cardiology_id,
        "neurology_id": neurology_id,
        "first_doctor": first_doctor,
        "second_doctor": second_doctor,
        "patient_id": profile.json()["id"],
        "patient_headers": patient_headers,
    }


async def add_appointment(db, clinic, day, slot_time, status, doctor_id=None):
    db.add(
        Appointment(
            patient_id=clinic["patient_id"],
            doctor_id=doctor_id or clinic["first_doctor"],
            department_id=clinic["cardiology_id"],
            date=day,
            time=slot_time,
            status=status,
        )
    )
    await db.commit()


async def fill_appointments(db, clinic):
    await add_appointment(db, clinic, date(2026, 3, 5), time(9, 0), "booked")
    await add_appointment(db, clinic, date(2026, 3, 6), time(9, 0), "completed")
    await add_appointment(db, clinic, date(2026, 3, 7), time(9, 0), "cancelled")
    await add_appointment(db, clinic, date(2026, 3, 8), time(9, 0), "no_show")
    await add_appointment(db, clinic, date(2026, 4, 10), time(9, 0), "booked")


async def test_workload_report_counts_by_status(client, db):
    clinic = await setup_clinic(client, db)
    await fill_appointments(db, clinic)

    response = await client.get(WORKLOAD_URL, params=PERIOD, headers=clinic["admin"])

    assert response.status_code == 200
    report = {row["doctor_id"]: row for row in response.json()}
    first = report[clinic["first_doctor"]]
    assert first["full_name"] == "Иванова Мария"
    assert first["total"] == 4
    assert first["booked"] == 1
    assert first["completed"] == 1
    assert first["cancelled"] == 1
    assert first["no_show"] == 1


async def test_workload_report_includes_doctors_without_appointments(client, db):
    clinic = await setup_clinic(client, db)
    await fill_appointments(db, clinic)

    response = await client.get(WORKLOAD_URL, params=PERIOD, headers=clinic["admin"])

    report = {row["doctor_id"]: row for row in response.json()}
    assert len(report) == 2
    assert report[clinic["second_doctor"]]["total"] == 0
    assert report[clinic["second_doctor"]]["booked"] == 0


async def test_workload_report_ignores_appointments_outside_period(client, db):
    clinic = await setup_clinic(client, db)
    await fill_appointments(db, clinic)

    response = await client.get(
        WORKLOAD_URL,
        params={"date_from": "2026-04-01", "date_to": "2026-04-30"},
        headers=clinic["admin"],
    )

    report = {row["doctor_id"]: row for row in response.json()}
    assert report[clinic["first_doctor"]]["total"] == 1
    assert report[clinic["first_doctor"]]["booked"] == 1


async def test_workload_report_filtered_by_department(client, db):
    clinic = await setup_clinic(client, db)
    await fill_appointments(db, clinic)

    response = await client.get(
        WORKLOAD_URL,
        params={**PERIOD, "department_id": clinic["neurology_id"]},
        headers=clinic["admin"],
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["doctor_id"] == clinic["second_doctor"]


async def test_workload_report_with_unknown_department(client, db):
    clinic = await setup_clinic(client, db)

    response = await client.get(
        WORKLOAD_URL, params={**PERIOD, "department_id": 999}, headers=clinic["admin"]
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DEPARTMENT_NOT_FOUND"


async def test_workload_report_with_invalid_period(client, db):
    clinic = await setup_clinic(client, db)

    response = await client.get(
        WORKLOAD_URL,
        params={"date_from": "2026-03-31", "date_to": "2026-03-01"},
        headers=clinic["admin"],
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"


async def test_workload_report_forbidden_for_patient(client, db):
    clinic = await setup_clinic(client, db)

    response = await client.get(WORKLOAD_URL, params=PERIOD, headers=clinic["patient_headers"])

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_workload_report_requires_auth(client, db):
    await setup_clinic(client, db)

    response = await client.get(WORKLOAD_URL, params=PERIOD)

    assert response.status_code == 401


async def test_summary_report(client, db):
    clinic = await setup_clinic(client, db)
    await fill_appointments(db, clinic)

    response = await client.get(SUMMARY_URL, params=PERIOD, headers=clinic["admin"])

    assert response.status_code == 200
    body = response.json()
    assert body["date_from"] == PERIOD["date_from"]
    assert body["total"] == 4
    assert body["booked"] == 1
    assert body["completed"] == 1
    assert body["cancelled"] == 1
    assert body["no_show"] == 1
    assert body["doctors"] == 1
    assert body["patients"] == 1


async def test_summary_report_counts_doctors_separately(client, db):
    clinic = await setup_clinic(client, db)
    await add_appointment(db, clinic, date(2026, 3, 5), time(9, 0), "booked")
    await add_appointment(
        db, clinic, date(2026, 3, 5), time(9, 0), "booked", clinic["second_doctor"]
    )

    response = await client.get(SUMMARY_URL, params=PERIOD, headers=clinic["admin"])

    body = response.json()
    assert body["total"] == 2
    assert body["doctors"] == 2
    assert body["patients"] == 1


async def test_summary_report_on_empty_period(client, db):
    clinic = await setup_clinic(client, db)
    await fill_appointments(db, clinic)

    response = await client.get(
        SUMMARY_URL,
        params={"date_from": "2026-01-01", "date_to": "2026-01-31"},
        headers=clinic["admin"],
    )

    body = response.json()
    assert body["total"] == 0
    assert body["doctors"] == 0
    assert body["patients"] == 0


async def test_summary_report_forbidden_for_doctor(client, db):
    clinic = await setup_clinic(client, db)
    doctor_headers = await auth_headers(client, "doctor@ometus.test")

    response = await client.get(SUMMARY_URL, params=PERIOD, headers=doctor_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_list_all_appointments_returns_every_record(client, db):
    clinic = await setup_clinic(client, db)
    await fill_appointments(db, clinic)

    response = await client.get(APPOINTMENTS_URL, headers=clinic["admin"])

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 5
    assert body[0]["doctor_name"] == "Иванова Мария"
    assert body[0]["patient_id"] == clinic["patient_id"]
    assert body[0]["specialization"] == "Кардиолог"


async def test_list_appointments_filtered_by_doctor(client, db):
    clinic = await setup_clinic(client, db)
    await fill_appointments(db, clinic)
    await add_appointment(
        db, clinic, date(2026, 3, 9), time(9, 0), "booked", clinic["second_doctor"]
    )

    response = await client.get(
        APPOINTMENTS_URL, params={"doctor_id": clinic["second_doctor"]}, headers=clinic["admin"]
    )

    body = response.json()
    assert len(body) == 1
    assert body[0]["doctor_id"] == clinic["second_doctor"]


async def test_list_appointments_filtered_by_status(client, db):
    clinic = await setup_clinic(client, db)
    await fill_appointments(db, clinic)

    response = await client.get(
        APPOINTMENTS_URL, params={"status": "cancelled"}, headers=clinic["admin"]
    )

    body = response.json()
    assert len(body) == 1
    assert body[0]["status"] == "cancelled"


async def test_list_appointments_filtered_by_period(client, db):
    clinic = await setup_clinic(client, db)
    await fill_appointments(db, clinic)

    response = await client.get(APPOINTMENTS_URL, params=PERIOD, headers=clinic["admin"])

    body = response.json()
    assert len(body) == 4


async def test_list_appointments_invalid_period(client, db):
    clinic = await setup_clinic(client, db)

    response = await client.get(
        APPOINTMENTS_URL,
        params={"date_from": "2026-03-31", "date_to": "2026-03-01"},
        headers=clinic["admin"],
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"


async def test_list_appointments_forbidden_for_patient(client, db):
    clinic = await setup_clinic(client, db)

    response = await client.get(APPOINTMENTS_URL, headers=clinic["patient_headers"])

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def schedules_url(doctor_id):
    return f"/api/admin/doctors/{doctor_id}/schedules"


async def create_schedule(client, clinic, department_id=None, weekday=0, start="09:00", end="13:00"):
    return await client.post(
        schedules_url(clinic["first_doctor"]),
        json={
            "department_id": department_id or clinic["cardiology_id"],
            "weekday": weekday,
            "start_time": start,
            "end_time": end,
        },
        headers=clinic["admin"],
    )


async def test_admin_creates_doctor_schedule(client, db):
    clinic = await setup_clinic(client, db)

    response = await create_schedule(client, clinic)

    assert response.status_code == 200
    body = response.json()
    assert body["doctor_id"] == clinic["first_doctor"]
    assert body["weekday"] == 0
    assert body["slot_duration"] == 20

    listing = await client.get(schedules_url(clinic["first_doctor"]), headers=clinic["admin"])
    assert len(listing.json()) == 1


async def test_admin_schedule_rejects_department_doctor_not_in(client, db):
    clinic = await setup_clinic(client, db)

    response = await create_schedule(client, clinic, department_id=clinic["neurology_id"])

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DOCTOR_NOT_IN_DEPARTMENT"


async def test_admin_schedule_rejects_duplicate_weekday(client, db):
    clinic = await setup_clinic(client, db)
    await create_schedule(client, clinic)

    response = await create_schedule(client, clinic)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SCHEDULE_ALREADY_EXISTS"


async def test_admin_schedule_rejects_invalid_time_range(client, db):
    clinic = await setup_clinic(client, db)

    response = await create_schedule(client, clinic, start="13:00", end="09:00")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_TIME_RANGE"


async def test_admin_schedule_unknown_doctor(client, db):
    clinic = await setup_clinic(client, db)

    response = await client.post(
        schedules_url(999),
        json={"department_id": clinic["cardiology_id"], "weekday": 0,
              "start_time": "09:00", "end_time": "13:00"},
        headers=clinic["admin"],
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCTOR_NOT_FOUND"


async def test_admin_updates_doctor_schedule(client, db):
    clinic = await setup_clinic(client, db)
    schedule_id = (await create_schedule(client, clinic)).json()["id"]

    response = await client.put(
        f"{schedules_url(clinic['first_doctor'])}/{schedule_id}",
        json={"end_time": "15:00"},
        headers=clinic["admin"],
    )

    assert response.status_code == 200
    assert response.json()["end_time"] == "15:00:00"


async def test_admin_deletes_doctor_schedule(client, db):
    clinic = await setup_clinic(client, db)
    schedule_id = (await create_schedule(client, clinic)).json()["id"]

    response = await client.delete(
        f"{schedules_url(clinic['first_doctor'])}/{schedule_id}", headers=clinic["admin"]
    )

    assert response.status_code == 200
    listing = await client.get(schedules_url(clinic["first_doctor"]), headers=clinic["admin"])
    assert listing.json() == []


async def test_admin_update_schedule_wrong_doctor(client, db):
    clinic = await setup_clinic(client, db)
    schedule_id = (await create_schedule(client, clinic)).json()["id"]

    response = await client.put(
        f"{schedules_url(clinic['second_doctor'])}/{schedule_id}",
        json={"end_time": "15:00"},
        headers=clinic["admin"],
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SCHEDULE_NOT_FOUND"


async def test_admin_schedule_forbidden_for_patient(client, db):
    clinic = await setup_clinic(client, db)

    response = await client.get(
        schedules_url(clinic["first_doctor"]), headers=clinic["patient_headers"]
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def user_id_by_email(client, admin, email):
    users = await client.get(USERS_URL, headers=admin)
    return next(user["id"] for user in users.json() if user["email"] == email)


async def test_admin_lists_all_users(client, db):
    clinic = await setup_clinic(client, db)

    response = await client.get(USERS_URL, headers=clinic["admin"])

    assert response.status_code == 200
    emails = {user["email"] for user in response.json()}
    assert emails == {
        "admin@ometus.test",
        "doctor@ometus.test",
        "doctor2@ometus.test",
        "patient@ometus.test",
    }


async def test_admin_lists_users_filtered_by_role(client, db):
    clinic = await setup_clinic(client, db)

    response = await client.get(USERS_URL, params={"role": "doctor"}, headers=clinic["admin"])

    body = response.json()
    assert len(body) == 2
    assert all(user["role"] == "doctor" for user in body)


async def test_admin_grants_admin_role(client, db):
    clinic = await setup_clinic(client, db)
    patient_user = await user_id_by_email(client, clinic["admin"], "patient@ometus.test")

    response = await client.put(
        f"{USERS_URL}/{patient_user}/role", json={"role": "admin"}, headers=clinic["admin"]
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


async def test_admin_change_role_to_doctor_requires_card(client, db):
    clinic = await setup_clinic(client, db)
    patient_user = await user_id_by_email(client, clinic["admin"], "patient@ometus.test")

    response = await client.put(
        f"{USERS_URL}/{patient_user}/role", json={"role": "doctor"}, headers=clinic["admin"]
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DOCTOR_CARD_REQUIRED"


async def test_admin_cannot_change_own_role(client, db):
    clinic = await setup_clinic(client, db)
    admin_user = await user_id_by_email(client, clinic["admin"], "admin@ometus.test")

    response = await client.put(
        f"{USERS_URL}/{admin_user}/role", json={"role": "patient"}, headers=clinic["admin"]
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "SELF_ROLE_CHANGE"


async def test_admin_change_role_unknown_user(client, db):
    clinic = await setup_clinic(client, db)

    response = await client.put(
        f"{USERS_URL}/999/role", json={"role": "admin"}, headers=clinic["admin"]
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "USER_NOT_FOUND"


async def test_admin_users_forbidden_for_patient(client, db):
    clinic = await setup_clinic(client, db)

    response = await client.get(USERS_URL, headers=clinic["patient_headers"])

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
