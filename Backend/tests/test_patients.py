from tests.conftest import verify_email

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
PATIENT_URL = "/api/users/me/patient"
ME_URL = "/api/users/me"
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


ADMIN_DEPENDENTS_URL = "/api/admin/patients"


async def test_dependents_are_patients_only(client, db):
    headers = await admin_headers(client, db)

    listing = await client.get(DEPENDENTS_URL, headers=headers)
    creating = await client.post(DEPENDENTS_URL, json={"full_name": "Малыш"}, headers=headers)

    assert listing.status_code == 403
    assert creating.status_code == 403
    assert creating.json()["error"]["code"] == "FORBIDDEN"


async def test_dependents_are_limited_to_five(client):
    await register(client)
    headers = await auth_headers(client)

    for number in range(5):
        created = await client.post(
            DEPENDENTS_URL, json={"full_name": f"Родственник {number}"}, headers=headers
        )
        assert created.status_code == 200

    sixth = await client.post(DEPENDENTS_URL, json={"full_name": "Лишний"}, headers=headers)

    assert sixth.status_code == 409
    assert sixth.json()["error"]["code"] == "DEPENDENTS_LIMIT_REACHED"


async def test_dependent_can_be_edited(client):
    await register(client)
    headers = await auth_headers(client)
    created = await client.post(
        DEPENDENTS_URL, json={"full_name": "Бабушка Оля"}, headers=headers
    )
    dependent_id = created.json()["id"]

    response = await client.put(
        f"{DEPENDENTS_URL}/{dependent_id}",
        json={"full_name": "Бабушка Ольга", "phone": "+992900000001"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Бабушка Ольга"
    assert response.json()["phone"] == "+992900000001"


async def test_dependent_can_be_deleted(client):
    await register(client)
    headers = await auth_headers(client)
    created = await client.post(DEPENDENTS_URL, json={"full_name": "Дедушка"}, headers=headers)
    dependent_id = created.json()["id"]

    response = await client.delete(f"{DEPENDENTS_URL}/{dependent_id}", headers=headers)
    left = await client.get(DEPENDENTS_URL, headers=headers)

    assert response.status_code == 200
    assert left.json() == []


async def test_dependent_of_another_guardian_is_untouchable(client):
    await register(client)
    await register(client, "other@ometus.test")
    mine = await client.post(
        DEPENDENTS_URL, json={"full_name": "Малыш"}, headers=await auth_headers(client)
    )
    dependent_id = mine.json()["id"]
    stranger = await auth_headers(client, "other@ometus.test")

    edited = await client.put(
        f"{DEPENDENTS_URL}/{dependent_id}", json={"full_name": "Чужой"}, headers=stranger
    )
    deleted = await client.delete(f"{DEPENDENTS_URL}/{dependent_id}", headers=stranger)

    assert edited.status_code == 404
    assert deleted.status_code == 404


async def test_admin_adds_dependent_in_patient_account(client, db):
    await register(client)
    patient_user = (await client.get("/api/users/me", headers=await auth_headers(client))).json()
    headers = await admin_headers(client, db)

    created = await client.post(
        f"{ADMIN_DEPENDENTS_URL}/{patient_user['id']}/dependents",
        json={"full_name": "Мама"},
        headers=headers,
    )
    listing = await client.get(
        f"{ADMIN_DEPENDENTS_URL}/{patient_user['id']}/dependents", headers=headers
    )

    assert created.status_code == 200
    assert created.json()["guardian_user_id"] == patient_user["id"]
    assert len(listing.json()) == 1


async def test_patient_card_follows_the_account_name(client):
    await register(client, first_name="Азиз")
    headers = await auth_headers(client)

    await client.put(ME_URL, json={"first_name": "Азиз", "last_name": "Негматов"}, headers=headers)
    card = await client.get(PATIENT_URL, headers=headers)

    assert card.json()["full_name"] == "Азиз Негматов"


async def test_patient_card_name_cannot_be_edited_directly(client):
    await register(client, first_name="Азиз")
    headers = await auth_headers(client)

    response = await client.put(PATIENT_URL, json={"full_name": "Другое Имя"}, headers=headers)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "NAME_FROM_ACCOUNT"
