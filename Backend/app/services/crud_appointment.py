from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_appointment import Appointment
from app.models.model_doctor import Doctor
from app.models.model_patient import Patient
from app.schemas.schema_appointment import (
    AppointmentCreateIn,
    AppointmentRescheduleIn,
    EmergencyAppointmentIn,
)

ACTIVE_STATUSES = ["booked", "completed", "no_show"]


async def create_appointment(
    patient_id: int, department_id: int, data: AppointmentCreateIn, db: AsyncSession
):
    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=data.doctor_id,
        department_id=department_id,
        date=data.date,
        time=data.time,
        status="booked",
    )

    db.add(appointment)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return None

    await db.refresh(appointment)
    return appointment


async def create_emergency_appointment(data: EmergencyAppointmentIn, db: AsyncSession):
    appointment = Appointment(
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        department_id=data.department_id,
        date=data.date,
        time=data.time,
        status="booked",
        is_emergency=True,
    )

    db.add(appointment)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return None

    await db.refresh(appointment)
    return appointment


async def get_by_id(appointment_id: int, db: AsyncSession):
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    return result.scalar_one_or_none()


async def get_patient_appointments(
    patient_id: int, db: AsyncSession, status: str | None = None
):
    query = select(Appointment).where(Appointment.patient_id == patient_id)

    if status:
        query = query.where(Appointment.status == status)

    result = await db.execute(query.order_by(Appointment.date.desc(), Appointment.time.desc()))
    return result.scalars().all()


async def get_doctor_appointments(
    doctor_id: int, db: AsyncSession, day: date | None = None, status: str | None = None
):
    query = (
        select(Appointment, Patient)
        .join(Patient, Patient.id == Appointment.patient_id)
        .where(Appointment.doctor_id == doctor_id)
    )

    if day:
        query = query.where(Appointment.date == day)

    if status:
        query = query.where(Appointment.status == status)

    result = await db.execute(query.order_by(Appointment.date, Appointment.time))

    return [
        {
            "id": appointment.id,
            "patient_id": patient.id,
            "patient_name": patient.full_name,
            "patient_phone": patient.phone,
            "department_id": appointment.department_id,
            "date": appointment.date,
            "time": appointment.time,
            "status": appointment.status,
        }
        for appointment, patient in result.all()
    ]


async def get_all_appointments(
    db: AsyncSession,
    doctor_id: int | None = None,
    patient_id: int | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    query = (
        select(Appointment, Patient, Doctor)
        .join(Patient, Patient.id == Appointment.patient_id)
        .join(Doctor, Doctor.id == Appointment.doctor_id)
    )

    if doctor_id:
        query = query.where(Appointment.doctor_id == doctor_id)

    if patient_id:
        query = query.where(Appointment.patient_id == patient_id)

    if status:
        query = query.where(Appointment.status == status)

    if date_from:
        query = query.where(Appointment.date >= date_from)

    if date_to:
        query = query.where(Appointment.date <= date_to)

    result = await db.execute(query.order_by(Appointment.date.desc(), Appointment.time.desc()))

    return [
        {
            "id": appointment.id,
            "patient_id": patient.id,
            "patient_name": patient.full_name,
            "patient_phone": patient.phone,
            "doctor_id": doctor.id,
            "doctor_name": doctor.full_name,
            "specialization": doctor.specialization,
            "department_id": appointment.department_id,
            "date": appointment.date,
            "time": appointment.time,
            "status": appointment.status,
            "is_emergency": appointment.is_emergency,
            "created_at": appointment.created_at,
        }
        for appointment, patient, doctor in result.all()
    ]


async def get_taken_times(doctor_id: int, day: date, db: AsyncSession):
    result = await db.execute(
        select(Appointment.time)
        .where(Appointment.doctor_id == doctor_id)
        .where(Appointment.date == day)
        .where(Appointment.status.in_(ACTIVE_STATUSES))
    )
    return result.scalars().all()


HOUR_WEIGHTS = {"completed": 2, "booked": 1, "cancelled": -1, "no_show": -2}


async def get_hour_preferences(patient_id: int, db: AsyncSession):
    result = await db.execute(
        select(Appointment.time, Appointment.status).where(Appointment.patient_id == patient_id)
    )

    preferences = {}

    for slot_time, status in result.all():
        weight = HOUR_WEIGHTS.get(status, 0)

        if weight:
            preferences[slot_time.hour] = preferences.get(slot_time.hour, 0) + weight

    return preferences


async def has_active_appointment(patient_id: int, doctor_id: int, day: date, db: AsyncSession):
    result = await db.execute(
        select(Appointment)
        .where(Appointment.patient_id == patient_id)
        .where(Appointment.doctor_id == doctor_id)
        .where(Appointment.date == day)
        .where(Appointment.status == "booked")
    )
    return result.scalars().first() is not None


async def set_status(appointment: Appointment, status: str, db: AsyncSession):
    appointment.status = status

    await db.commit()
    await db.refresh(appointment)
    return appointment


async def reschedule_appointment(
    appointment: Appointment, department_id: int, data: AppointmentRescheduleIn, db: AsyncSession
):
    appointment.department_id = department_id
    appointment.date = data.date
    appointment.time = data.time

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return None

    await db.refresh(appointment)
    return appointment
