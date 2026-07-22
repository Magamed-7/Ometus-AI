from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.permissions import require_role
from app.core.errors import AppError
from app.db.database import get_db
from app.schemas.schema_department import (
    DepartmentCreateIn,
    DepartmentOut,
    DepartmentUpdateIn,
)
from app.schemas.schema_doctor import DoctorCreateIn, DoctorDepartmentIn, DoctorOut, DoctorUpdateIn
from app.schemas.schema_filial import FilialCreateIn, FilialOut, FilialUpdateIn
from app.schemas.schema_report import AppointmentsSummaryOut, DoctorWorkloadOut
from app.services import crud_department, crud_doctor, crud_filial, crud_report, crud_user

admin_router = APIRouter(prefix="/api/admin", tags=["Admin"])


@admin_router.post("/filials", response_model=FilialOut)
async def create_filial(
    data: FilialCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    return await crud_filial.create_filial(data, db)


@admin_router.put("/filials/{filial_id}", response_model=FilialOut)
async def update_filial(
    filial_id: int,
    data: FilialUpdateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    filial = await crud_filial.get_by_id(filial_id, db)

    if filial is None:
        raise AppError(code="FILIAL_NOT_FOUND", message="Филиал не найден", status_code=404)

    return await crud_filial.update_filial(filial, data, db)


@admin_router.delete("/filials/{filial_id}")
async def delete_filial(
    filial_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    filial = await crud_filial.get_by_id(filial_id, db)

    if filial is None:
        raise AppError(code="FILIAL_NOT_FOUND", message="Филиал не найден", status_code=404)

    await crud_filial.delete_filial(filial, db)
    return {"message": "Филиал удалён"}


@admin_router.post("/departments", response_model=DepartmentOut)
async def create_department(
    data: DepartmentCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    filial = await crud_filial.get_by_id(data.filial_id, db)

    if filial is None:
        raise AppError(code="FILIAL_NOT_FOUND", message="Филиал не найден", status_code=404)

    return await crud_department.create_department(data, db)


@admin_router.put("/departments/{department_id}", response_model=DepartmentOut)
async def update_department(
    department_id: int,
    data: DepartmentUpdateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    department = await crud_department.get_by_id(department_id, db)

    if department is None:
        raise AppError(
            code="DEPARTMENT_NOT_FOUND", message="Отделение не найдено", status_code=404
        )

    return await crud_department.update_department(department, data, db)


@admin_router.delete("/departments/{department_id}")
async def delete_department(
    department_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    department = await crud_department.get_by_id(department_id, db)

    if department is None:
        raise AppError(
            code="DEPARTMENT_NOT_FOUND", message="Отделение не найдено", status_code=404
        )

    await crud_department.delete_department(department, db)
    return {"message": "Отделение удалено"}


@admin_router.post("/doctors", response_model=DoctorOut)
async def create_doctor(
    data: DoctorCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    existing_user = await crud_user.get_by_email(data.email, db)

    if existing_user:
        raise AppError(code="EMAIL_ALREADY_EXISTS", message="Email уже занят", status_code=409)

    return await crud_doctor.create_doctor(data, db)


@admin_router.put("/doctors/{doctor_id}", response_model=DoctorOut)
async def update_doctor(
    doctor_id: int,
    data: DoctorUpdateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    return await crud_doctor.update_doctor(doctor, data, db)


@admin_router.post("/doctors/{doctor_id}/departments")
async def assign_doctor_department(
    doctor_id: int,
    data: DoctorDepartmentIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    department = await crud_department.get_by_id(data.department_id, db)

    if department is None:
        raise AppError(
            code="DEPARTMENT_NOT_FOUND", message="Отделение не найдено", status_code=404
        )

    assignment = await crud_doctor.assign_department(doctor_id, data.department_id, db)

    if assignment is None:
        raise AppError(
            code="DOCTOR_ALREADY_IN_DEPARTMENT",
            message="Врач уже назначен в это отделение",
            status_code=409,
        )

    return {"message": "Врач назначен в отделение"}


@admin_router.delete("/doctors/{doctor_id}/departments/{department_id}")
async def remove_doctor_department(
    doctor_id: int,
    department_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    assignment = await crud_doctor.remove_department(doctor_id, department_id, db)

    if assignment is None:
        raise AppError(
            code="DOCTOR_NOT_IN_DEPARTMENT",
            message="Врач не назначен в это отделение",
            status_code=404,
        )

    return {"message": "Врач снят с отделения"}


@admin_router.get("/reports/workload", response_model=list[DoctorWorkloadOut])
async def get_workload_report(
    date_from: date,
    date_to: date,
    department_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    if date_from > date_to:
        raise AppError(
            code="INVALID_DATE_RANGE",
            message="Дата начала должна быть раньше даты окончания",
            status_code=400,
        )

    if department_id:
        department = await crud_department.get_by_id(department_id, db)

        if department is None:
            raise AppError(
                code="DEPARTMENT_NOT_FOUND", message="Отделение не найдено", status_code=404
            )

    return await crud_report.get_doctor_workload(db, date_from, date_to, department_id)


@admin_router.get("/reports/summary", response_model=AppointmentsSummaryOut)
async def get_summary_report(
    date_from: date,
    date_to: date,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    if date_from > date_to:
        raise AppError(
            code="INVALID_DATE_RANGE",
            message="Дата начала должна быть раньше даты окончания",
            status_code=400,
        )

    return await crud_report.get_appointments_summary(db, date_from, date_to)
