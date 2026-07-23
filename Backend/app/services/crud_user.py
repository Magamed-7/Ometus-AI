from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.model_user import User
from app.models.model_verification import EmailVerificationCode
from app.schemas.schema_auth import RegisterIn
from app.schemas.schema_user import UserUpdateIn
from app.services.email import generate_code, send_verification_code


async def create_user(data: RegisterIn, db: AsyncSession):
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        role=data.role,
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


async def update_user(user: User, data: UserUpdateIn, db: AsyncSession):
    user.first_name = data.first_name or user.first_name
    user.last_name = data.last_name or user.last_name
    user.phone = data.phone or user.phone

    await db.commit()
    await db.refresh(user)
    return user


async def create_verification_code(user: User, db: AsyncSession):
    code = generate_code()
    verification = EmailVerificationCode(
        user_id=user.id,
        code=code,
        expires_at=datetime.now(UTC) + timedelta(minutes=settings.EMAIL_CODE_TTL_MINUTES),
    )

    db.add(verification)
    await db.commit()

    send_verification_code(user.email, code)
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
