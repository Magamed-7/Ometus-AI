from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.permissions import get_current_patient
from app.core.errors import AppError
from app.db.database import get_db
from app.schemas.schema_appointment import (
    AppointmentCreateIn,
    AppointmentOut,
    AppointmentRescheduleIn,
)
from app.services import crud_appointment, crud_doctor, crud_schedule

appointments_router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


@appointments_router.get("/me", response_model=list[AppointmentOut])
async def get_my_appointments(
    status: str | None = None,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    return await crud_appointment.get_patient_appointments(patient.id, db, status)


@appointments_router.post("", response_model=AppointmentOut)
async def book_appointment(
    data: AppointmentCreateIn,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    doctor = await crud_doctor.get_by_id(data.doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    if datetime.combine(data.date, data.time) < datetime.now():
        raise AppError(
            code="SLOT_IN_PAST",
            message="Нельзя записаться на прошедшее время",
            status_code=400,
        )

    if await crud_appointment.has_active_appointment(patient.id, data.doctor_id, data.date, db):
        raise AppError(
            code="ALREADY_BOOKED",
            message="У вас уже есть запись к этому врачу на этот день",
            status_code=409,
        )

    slot = await crud_schedule.find_slot(data.doctor_id, data.date, data.time, db)

    if slot is None:
        raise AppError(
            code="SLOT_NOT_AVAILABLE",
            message="Это время недоступно для записи",
            status_code=409,
        )

    appointment = await crud_appointment.create_appointment(
        patient.id, slot["department_id"], data, db
    )

    if appointment is None:
        raise AppError(
            code="SLOT_TAKEN", message="Это время только что заняли", status_code=409
        )

    return appointment


@appointments_router.get("/{appointment_id}", response_model=AppointmentOut)
async def get_my_appointment(
    appointment_id: int,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    appointment = await crud_appointment.get_by_id(appointment_id, db)

    if appointment is None or appointment.patient_id != patient.id:
        raise AppError(
            code="APPOINTMENT_NOT_FOUND", message="Запись не найдена", status_code=404
        )

    return appointment


@appointments_router.put("/{appointment_id}/reschedule", response_model=AppointmentOut)
async def reschedule_appointment(
    appointment_id: int,
    data: AppointmentRescheduleIn,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    appointment = await crud_appointment.get_by_id(appointment_id, db)

    if appointment is None or appointment.patient_id != patient.id:
        raise AppError(
            code="APPOINTMENT_NOT_FOUND", message="Запись не найдена", status_code=404
        )

    if appointment.status != "booked":
        raise AppError(
            code="APPOINTMENT_NOT_ACTIVE", message="Запись уже закрыта", status_code=400
        )

    if datetime.combine(data.date, data.time) < datetime.now():
        raise AppError(
            code="SLOT_IN_PAST",
            message="Нельзя записаться на прошедшее время",
            status_code=400,
        )

    slot = await crud_schedule.find_slot(appointment.doctor_id, data.date, data.time, db)

    if slot is None:
        raise AppError(
            code="SLOT_NOT_AVAILABLE",
            message="Это время недоступно для записи",
            status_code=409,
        )

    updated = await crud_appointment.reschedule_appointment(
        appointment, slot["department_id"], data, db
    )

    if updated is None:
        raise AppError(
            code="SLOT_TAKEN", message="Это время только что заняли", status_code=409
        )

    return updated


@appointments_router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: int,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    appointment = await crud_appointment.get_by_id(appointment_id, db)

    if appointment is None or appointment.patient_id != patient.id:
        raise AppError(
            code="APPOINTMENT_NOT_FOUND", message="Запись не найдена", status_code=404
        )

    if appointment.status != "booked":
        raise AppError(
            code="APPOINTMENT_NOT_ACTIVE", message="Запись уже закрыта", status_code=400
        )

    await crud_appointment.set_status(appointment, "cancelled", db)
    return {"message": "Запись отменена"}
