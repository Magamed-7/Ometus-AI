from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.model_user import User
from app.models.model_verification import EmailVerificationCode
from app.schemas.schema_auth import RegisterIn
from app.schemas.schema_user import UserUpdateIn
from app.services import crud_patient
from app.services.email import deliver_verification_code, generate_code


async def create_user(data: RegisterIn, db: AsyncSession):
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        role="patient",
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_by_email(email: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_id(user_id: int, db: AsyncSession):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_all_users(db: AsyncSession, role: str | None = None):
    query = select(User)

    if role:
        query = query.where(User.role == role)

    result = await db.execute(query.order_by(User.id))
    return result.scalars().all()


async def set_role(user: User, role: str, db: AsyncSession):
    user.role = role

    await db.commit()
    await db.refresh(user)
    return user


async def update_user(user: User, data: UserUpdateIn, db: AsyncSession):
    user.first_name = data.first_name or user.first_name
    user.last_name = data.last_name or user.last_name
    user.phone = data.phone or user.phone

    # имя владельца аккаунта живёт в users и нигде больше: карточка пациента только
    # отражает его. Иначе после правки профиля в карточке остаётся старое имя,
    # и врач на приёме видит одно, а пациент у себя — другое
    patient = await crud_patient.get_by_user_id(user.id, db)

    if patient is not None:
        patient.full_name = " ".join(
            part for part in [user.first_name, user.last_name] if part
        ) or None
        patient.phone = user.phone or patient.phone

    await db.commit()
    await db.refresh(user)
    return user


async def change_password(user: User, new_password: str, db: AsyncSession):
    user.hashed_password = hash_password(new_password)

    await db.commit()
    await db.refresh(user)
    return user


async def change_email(user: User, new_email: str, db: AsyncSession):
    # новая почта не подтверждена по определению, поэтому сбрасываем флаг:
    # иначе аккаунт можно было бы увести на чужой адрес и войти без подтверждения.
    # Код на новый адрес выпускает и ставит в очередь отправки сам эндпоинт
    user.email = new_email
    user.is_verified = False

    await db.commit()
    await db.refresh(user)
    return user


async def create_verification_code(user: User, db: AsyncSession):
    # один активный код на пользователя: старые гасим, иначе после трёх запросов
    # у человека на руках три рабочих кода, и отозвать их нечем
    await db.execute(
        delete(EmailVerificationCode).where(EmailVerificationCode.user_id == user.id)
    )

    code = generate_code()
    verification = EmailVerificationCode(
        user_id=user.id,
        code=code,
        expires_at=datetime.now(UTC) + timedelta(minutes=settings.EMAIL_CODE_TTL_MINUTES),
    )

    db.add(verification)
    await db.commit()

    # саму отправку здесь не ждём: письмо уходит фоновой задачей, а её статус
    # прилетает клиенту по websocket. Ответ эндпоинта не должен зависеть от Gmail
    return code


async def verify_code(user: User, code: str, db: AsyncSession):
    result = await db.execute(
        select(EmailVerificationCode)
        .where(EmailVerificationCode.user_id == user.id)
        .where(EmailVerificationCode.code == code)
        .where(EmailVerificationCode.expires_at > datetime.now(UTC))
    )
    verification = result.scalar_one_or_none()

    if verification is None:
        return False

    await db.delete(verification)
    user.is_verified = True
    await db.commit()
    return True
