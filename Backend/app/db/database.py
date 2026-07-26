from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.SQL_ECHO, future=True)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# фоновым задачам нужна своя сессия: сессия запроса закрывается сразу после ответа,
# а задача живёт дольше. Отдельная функция — чтобы тесты подменили фабрику на свою
def get_session_factory():
    return AsyncSessionLocal
