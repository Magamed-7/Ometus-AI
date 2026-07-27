from app.ai.specialization_map import SPECIALIZATION_KEYWORDS

from tests.conftest import verify_email

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
DOCTORS_URL = "/api/doctors"
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


async def register(client, email, password="secret1234", role="patient"):
    response = await client.post(
        REGISTER_URL,
        json={"email": email, "password": password, "role": role},
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


async def create_filial(client, headers):
    response = await client.post(ADMIN_FILIALS_URL, json=FILIAL_DATA, headers=headers)
    return response.json()["id"]


async def create_department(client, headers, filial_id, name="Кардиология"):
    response = await client.post(
        ADMIN_DEPARTMENTS_URL, json={"filial_id": filial_id, "name": name}, headers=headers
    )
    return response.json()["id"]


async def create_doctor(client, headers, data=None):
    response = await client.post(ADMIN_DOCTORS_URL, json=data or DOCTOR_DATA, headers=headers)
    return response.json()


async def test_create_doctor(client, db):
    headers = await admin_headers(client, db)

    response = await client.post(ADMIN_DOCTORS_URL, json=DOCTOR_DATA, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Иванова Мария"
    assert body["specialization"] == "Кардиолог"


async def test_create_doctor_duplicate_email(client, db):
    headers = await admin_headers(client, db)
    await client.post(ADMIN_DOCTORS_URL, json=DOCTOR_DATA, headers=headers)

    response = await client.post(ADMIN_DOCTORS_URL, json=DOCTOR_DATA, headers=headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


async def test_create_doctor_forbidden_for_patient(client):
    await register(client, "patient@ometus.test")
    headers = await auth_headers(client, "patient@ometus.test")

    response = await client.post(ADMIN_DOCTORS_URL, json=DOCTOR_DATA, headers=headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_doctor_can_login(client, db):
    headers = await admin_headers(client, db)
    await create_doctor(client, headers)

    response = await client.post(
        LOGIN_URL, json={"email": DOCTOR_DATA["email"], "password": DOCTOR_DATA["password"]}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_update_doctor(client, db):
    headers = await admin_headers(client, db)
    doctor = await create_doctor(client, headers)

    response = await client.put(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}",
        json={"specialization": "Терапевт"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["specialization"] == "Терапевт"
    assert body["full_name"] == "Иванова Мария"


async def test_update_doctor_not_found(client, db):
    headers = await admin_headers(client, db)

    response = await client.put(
        f"{ADMIN_DOCTORS_URL}/999", json={"specialization": "Терапевт"}, headers=headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCTOR_NOT_FOUND"


async def test_assign_doctor_department(client, db):
    headers = await admin_headers(client, db)
    filial_id = await create_filial(client, headers)
    department_id = await create_department(client, headers, filial_id)
    doctor = await create_doctor(client, headers)

    response = await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}/departments",
        json={"department_id": department_id},
        headers=headers,
    )

    assert response.status_code == 200

    departments = await client.get(f"{DOCTORS_URL}/{doctor['id']}/departments")
    assert len(departments.json()) == 1
    assert departments.json()[0]["id"] == department_id


async def test_assign_doctor_department_twice(client, db):
    headers = await admin_headers(client, db)
    filial_id = await create_filial(client, headers)
    department_id = await create_department(client, headers, filial_id)
    doctor = await create_doctor(client, headers)

    await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}/departments",
        json={"department_id": department_id},
        headers=headers,
    )
    response = await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}/departments",
        json={"department_id": department_id},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DOCTOR_ALREADY_IN_DEPARTMENT"


async def test_remove_doctor_department(client, db):
    headers = await admin_headers(client, db)
    filial_id = await create_filial(client, headers)
    department_id = await create_department(client, headers, filial_id)
    doctor = await create_doctor(client, headers)

    await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}/departments",
        json={"department_id": department_id},
        headers=headers,
    )
    response = await client.delete(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}/departments/{department_id}", headers=headers
    )

    assert response.status_code == 200

    departments = await client.get(f"{DOCTORS_URL}/{doctor['id']}/departments")
    assert departments.json() == []


async def test_remove_doctor_department_not_assigned(client, db):
    headers = await admin_headers(client, db)
    filial_id = await create_filial(client, headers)
    department_id = await create_department(client, headers, filial_id)
    doctor = await create_doctor(client, headers)

    response = await client.delete(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}/departments/{department_id}", headers=headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCTOR_NOT_IN_DEPARTMENT"


