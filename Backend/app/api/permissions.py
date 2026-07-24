from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.errors import AppError
from app.db.database import get_db
from app.services import crud_doctor, crud_patient


def require_role(role: str):
    def role_checker(current_user=Depends(get_current_user)):
        if current_user.role != role:
            raise AppError(code="FORBIDDEN", message="Недостаточно прав", status_code=403)
        return current_user

    return role_checker


def require_staff(current_user=Depends(get_current_user)):
    if current_user.role not in ("registrar", "admin"):
        raise AppError(code="FORBIDDEN", message="Недостаточно прав", status_code=403)
    return current_user


async def get_current_doctor(
    current_user=Depends(require_role("doctor")), db: AsyncSession = Depends(get_db)
):
    doctor = await crud_doctor.get_by_user_id(current_user.id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    return doctor


async def get_current_patient(
    current_user=Depends(require_role("patient")), db: AsyncSession = Depends(get_db)
):
    patient = await crud_patient.get_by_user_id(current_user.id, db)

    if patient is None:
        raise AppError(
            code="PATIENT_NOT_FOUND", message="Профиль пациента не найден", status_code=404
        )

    return patient
