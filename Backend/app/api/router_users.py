from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.errors import AppError
from app.core.security import verify_password
from app.db.database import get_db
from app.models.model_user import User
from app.schemas.schema_patient import DependentCreateIn, PatientOut, PatientUpdateIn
from app.schemas.schema_user import EmailChangeIn, PasswordChangeIn, UserOut, UserUpdateIn
from app.services import crud_patient, crud_user

users_router = APIRouter(prefix="/api/users", tags=["Users"])


@users_router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@users_router.put("/me", response_model=UserOut)
async def update_me(
    data: UserUpdateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await crud_user.update_user(current_user, data, db)


@users_router.put("/me/password", response_model=UserOut)
async def change_my_password(
    data: PasswordChangeIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise AppError(code="INVALID_CREDENTIALS", message="Текущий пароль неверен", status_code=401)

    if data.current_password == data.new_password:
        raise AppError(
            code="PASSWORD_NOT_CHANGED",
            message="Новый пароль совпадает со старым",
            status_code=400,
        )

    return await crud_user.change_password(current_user, data.new_password, db)


@users_router.put("/me/email", response_model=UserOut)
async def change_my_email(
    data: EmailChangeIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # пароль спрашиваем не для галочки: смена почты — это смена точки восстановления доступа
    if not verify_password(data.password, current_user.hashed_password):
        raise AppError(code="INVALID_CREDENTIALS", message="Пароль неверен", status_code=401)

    if data.email == current_user.email:
        raise AppError(
            code="EMAIL_NOT_CHANGED", message="Это ваша текущая почта", status_code=400
        )

    if await crud_user.get_by_email(data.email, db):
        raise AppError(code="EMAIL_ALREADY_EXISTS", message="Email уже занят", status_code=409)

    return await crud_user.change_email(current_user, data.email, db)


@users_router.get("/me/patient", response_model=PatientOut)
async def get_my_patient_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    patient = await crud_patient.get_by_user_id(current_user.id, db)

    if patient is None:
        raise AppError(code="PATIENT_NOT_FOUND", message="Профиль пациента не найден", status_code=404)

    return patient


@users_router.put("/me/patient", response_model=PatientOut)
async def update_my_patient_profile(
    data: PatientUpdateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    patient = await crud_patient.get_by_user_id(current_user.id, db)

    if patient is None:
        raise AppError(code="PATIENT_NOT_FOUND", message="Профиль пациента не найден", status_code=404)

    return await crud_patient.update_patient(patient, data, db)


@users_router.get("/me/dependents", response_model=list[PatientOut])
async def get_my_dependents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await crud_patient.get_dependents(current_user.id, db)


@users_router.post("/me/dependents", response_model=PatientOut)
async def add_my_dependent(
    data: DependentCreateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await crud_patient.create_dependent(current_user, data, db)