async def test_search_doctors_by_specialization(client, db):
    headers = await admin_headers(client, db)
    await create_doctor(client, headers)
    await create_doctor(
        client,
        headers,
        {**DOCTOR_DATA, "email": "doctor2@ometus.test", "specialization": "Невролог"},
    )

    response = await client.get(DOCTORS_URL, params={"specialization": "Кардио"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["specialization"] == "Кардиолог"


async def test_search_doctors_by_filial(client, db):
    headers = await admin_headers(client, db)
    filial_id = await create_filial(client, headers)
    department_id = await create_department(client, headers, filial_id)
    doctor = await create_doctor(client, headers)
    await create_doctor(
        client, headers, {**DOCTOR_DATA, "email": "doctor2@ometus.test"}
    )

    await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}/departments",
        json={"department_id": department_id},
        headers=headers,
    )

    response = await client.get(DOCTORS_URL, params={"filial_id": filial_id})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == doctor["id"]


async def test_get_doctor_not_found(client):
    response = await client.get(f"{DOCTORS_URL}/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCTOR_NOT_FOUND"


async def test_add_specialization(client, db):
    headers = await admin_headers(client, db)
    doctor = await create_doctor(client, headers)

    response = await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}/specializations",
        json={"name": "Терапевт"},
        headers=headers,
    )

    assert response.status_code == 200

    specializations = await client.get(f"{DOCTORS_URL}/{doctor['id']}/specializations")
    assert len(specializations.json()) == 1
    assert specializations.json()[0]["name"] == "Терапевт"


async def test_add_specialization_duplicate(client, db):
    headers = await admin_headers(client, db)
    doctor = await create_doctor(client, headers)

    await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}/specializations",
        json={"name": "Терапевт"},
        headers=headers,
    )
    response = await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}/specializations",
        json={"name": "Терапевт"},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SPECIALIZATION_ALREADY_EXISTS"


async def test_add_specialization_forbidden_for_patient(client, db):
    headers = await admin_headers(client, db)
    doctor = await create_doctor(client, headers)
    await register(client, "patient@ometus.test")
    patient_headers = await auth_headers(client, "patient@ometus.test")

    response = await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}/specializations",
        json={"name": "Терапевт"},
        headers=patient_headers,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_remove_specialization(client, db):
    headers = await admin_headers(client, db)
    doctor = await create_doctor(client, headers)

    await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}/specializations",
        json={"name": "Терапевт"},
        headers=headers,
    )
    response = await client.delete(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}/specializations/Терапевт", headers=headers
    )

    assert response.status_code == 200

    specializations = await client.get(f"{DOCTORS_URL}/{doctor['id']}/specializations")
    assert specializations.json() == []


async def test_remove_specialization_not_found(client, db):
    headers = await admin_headers(client, db)
    doctor = await create_doctor(client, headers)

    response = await client.delete(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}/specializations/Терапевт", headers=headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SPECIALIZATION_NOT_FOUND"


async def test_search_doctors_by_additional_specialization(client, db):
    headers = await admin_headers(client, db)
    doctor = await create_doctor(client, headers)

    await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor['id']}/specializations",
        json={"name": "Терапевт"},
        headers=headers,
    )

    response = await client.get(DOCTORS_URL, params={"specialization": "Терапевт"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == doctor["id"]


async def test_doctor_name_is_split_between_first_and_last(client, db):
    from sqlalchemy import select

    from app.models.model_user import User

    headers = await admin_headers(client, db)
    await client.post(
        ADMIN_DOCTORS_URL,
        json={
            "email": "surgeon@ometus.test",
            "full_name": "Иванова Мария Петровна",
            "specialization": "Хирург",
        },
        headers=headers,
    )

    user = (
        await db.execute(select(User).where(User.email == "surgeon@ometus.test"))
    ).scalar_one()

    assert user.last_name == "Иванова"
    assert user.first_name == "Мария Петровна"


async def test_specialization_removal_ignores_case(client, db):
    headers = await admin_headers(client, db)
    created = await client.post(
        ADMIN_DOCTORS_URL,
        json={
            "email": "multi@ometus.test",
            "full_name": "Саидов Фарход",
            "specialization": "Терапевт",
        },
        headers=headers,
    )
    doctor_id = created.json()["id"]
    await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor_id}/specializations",
        json={"name": "Кардиолог"},
        headers=headers,
    )

    response = await client.delete(
        f"{ADMIN_DOCTORS_URL}/{doctor_id}/specializations/кардиолог", headers=headers
    )
    left = await client.get(f"/api/doctors/{doctor_id}/specializations")

    assert response.status_code == 200
    assert left.json() == []


