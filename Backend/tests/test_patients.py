from tests.conftest import verify_email

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
PATIENT_URL = "/api/users/me/patient"
ADMIN_DOCTORS_URL = "/api/admin/doctors"

DOCTOR_DATA = {
    "email": "doctor@ometus.test",
    "password": "secret1234",
    "full_name": "Иванова Мария",
    "specialization": "Кардиолог",
}


async def register(client, email="patient@ometus.test", password="secret1234", **extra):
    response = await client.post(
        REGISTER_URL,
        json={"email": email, "password": password, **extra},
    )
    if response.status_code == 200:
        await verify_email(client, email)

    return response


async def auth_headers(client, email="patient@ometus.test", password="secret1234"):
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


async def test_patient_profile_created_on_register(client):
    await register(client, first_name="Aziz", last_name="Negmatov", phone="+992900000000")
    headers = await auth_headers(client)

    response = await client.get(PATIENT_URL, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Aziz Negmatov"
    assert body["phone"] == "+992900000000"
    assert body["date_of_birth"] is None


async def test_patient_profile_without_names(client):
    await register(client)
    headers = await auth_headers(client)

    response = await client.get(PATIENT_URL, headers=headers)

    assert response.status_code == 200
    assert response.json()["full_name"] is None


async def test_patient_profile_unauthenticated(client):
    response = await client.get(PATIENT_URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


async def test_doctor_has_no_patient_profile(client, db):
    headers = await admin_headers(client, db)
    await client.post(ADMIN_DOCTORS_URL, json=DOCTOR_DATA, headers=headers)
    doctor_headers = await auth_headers(client, DOCTOR_DATA["email"])

    response = await client.get(PATIENT_URL, headers=doctor_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PATIENT_NOT_FOUND"


async def test_update_patient_profile(client):
    await register(client, first_name="Aziz")
    headers = await auth_headers(client)

    response = await client.put(
        PATIENT_URL,
        json={"date_of_birth": "1998-05-17", "phone": "+992911111111"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["date_of_birth"] == "1998-05-17"
    assert body["phone"] == "+992911111111"
    assert body["full_name"] == "Aziz"


async def test_update_patient_profile_invalid_date(client):
    await register(client)
    headers = await auth_headers(client)

    response = await client.put(PATIENT_URL, json={"date_of_birth": "вчера"}, headers=headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_patients_are_isolated(client):
    await register(client, first_name="Aziz")
    await register(client, "other@ometus.test", first_name="Farrukh")

    first = await client.get(PATIENT_URL, headers=await auth_headers(client))
    second = await client.get(
        PATIENT_URL, headers=await auth_headers(client, "other@ometus.test")
    )

    assert first.json()["full_name"] == "Aziz"
    assert second.json()["full_name"] == "Farrukh"
    assert first.json()["id"] != second.json()["id"]


DEPENDENTS_URL = "/api/users/me/dependents"


async def test_create_dependent(client):
    await register(client, first_name="Aziz")
    headers = await auth_headers(client)

    response = await client.post(
        DEPENDENTS_URL,
        json={"full_name": "Малыш Негматов", "date_of_birth": "2020-01-01"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Малыш Негматов"
    assert body["user_id"] is None
    assert body["guardian_user_id"] is not None


async def test_list_dependents(client):
    await register(client, first_name="Aziz")
    headers = await auth_headers(client)

    await client.post(DEPENDENTS_URL, json={"full_name": "Малыш"}, headers=headers)
    await client.post(DEPENDENTS_URL, json={"full_name": "Бабушка"}, headers=headers)

    response = await client.get(DEPENDENTS_URL, headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_dependents_isolated_between_guardians(client):
    await register(client, first_name="Aziz")
    await register(client, "other@ometus.test", first_name="Farrukh")

    await client.post(
        DEPENDENTS_URL, json={"full_name": "Малыш"}, headers=await auth_headers(client)
    )

    response = await client.get(
        DEPENDENTS_URL, headers=await auth_headers(client, "other@ometus.test")
    )

    assert response.status_code == 200
    assert response.json() == []
