from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.db.database import get_db
from app.schemas.schema_department import DepartmentOut
from app.schemas.schema_doctor import DoctorOut
from app.services import crud_doctor

doctors_router = APIRouter(prefix="/api/doctors", tags=["Doctors"])


@doctors_router.get("", response_model=list[DoctorOut])
async def search_doctors(
    specialization: str | None = None,
    department_id: int | None = None,
    filial_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await crud_doctor.search_doctors(db, specialization, department_id, filial_id)


@doctors_router.get("/{doctor_id}", response_model=DoctorOut)
async def get_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    return doctor


@doctors_router.get("/{doctor_id}/departments", response_model=list[DepartmentOut])
async def get_doctor_departments(doctor_id: int, db: AsyncSession = Depends(get_db)):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    return await crud_doctor.get_departments(doctor_id, db)
