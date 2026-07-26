import email_validator
import pytest
from httpx import ASGITransport, AsyncClient

# после перехода схем на EmailStr домен `.test` перестал проходить валидацию:
# email-validator по умолчанию режет зарезервированные домены (.test/.example/.invalid).
# Тесты как раз для того их и используют, поэтому в тестовой среде разрешаем
email_validator.TEST_ENVIRONMENT = True
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.services.crud_user as crud_user
from app.db.database import Base, get_db
from app.main import app

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)


def unicode_lower(value):
    return value.lower() if value is not None else None


@event.listens_for(test_engine.sync_engine, "connect")
def register_unicode_lower(dbapi_connection, connection_record):
    dbapi_connection.driver_connection._conn.create_function("lower", 1, unicode_lower)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db

# фоновые задачи берут сессию не через Depends, а через фабрику — её тоже уводим
# на тестовую базу, иначе задача пойдёт в настоящий Postgres
import app.db.database as database_module  # noqa: E402

database_module.get_session_factory = lambda: TestSessionLocal


@pytest.fixture(autouse=True)
async def prepare_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# последний код, выданный каждой почте: письма в тестах никуда не уходят,
# а подтвердить почту нужно — вход без этого теперь запрещён
SENT_CODES = {}


@pytest.fixture(autouse=True)
def sent_emails(monkeypatch):
    sent = []

    async def fake_deliver(email, code):
        sent.append((email, code))
        SENT_CODES[email] = code
        return True

    SENT_CODES.clear()
    monkeypatch.setattr(crud_user, "deliver_verification_code", fake_deliver)
    return sent


async def verify_email(client, email):
    return await client.post(
        "/api/auth/verify-email", json={"email": email, "code": SENT_CODES[email]}
    )


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db():
    async with TestSessionLocal() as session:
        yield session
