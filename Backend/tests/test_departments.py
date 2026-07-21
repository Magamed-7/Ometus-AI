REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
DEPARTMENTS_URL = "/api/departments"
ADMIN_FILIALS_URL = "/api/admin/filials"
ADMIN_DEPARTMENTS_URL = "/api/admin/departments"

FILIAL_DATA = {"name": "Ometus Центр", "city": "Душанбе", "address": "ул. Рудаки 100"}


async def register(client, email, password="secret1234", role="patient"):
    return await client.post(
        REGISTER_URL,
        json={"email": email, "password": password, "role": role},
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


async def create_filial(client, headers):
    response = await client.post(ADMIN_FILIALS_URL, json=FILIAL_DATA, headers=headers)
    return response.json()["id"]


async def test_create_department(client, db):
    headers = await admin_headers(client, db)
    filial_id = await create_filial(client, headers)

    response = await client.post(
        ADMIN_DEPARTMENTS_URL,
        json={"filial_id": filial_id, "name": "Кардиология"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Кардиология"
    assert body["filial_id"] == filial_id


async def test_create_department_unknown_filial(client, db):
    headers = await admin_headers(client, db)

    response = await client.post(
        ADMIN_DEPARTMENTS_URL, json={"filial_id": 999, "name": "Кардиология"}, headers=headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FILIAL_NOT_FOUND"


async def test_create_department_forbidden_for_patient(client, db):
    admin = await admin_headers(client, db)
    filial_id = await create_filial(client, admin)

    await register(client, "patient@ometus.test")
    headers = await auth_headers(client, "patient@ometus.test")

    response = await client.post(
        ADMIN_DEPARTMENTS_URL,
        json={"filial_id": filial_id, "name": "Кардиология"},
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_list_departments_by_filial(client, db):
    headers = await admin_headers(client, db)
    first_filial = await create_filial(client, headers)
    second = await client.post(
        ADMIN_FILIALS_URL,
        json={**FILIAL_DATA, "name": "Ometus Худжанд", "city": "Худжанд"},
        headers=headers,
    )
    second_filial = second.json()["id"]

    await client.post(
        ADMIN_DEPARTMENTS_URL,
        json={"filial_id": first_filial, "name": "Кардиология"},
        headers=headers,
    )
    await client.post(
        ADMIN_DEPARTMENTS_URL,
        json={"filial_id": second_filial, "name": "Неврология"},
        headers=headers,
    )

    response = await client.get(DEPARTMENTS_URL, params={"filial_id": second_filial})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Неврология"


async def test_get_department_not_found(client):
    response = await client.get(f"{DEPARTMENTS_URL}/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DEPARTMENT_NOT_FOUND"


async def test_update_department(client, db):
    headers = await admin_headers(client, db)
    filial_id = await create_filial(client, headers)
    created = await client.post(
        ADMIN_DEPARTMENTS_URL,
        json={"filial_id": filial_id, "name": "Кардиология"},
        headers=headers,
    )
    department_id = created.json()["id"]

    response = await client.put(
        f"{ADMIN_DEPARTMENTS_URL}/{department_id}",
        json={"description": "Лечение сердца"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["description"] == "Лечение сердца"
    assert body["name"] == "Кардиология"


async def test_delete_department(client, db):
    headers = await admin_headers(client, db)
    filial_id = await create_filial(client, headers)
    created = await client.post(
        ADMIN_DEPARTMENTS_URL,
        json={"filial_id": filial_id, "name": "Кардиология"},
        headers=headers,
    )
    department_id = created.json()["id"]

    response = await client.delete(
        f"{ADMIN_DEPARTMENTS_URL}/{department_id}", headers=headers
    )

    assert response.status_code == 200

    listed = await client.get(DEPARTMENTS_URL)
    assert listed.json() == []
