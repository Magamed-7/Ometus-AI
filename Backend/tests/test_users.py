from tests.conftest import verify_email

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
ME_URL = "/api/users/me"
PASSWORD_URL = "/api/users/me/password"
EMAIL_URL = "/api/users/me/email"


async def register(client, email="patient@ometus.test", password="patient1234"):
    response = await client.post(
        REGISTER_URL,
        json={"email": email, "password": password, "first_name": "Aziz"},
    )
    if response.status_code == 200:
        await verify_email(client, email)

    return response


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


async def test_change_password_and_login_with_it(client):
    await register(client)
    headers = await auth_headers(client)

    response = await client.put(
        PASSWORD_URL,
        json={"current_password": "patient1234", "new_password": "brand-new-4321"},
        headers=headers,
    )

    assert response.status_code == 200

    with_old = await client.post(
        LOGIN_URL, json={"email": "patient@ometus.test", "password": "patient1234"}
    )
    with_new = await client.post(
        LOGIN_URL, json={"email": "patient@ometus.test", "password": "brand-new-4321"}
    )

    assert with_old.status_code == 401
    assert with_new.status_code == 200


async def test_change_password_checks_the_current_one(client):
    await register(client)
    headers = await auth_headers(client)

    response = await client.put(
        PASSWORD_URL,
        json={"current_password": "not-my-password", "new_password": "brand-new-4321"},
        headers=headers,
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_change_password_rejects_short_one(client):
    await register(client)
    headers = await auth_headers(client)

    response = await client.put(
        PASSWORD_URL,
        json={"current_password": "patient1234", "new_password": "short"},
        headers=headers,
    )

    assert response.status_code == 422


async def test_change_email_requires_new_verification(client, sent_emails):
    await register(client)
    headers = await auth_headers(client)

    response = await client.put(
        EMAIL_URL,
        json={"email": "new.address@ometus.test", "password": "patient1234"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["email"] == "new.address@ometus.test"

    blocked = await client.post(
        LOGIN_URL, json={"email": "new.address@ometus.test", "password": "patient1234"}
    )
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"

    assert sent_emails[-1][0] == "new.address@ometus.test"

    await verify_email(client, "new.address@ometus.test")
    allowed = await client.post(
        LOGIN_URL, json={"email": "new.address@ometus.test", "password": "patient1234"}
    )
    assert allowed.status_code == 200


async def test_change_email_rejects_taken_address(client):
    await register(client)
    await register(client, email="someone.else@ometus.test")
    headers = await auth_headers(client)

    response = await client.put(
        EMAIL_URL,
        json={"email": "someone.else@ometus.test", "password": "patient1234"},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


async def test_change_email_checks_password(client):
    await register(client)
    headers = await auth_headers(client)

    response = await client.put(
        EMAIL_URL,
        json={"email": "new.address@ometus.test", "password": "not-my-password"},
        headers=headers,
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
