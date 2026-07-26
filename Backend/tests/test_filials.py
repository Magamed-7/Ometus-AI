from tests.conftest import verify_email

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
FILIALS_URL = "/api/filials"
ADMIN_FILIALS_URL = "/api/admin/filials"

FILIAL_DATA = {
    "name": "Ometus Центр",
    "city": "Душанбе",
    "address": "ул. Рудаки 100",
    "phone": "+992900000000",
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


async def test_create_filial(client, db):
    headers = await admin_headers(client, db)

    response = await client.post(ADMIN_FILIALS_URL, json=FILIAL_DATA, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Ometus Центр"
    assert body["city"] == "Душанбе"


async def test_create_filial_forbidden_for_patient(client):
    await register(client, "patient@ometus.test")
    headers = await auth_headers(client, "patient@ometus.test")

    response = await client.post(ADMIN_FILIALS_URL, json=FILIAL_DATA, headers=headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_create_filial_unauthenticated(client):
    response = await client.post(ADMIN_FILIALS_URL, json=FILIAL_DATA)

    assert response.status_code == 401


async def test_list_filials_is_public(client, db):
    headers = await admin_headers(client, db)
    await client.post(ADMIN_FILIALS_URL, json=FILIAL_DATA, headers=headers)

    response = await client.get(FILIALS_URL)

    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_list_filials_by_city(client, db):
    headers = await admin_headers(client, db)
    await client.post(ADMIN_FILIALS_URL, json=FILIAL_DATA, headers=headers)
    await client.post(
        ADMIN_FILIALS_URL,
        json={**FILIAL_DATA, "name": "Ometus Худжанд", "city": "Худжанд"},
        headers=headers,
    )

    response = await client.get(FILIALS_URL, params={"city": "Худжанд"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["city"] == "Худжанд"


async def test_get_filial_not_found(client):
    response = await client.get(f"{FILIALS_URL}/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FILIAL_NOT_FOUND"


async def test_update_filial(client, db):
    headers = await admin_headers(client, db)
    created = await client.post(ADMIN_FILIALS_URL, json=FILIAL_DATA, headers=headers)
    filial_id = created.json()["id"]

    response = await client.put(
        f"{ADMIN_FILIALS_URL}/{filial_id}", json={"phone": "+992911111111"}, headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["phone"] == "+992911111111"
    assert body["name"] == "Ometus Центр"


async def test_delete_filial(client, db):
    headers = await admin_headers(client, db)
    created = await client.post(ADMIN_FILIALS_URL, json=FILIAL_DATA, headers=headers)
    filial_id = created.json()["id"]

    response = await client.delete(f"{ADMIN_FILIALS_URL}/{filial_id}", headers=headers)

    assert response.status_code == 200

    listed = await client.get(FILIALS_URL)
    assert listed.json() == []
