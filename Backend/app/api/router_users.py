from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.errors import AppError
from app.db.database import get_db
from app.models.model_user import User
from app.schemas.schema_patient import PatientOut, PatientUpdateIn
from app.schemas.schema_user import UserOut, UserUpdateIn
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
