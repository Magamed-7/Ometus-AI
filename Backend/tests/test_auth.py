from tests.conftest import verify_email

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
VERIFY_EMAIL_URL = "/api/auth/verify-email"
REFRESH_URL = "/api/auth/refresh"


async def register(client, email="patient@ometus.test", password="patient1234"):
    return await client.post(
        REGISTER_URL,
        json={"email": email, "password": password, "first_name": "Aziz"},
    )


async def register_verified(client, email="patient@ometus.test", password="patient1234"):
    response = await register(client, email, password)
    await verify_email(client, email)
    return response


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
    await register_verified(client)
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


async def test_new_code_kills_the_previous_one(client, db, sent_emails):
    from app.models.model_user import User
    from app.services import crud_user as crud_user_module
    from sqlalchemy import select

    await register(client)
    first_code = sent_emails[0][1]

    user = (
        await db.execute(select(User).where(User.email == "patient@ometus.test"))
    ).scalar_one()
    await crud_user_module.create_verification_code(user, db)
    second_code = sent_emails[1][1]

    stale = await client.post(
        VERIFY_EMAIL_URL, json={"email": "patient@ometus.test", "code": first_code}
    )
    fresh = await client.post(
        VERIFY_EMAIL_URL, json={"email": "patient@ometus.test", "code": second_code}
    )

    assert stale.status_code == 400
    assert stale.json()["error"]["code"] == "INVALID_CODE"
    assert fresh.status_code == 200


async def test_register_survives_broken_smtp(client, monkeypatch):
    # SMTP лежит: аккаунт уже создан, поэтому 500 отдавать нельзя — иначе пользователь
    # останется и без письма, и без возможности зарегистрироваться заново
    import app.services.crud_user as crud_user_module
    import app.services.email as email_module

    def explode(email, code):
        raise OSError("SMTP недоступен")

    monkeypatch.setattr(email_module, "send_verification_code", explode)
    monkeypatch.setattr(
        crud_user_module, "deliver_verification_code", email_module.deliver_verification_code
    )

    response = await register(client, email="smtp.down@ometus.test")

    assert response.status_code == 200
    assert response.json()["email"] == "smtp.down@ometus.test"


async def test_delivery_reports_failure_instead_of_raising():
    import app.services.email as email_module

    original = email_module.send_verification_code

    def explode(email, code):
        raise OSError("SMTP недоступен")

    email_module.send_verification_code = explode

    try:
        assert await email_module.deliver_verification_code("patient@ometus.test", "123456") is False
    finally:
        email_module.send_verification_code = original


async def test_register_rejects_malformed_email(client):
    response = await client.post(
        REGISTER_URL, json={"email": "не почта", "password": "patient1234"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_login_rejects_malformed_email(client):
    response = await client.post(LOGIN_URL, json={"email": "user@", "password": "patient1234"})

    assert response.status_code == 422


async def test_register_normalizes_email_domain(client):
    response = await register(client, email="Patient@Ometus.TEST")

    assert response.status_code == 200
    # EmailStr приводит домен к нижнему регистру, но локальную часть не трогает —
    # по RFC это разные почтовые ящики
    assert response.json()["email"] == "Patient@ometus.test"


async def test_login_requires_verified_email(client):
    await register(client)
    response = await client.post(
        LOGIN_URL, json={"email": "patient@ometus.test", "password": "patient1234"}
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"


async def test_login_works_right_after_verification(client):
    await register(client)
    await verify_email(client, "patient@ometus.test")

    response = await client.post(
        LOGIN_URL, json={"email": "patient@ometus.test", "password": "patient1234"}
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


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


async def login(client, email="patient@ometus.test", password="patient1234"):
    return await client.post(LOGIN_URL, json={"email": email, "password": password})


async def test_refresh_returns_new_access_token(client):
    await register_verified(client)
    tokens = (await login(client)).json()

    response = await client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"

    me = await client.get(
        "/api/users/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == "patient@ometus.test"


async def test_refresh_rejects_access_token(client):
    await register_verified(client)
    tokens = (await login(client)).json()

    response = await client.post(REFRESH_URL, json={"refresh_token": tokens["access_token"]})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


async def test_refresh_rejects_garbage_token(client):
    response = await client.post(REFRESH_URL, json={"refresh_token": "not-a-token"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"
