from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.permissions import get_current_doctor
from app.core.errors import AppError
from app.db.database import get_db
from app.schemas.schema_schedule import (
    AbsenceCreateIn,
    AbsenceOut,
    ScheduleCreateIn,
    ScheduleOut,
    ScheduleUpdateIn,
)
from app.services import crud_department, crud_doctor, crud_schedule

schedules_router = APIRouter(prefix="/api/schedules", tags=["Schedules"])


@schedules_router.get("/me", response_model=list[ScheduleOut])
async def get_my_schedule(
    doctor=Depends(get_current_doctor), db: AsyncSession = Depends(get_db)
):
    return await crud_schedule.get_schedules(doctor.id, db)


@schedules_router.post("/me", response_model=ScheduleOut)
async def create_my_schedule(
    data: ScheduleCreateIn,
    doctor=Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    if data.start_time >= data.end_time:
        raise AppError(
            code="INVALID_TIME_RANGE",
            message="Начало работы должно быть раньше окончания",
            status_code=400,
        )

    department = await crud_department.get_by_id(data.department_id, db)

    if department is None:
        raise AppError(
            code="DEPARTMENT_NOT_FOUND", message="Отделение не найдено", status_code=404
        )

    departments = await crud_doctor.get_departments(doctor.id, db)

    if data.department_id not in [item.id for item in departments]:
        raise AppError(
            code="DOCTOR_NOT_IN_DEPARTMENT",
            message="Врач не работает в этом отделении",
            status_code=400,
        )

    existing = await crud_schedule.get_schedule_by_weekday(doctor.id, data.weekday, db)

    if data.department_id in [item.department_id for item in existing]:
        raise AppError(
            code="SCHEDULE_ALREADY_EXISTS",
            message="Расписание на этот день уже есть",
            status_code=409,
        )

    return await crud_schedule.create_schedule(doctor.id, data, db)


@schedules_router.get("/me/absences", response_model=list[AbsenceOut])
async def get_my_absences(
    doctor=Depends(get_current_doctor), db: AsyncSession = Depends(get_db)
):
    return await crud_schedule.get_absences(doctor.id, db)


@schedules_router.post("/me/absences", response_model=AbsenceOut)
async def create_my_absence(
    data: AbsenceCreateIn,
    doctor=Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    if data.date_from > data.date_to:
        raise AppError(
            code="INVALID_DATE_RANGE",
            message="Дата начала должна быть раньше даты окончания",
            status_code=400,
        )

    return await crud_schedule.create_absence(doctor.id, data, db)


@schedules_router.delete("/me/absences/{absence_id}")
async def delete_my_absence(
    absence_id: int,
    doctor=Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    absence = await crud_schedule.get_absence_by_id(absence_id, db)

    if absence is None or absence.doctor_id != doctor.id:
        raise AppError(code="ABSENCE_NOT_FOUND", message="Отсутствие не найдено", status_code=404)

    await crud_schedule.delete_absence(absence, db)
    return {"message": "Отсутствие удалено"}


@schedules_router.put("/me/{schedule_id}", response_model=ScheduleOut)
async def update_my_schedule(
    schedule_id: int,
    data: ScheduleUpdateIn,
    doctor=Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    schedule = await crud_schedule.get_schedule_by_id(schedule_id, db)

    if schedule is None or schedule.doctor_id != doctor.id:
        raise AppError(code="SCHEDULE_NOT_FOUND", message="Расписание не найдено", status_code=404)

    start_time = data.start_time or schedule.start_time
    end_time = data.end_time or schedule.end_time

    if start_time >= end_time:
        raise AppError(
            code="INVALID_TIME_RANGE",
            message="Начало работы должно быть раньше окончания",
            status_code=400,
        )

    return await crud_schedule.update_schedule(schedule, data, db)


@schedules_router.delete("/me/{schedule_id}")
async def delete_my_schedule(
    schedule_id: int,
    doctor=Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    schedule = await crud_schedule.get_schedule_by_id(schedule_id, db)

    if schedule is None or schedule.doctor_id != doctor.id:
        raise AppError(code="SCHEDULE_NOT_FOUND", message="Расписание не найдено", status_code=404)

    await crud_schedule.delete_schedule(schedule, db)
    return {"message": "Расписание удалено"}