async def test_empty_specialization_returns_every_doctor(client, db):
    headers = await admin_headers(client, db)

    for number in range(2):
        await client.post(
            ADMIN_DOCTORS_URL,
            json={
                "email": f"doc{number}@ometus.test",
                "full_name": f"Врач Номер{number}",
                "specialization": "Терапевт",
            },
            headers=headers,
        )

    everyone = await client.get(DOCTORS_URL)
    with_empty_filter = await client.get(f"{DOCTORS_URL}?specialization=")

    assert with_empty_filter.status_code == 200
    assert len(with_empty_filter.json()) == len(everyone.json()) == 2


async def test_dismissed_doctor_disappears_from_search(client, db):
    from datetime import date

    headers = await admin_headers(client, db)
    created = await client.post(
        ADMIN_DOCTORS_URL,
        json={
            "email": "leaving@ometus.test",
            "full_name": "Уходящий Врач",
            "specialization": "Терапевт",
        },
        headers=headers,
    )
    doctor_id = created.json()["id"]

    dismissed = await client.put(
        f"{ADMIN_DOCTORS_URL}/{doctor_id}/dismiss",
        json={"dismissed_at": date.today().isoformat()},
        headers=headers,
    )
    listing = await client.get(DOCTORS_URL)

    assert dismissed.status_code == 200
    assert dismissed.json()["dismissed_at"] == date.today().isoformat()
    assert all(doctor["id"] != doctor_id for doctor in listing.json())

    card = await client.get(f"{DOCTORS_URL}/{doctor_id}")
    assert card.status_code == 200


async def test_dismissal_warns_about_upcoming_appointments(client, db):
    from datetime import date, time, timedelta

    from app.models.model_appointment import Appointment

    headers = await admin_headers(client, db)
    created = await client.post(
        ADMIN_DOCTORS_URL,
        json={
            "email": "busy@ometus.test",
            "full_name": "Занятый Врач",
            "specialization": "Терапевт",
        },
        headers=headers,
    )
    doctor_id = created.json()["id"]

    await register(client, "some.patient@ometus.test")
    patient_card = await client.get(
        "/api/users/me/patient", headers=await auth_headers(client, "some.patient@ometus.test")
    )

    db.add(
        Appointment(
            patient_id=patient_card.json()["id"],
            doctor_id=doctor_id,
            department_id=1,
            date=date.today() + timedelta(days=3),
            time=time(9, 0),
            status="booked",
        )
    )
    await db.commit()

    warned = await client.put(
        f"{ADMIN_DOCTORS_URL}/{doctor_id}/dismiss",
        json={"dismissed_at": date.today().isoformat()},
        headers=headers,
    )

    assert warned.status_code == 409
    assert warned.json()["error"]["code"] == "DOCTOR_HAS_UPCOMING_APPOINTMENTS"

    confirmed = await client.put(
        f"{ADMIN_DOCTORS_URL}/{doctor_id}/dismiss",
        json={"dismissed_at": date.today().isoformat(), "confirm": True},
        headers=headers,
    )

    assert confirmed.status_code == 200
    assert confirmed.json()["upcoming_appointments"] == 1


async def test_dismissal_can_be_undone(client, db):
    from datetime import date

    headers = await admin_headers(client, db)
    created = await client.post(
        ADMIN_DOCTORS_URL,
        json={
            "email": "returning@ometus.test",
            "full_name": "Вернувшийся Врач",
            "specialization": "Терапевт",
        },
        headers=headers,
    )
    doctor_id = created.json()["id"]

    await client.put(
        f"{ADMIN_DOCTORS_URL}/{doctor_id}/dismiss",
        json={"dismissed_at": date.today().isoformat()},
        headers=headers,
    )
    restored = await client.delete(f"{ADMIN_DOCTORS_URL}/{doctor_id}/dismiss", headers=headers)
    listing = await client.get(DOCTORS_URL)

    assert restored.status_code == 200
    assert restored.json()["dismissed_at"] is None
    assert any(doctor["id"] == doctor_id for doctor in listing.json())


async def test_every_specialty_in_the_map_can_be_booked(client, db):
    headers = await admin_headers(client, db)

    for number, specialization in enumerate(SPECIALIZATION_KEYWORDS):
        await create_doctor(
            client,
            headers,
            {
                "email": f"specialist{number}@ometus.test",
                "full_name": f"Врач Номер{number}",
                "specialization": specialization.capitalize(),
            },
        )

    for specialization in SPECIALIZATION_KEYWORDS:
        found = await client.get(DOCTORS_URL, params={"specialization": specialization})

        assert found.status_code == 200
        assert found.json(), f"по специализации «{specialization}» врач не нашёлся"
