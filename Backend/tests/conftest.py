import pytest
from httpx import ASGITransport, AsyncClient
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


@event.listens_for(test_engine.sync_engine, "connect")
def register_unicode_lower(dbapi_connection, connection_record):
    dbapi_connection.driver_connection._conn.create_function("lower", 1, str.lower)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def prepare_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def sent_emails(monkeypatch):
    sent = []
    fake_send = lambda email, code: sent.append((email, code))
    monkeypatch.setattr(crud_user, "send_verification_code", fake_send)
    return sent


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db():
    async with TestSessionLocal() as session:
        yield session
