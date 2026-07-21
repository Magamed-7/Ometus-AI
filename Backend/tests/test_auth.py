REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
VERIFY_EMAIL_URL = "/api/auth/verify-email"


async def register(client, email="patient@ometus.test", password="patient1234"):
    return await client.post(
        REGISTER_URL,
        json={"email": email, "password": password, "first_name": "Aziz"},
    )


async def test_register_success(client):
    response = await register(client)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "patient@ometus.test"
    assert body["role"] == "patient"
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_duplicate_email(client):
    await register(client)
    response = await register(client)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


async def test_register_sends_verification_code(client, sent_emails):
    await register(client)

    assert len(sent_emails) == 1
    email, code = sent_emails[0]
    assert email == "patient@ometus.test"
    assert len(code) == 6


async def test_login_success(client):
    await register(client)
    response = await client.post(
        LOGIN_URL, json={"email": "patient@ometus.test", "password": "patient1234"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


async def test_login_wrong_password(client):
    await register(client)
    response = await client.post(
        LOGIN_URL, json={"email": "patient@ometus.test", "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_verify_email_success(client, sent_emails):
    await register(client)
    _, code = sent_emails[0]

    response = await client.post(
        VERIFY_EMAIL_URL, json={"email": "patient@ometus.test", "code": code}
    )

    assert response.status_code == 200
    assert response.json()["email"] == "patient@ometus.test"


async def test_verify_email_wrong_code(client, sent_emails):
    await register(client)

    response = await client.post(
        VERIFY_EMAIL_URL, json={"email": "patient@ometus.test", "code": "000000"}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_CODE"


async def test_verify_email_code_is_single_use(client, sent_emails):
    await register(client)
    _, code = sent_emails[0]

    first = await client.post(
        VERIFY_EMAIL_URL, json={"email": "patient@ometus.test", "code": code}
    )
    second = await client.post(
        VERIFY_EMAIL_URL, json={"email": "patient@ometus.test", "code": code}
    )

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "INVALID_CODE"


async def test_verify_email_unknown_email(client):
    response = await client.post(
        VERIFY_EMAIL_URL, json={"email": "nobody@ometus.test", "code": "000000"}
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "USER_NOT_FOUND"
