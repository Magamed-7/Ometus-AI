from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.permissions import get_current_doctor, get_current_patient, require_staff
from app.core.clock import clinic_now
from app.core.errors import AppError
from app.db.database import get_db
from app.schemas.schema_appointment import (
    AppointmentStatus,
    AppointmentCreateIn,
    AppointmentOut,
    AppointmentRescheduleIn,
    DoctorAppointmentOut,
    EmergencyAppointmentIn,
)
from app.services import crud_appointment, crud_doctor, crud_patient, crud_schedule

appointments_router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


async def get_doctor_appointment(appointment_id: int, doctor, db: AsyncSession):
    appointment = await crud_appointment.get_by_id(appointment_id, db)

    if appointment is None or appointment.doctor_id != doctor.id:
        raise AppError(
            code="APPOINTMENT_NOT_FOUND", message="Запись не найдена", status_code=404
        )

    if appointment.status != "booked":
        raise AppError(
            code="APPOINTMENT_NOT_ACTIVE", message="Запись уже закрыта", status_code=400
        )

    return appointment


@appointments_router.get("/me", response_model=list[AppointmentOut])
async def get_my_appointments(
    status: AppointmentStatus | None = None,
    limit: int = Query(crud_appointment.DEFAULT_PAGE_SIZE, ge=1, le=crud_appointment.MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    return await crud_appointment.get_patient_appointments(patient.id, db, status, limit, offset)


@appointments_router.post("", response_model=AppointmentOut)
async def book_appointment(
    data: AppointmentCreateIn,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    doctor = await crud_doctor.get_by_id(data.doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    if crud_doctor.is_dismissed_on(doctor, data.date):
        raise AppError(
            code="DOCTOR_DISMISSED",
            message=f"Врач не принимает с {doctor.dismissed_at:%d.%m.%Y}",
            status_code=409,
        )

    patient_id = patient.id

    if data.patient_id and data.patient_id != patient.id:
        if not await crud_patient.is_bookable_by(data.patient_id, patient.user_id, db):
            raise AppError(
                code="PERMISSION_DENIED",
                message="Нельзя записать этого пациента",
                status_code=403,
            )
        patient_id = data.patient_id

    if datetime.combine(data.date, data.time) < clinic_now():
        raise AppError(
            code="SLOT_IN_PAST",
            message="Нельзя записаться на прошедшее время",
            status_code=400,
        )

    if await crud_appointment.has_appointment_at(patient_id, data.date, data.time, db):
        raise AppError(
            code="PATIENT_BUSY",
            message="На это время у вас уже есть запись к другому врачу",
            status_code=409,
        )

    if await crud_appointment.has_active_appointment(patient_id, data.doctor_id, data.date, db):
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
        patient_id, slot["department_id"], data, db
    )

    if appointment is None:
        raise AppError(
            code="SLOT_TAKEN", message="Это время только что заняли", status_code=409
        )

    return appointment


@appointments_router.post("/emergency", response_model=AppointmentOut)
async def book_emergency_appointment(
    data: EmergencyAppointmentIn,
    current_user=Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    # отпуск врача здесь не проверяется намеренно: экстренная запись и нужна для случаев,
    # когда сетка и отпуска не важны. Остальное проверяется как обычно
    patient = await crud_patient.get_by_id(data.patient_id, db)

    if patient is None:
        raise AppError(code="PATIENT_NOT_FOUND", message="Пациент не найден", status_code=404)

    doctor = await crud_doctor.get_by_id(data.doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    if crud_doctor.is_dismissed_on(doctor, data.date):
        raise AppError(
            code="DOCTOR_DISMISSED",
            message=f"Врач не принимает с {doctor.dismissed_at:%d.%m.%Y}",
            status_code=409,
        )

    departments = await crud_doctor.get_departments(data.doctor_id, db)

    if data.department_id not in [item.id for item in departments]:
        raise AppError(
            code="DOCTOR_NOT_IN_DEPARTMENT",
            message="Врач не работает в этом отделении",
            status_code=400,
        )

    if datetime.combine(data.date, data.time) < clinic_now():
        raise AppError(
            code="SLOT_IN_PAST",
            message="Нельзя записаться на прошедшее время",
            status_code=400,
        )

    appointment = await crud_appointment.create_emergency_appointment(data, db)

    if appointment is None:
        raise AppError(
            code="SLOT_TAKEN", message="Это время только что заняли", status_code=409
        )

    return appointment


@appointments_router.get("/doctor/me", response_model=list[DoctorAppointmentOut])
async def get_doctor_appointments(
    day: date | None = None,
    status: AppointmentStatus | None = None,
    doctor=Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    return await crud_appointment.get_doctor_appointments(doctor.id, db, day, status)


@appointments_router.get("/doctor/me/today", response_model=list[DoctorAppointmentOut])
async def get_doctor_appointments_today(
    doctor=Depends(get_current_doctor), db: AsyncSession = Depends(get_db)
):
    return await crud_appointment.get_doctor_appointments(doctor.id, db, date.today(), "booked")


@appointments_router.put("/doctor/me/{appointment_id}/complete", response_model=AppointmentOut)
async def complete_appointment(
    appointment_id: int,
    doctor=Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    appointment = await get_doctor_appointment(appointment_id, doctor, db)
    return await crud_appointment.set_status(appointment, "completed", db)


@appointments_router.put("/doctor/me/{appointment_id}/no-show", response_model=AppointmentOut)
async def mark_appointment_no_show(
    appointment_id: int,
    doctor=Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    appointment = await get_doctor_appointment(appointment_id, doctor, db)
    return await crud_appointment.set_status(appointment, "no_show", db)


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

    if datetime.combine(data.date, data.time) < clinic_now():
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

    if await crud_appointment.has_appointment_at(
        appointment.patient_id, data.date, data.time, db, exclude_id=appointment.id
    ):
        raise AppError(
            code="PATIENT_BUSY",
            message="На это время у вас уже есть запись к другому врачу",
            status_code=409,
        )

    if data.date != appointment.date and await crud_appointment.has_active_appointment(
        appointment.patient_id, appointment.doctor_id, data.date, db
    ):
        raise AppError(
            code="ALREADY_BOOKED",
            message="У вас уже есть запись к этому врачу на этот день",
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


@appointments_router.delete("/doctor/me/{appointment_id}")
async def cancel_appointment_by_doctor(
    appointment_id: int,
    doctor=Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    appointment = await crud_appointment.get_by_id(appointment_id, db)

    if appointment is None or appointment.doctor_id != doctor.id:
        raise AppError(
            code="APPOINTMENT_NOT_FOUND", message="Запись не найдена", status_code=404
        )

    if appointment.status != "booked":
        raise AppError(
            code="APPOINTMENT_NOT_ACTIVE", message="Запись уже закрыта", status_code=400
        )

    await crud_appointment.set_status(appointment, "cancelled", db)
    return {"message": "Запись отменена"}
