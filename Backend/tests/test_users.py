REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
ME_URL = "/api/users/me"


async def register(client, email="patient@ometus.test", password="patient1234"):
    return await client.post(
        REGISTER_URL,
        json={"email": email, "password": password, "first_name": "Aziz"},
    )


async def auth_headers(client, email="patient@ometus.test", password="patient1234"):
    login_response = await client.post(LOGIN_URL, json={"email": email, "password": password})
    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


async def test_get_me(client):
    await register(client)
    headers = await auth_headers(client)

    response = await client.get(ME_URL, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "patient@ometus.test"
    assert body["first_name"] == "Aziz"


async def test_get_me_unauthenticated(client):
    response = await client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


async def test_update_me(client):
    await register(client)
    headers = await auth_headers(client)

    response = await client.put(
        ME_URL, json={"last_name": "Negmatov", "phone": "+992900000000"}, headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["last_name"] == "Negmatov"
    assert body["phone"] == "+992900000000"
    assert body["first_name"] == "Aziz"


async def test_update_me_unauthenticated(client):
    response = await client.put(ME_URL, json={"last_name": "Negmatov"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"
