from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.database import get_db
from app.schemas.schema_auth import (
    AccessToken,
    LoginIn,
    RefreshIn,
    RegisterIn,
    TokenPair,
    VerifyEmailIn,
)
from app.schemas.schema_user import UserOut
from app.services import crud_patient, crud_user

auth_router = APIRouter(prefix="/api/auth", tags=["Auth"])


@auth_router.post("/register", response_model=UserOut)
async def register(data: RegisterIn, db: AsyncSession = Depends(get_db)):
    existing_user = await crud_user.get_by_email(data.email, db)

    if existing_user:
        raise AppError(code="EMAIL_ALREADY_EXISTS", message="Email уже занят", status_code=409)

    user = await crud_user.create_user(data, db)
    await crud_patient.create_patient(user, db)
    await crud_user.create_verification_code(user, db)
    return user


@auth_router.post("/login", response_model=TokenPair)
async def login(data: LoginIn, db: AsyncSession = Depends(get_db)):
    user = await crud_user.get_by_email(data.email, db)

    if not user or not verify_password(data.password, user.hashed_password):
        raise AppError(code="INVALID_CREDENTIALS", message="Неверный email или пароль", status_code=401)

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}

    return TokenPair(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@auth_router.post("/refresh", response_model=AccessToken)
async def refresh_token(data: RefreshIn, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise AppError(code="INVALID_TOKEN", message="Неверный refresh токен", status_code=401)

    user = await crud_user.get_by_id(int(payload["sub"]), db)

    if user is None:
        raise AppError(code="USER_NOT_FOUND", message="Пользователь не найден", status_code=404)

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}

    return AccessToken(access_token=create_access_token(token_data))


@auth_router.post("/verify-email", response_model=UserOut)
async def verify_email(data: VerifyEmailIn, db: AsyncSession = Depends(get_db)):
    user = await crud_user.get_by_email(data.email, db)

    if user is None:
        raise AppError(code="USER_NOT_FOUND", message="Пользователь не найден", status_code=404)

    if not await crud_user.verify_code(user, data.code, db):
        raise AppError(code="INVALID_CODE", message="Неверный или просроченный код", status_code=400)

    return user
