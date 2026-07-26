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
