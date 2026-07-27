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


async def get_all_users(
    db: AsyncSession,
    role: str | None = None,
    email: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    query = select(User)

    if role:
        query = query.where(User.role == role)

    if email:
        query = query.where(User.email.ilike(f"%{email.strip()}%"))

    result = await db.execute(query.order_by(User.id).limit(limit).offset(offset))
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
    user.email = new_email
    user.is_verified = False

    await db.commit()
    await db.refresh(user)
    return user


RESEND_COOLDOWN_SECONDS = 60


async def seconds_since_last_code(user: User, db: AsyncSession):
    result = await db.execute(
        select(EmailVerificationCode.created_at)
        .where(EmailVerificationCode.user_id == user.id)
        .order_by(EmailVerificationCode.created_at.desc())
        .limit(1)
    )
    issued_at = result.scalar_one_or_none()

    if issued_at is None:
        return None

    if issued_at.tzinfo is None:
        issued_at = issued_at.replace(tzinfo=UTC)

    return (datetime.now(UTC) - issued_at).total_seconds()


async def create_verification_code(user: User, db: AsyncSession):
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
