from datetime import date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import clinic_now
from app.schemas.schema_appointment import AppointmentCreateIn, AppointmentRescheduleIn
from app.services import crud_appointment, crud_department, crud_doctor, crud_schedule

SEARCH_DAYS_AHEAD = 14


def tool_error(code: str, message: str):
    return {"ok": False, "error": {"code": code, "message": message}}


def tool_result(data):
    return {"ok": True, "data": data}


def is_future(day: date, slot_time: time):
    return datetime.combine(day, slot_time) >= clinic_now()


async def find_doctors(
    db: AsyncSession, specialization: str | None = None, department: str | None = None
):
    department_id = None

    if department:
        departments = await crud_department.get_departments(db)
        matched = [item for item in departments if department.lower() in item.name.lower()]

        if not matched:
            return tool_error(
                "DEPARTMENT_NOT_FOUND", f"Отделение «{department}» не найдено"
            )

        department_id = matched[0].id

    doctors = await crud_doctor.search_doctors(db, specialization, department_id)

    if not doctors:
        return tool_error("DOCTORS_NOT_FOUND", "Подходящих врачей не нашлось")

    return tool_result(
        [
            {
                "doctor_id": doctor.id,
                "full_name": doctor.full_name,
                "specialization": doctor.specialization,
            }
            for doctor in doctors
        ]
    )


async def get_available_time(db: AsyncSession, doctor_id: int, day: date | None = None):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        return tool_error("DOCTOR_NOT_FOUND", "Врач не найден")

    days = [day] if day else [date.today() + timedelta(days=shift) for shift in range(SEARCH_DAYS_AHEAD)]
    found = []

    for current in days:
        slots = await crud_schedule.get_available_slots(doctor_id, current, db)
        found.extend(
            {"date": str(current), "time": str(slot["time"])}
            for slot in slots
            if is_future(current, slot["time"])
        )

        if found and not day:
            break

    if not found:
        return tool_error(
            "NO_SLOTS",
            f"У врача {doctor.full_name} нет свободного времени "
            + (f"на {day}" if day else f"в ближайшие {SEARCH_DAYS_AHEAD} дней"),
        )

    return tool_result(found)


async def book_appointment(
    db: AsyncSession,
    current_patient,
    doctor_id: int,
    patient_id: int,
    day: date,
    slot_time: time,
):
    if current_patient.id != patient_id:
        return tool_error(
            "PERMISSION_DENIED", "Записать можно только самого себя, не другого пациента"
        )

    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        return tool_error("DOCTOR_NOT_FOUND", "Врач не найден")

    if not is_future(day, slot_time):
        return tool_error("SLOT_IN_PAST", "Нельзя записаться на прошедшее время")

    if await crud_appointment.has_active_appointment(patient_id, doctor_id, day, db):
        return tool_error(
            "ALREADY_BOOKED", "У вас уже есть запись к этому врачу на этот день"
        )

    slot = await crud_schedule.find_slot(doctor_id, day, slot_time, db)

    if slot is None:
        return tool_error("SLOT_NOT_AVAILABLE", "Это время недоступно для записи")

    data = AppointmentCreateIn(doctor_id=doctor_id, date=day, time=slot_time)
    appointment = await crud_appointment.create_appointment(
        patient_id, slot["department_id"], data, db
    )

    if appointment is None:
        return tool_error("SLOT_TAKEN", "Это время только что заняли")

    department = await crud_department.get_by_id(appointment.department_id, db)

    return tool_result(
        {
            "appointment_id": appointment.id,
            "doctor_id": doctor.id,
            "doctor_name": doctor.full_name,
            "specialization": doctor.specialization,
            "department": department.name if department else None,
            "date": str(appointment.date),
            "time": str(appointment.time),
            "status": appointment.status,
        }
    )


async def get_own_appointment(db: AsyncSession, current_patient, appointment_id: int):
    appointment = await crud_appointment.get_by_id(appointment_id, db)

    if appointment is None or appointment.patient_id != current_patient.id:
        return None

    return appointment


async def cancel_appointment(db: AsyncSession, current_patient, appointment_id: int):
    appointment = await get_own_appointment(db, current_patient, appointment_id)

    if appointment is None:
        return tool_error("APPOINTMENT_NOT_FOUND", "Запись не найдена")

    if appointment.status != "booked":
        return tool_error("APPOINTMENT_NOT_ACTIVE", "Запись уже закрыта")

    await crud_appointment.set_status(appointment, "cancelled", db)

    return tool_result({"appointment_id": appointment.id, "status": "cancelled"})


async def reschedule_appointment(
    db: AsyncSession, current_patient, appointment_id: int, day: date, slot_time: time
):
    appointment = await get_own_appointment(db, current_patient, appointment_id)

    if appointment is None:
        return tool_error("APPOINTMENT_NOT_FOUND", "Запись не найдена")

    if appointment.status != "booked":
        return tool_error("APPOINTMENT_NOT_ACTIVE", "Запись уже закрыта")

    if not is_future(day, slot_time):
        return tool_error("SLOT_IN_PAST", "Нельзя записаться на прошедшее время")

    slot = await crud_schedule.find_slot(appointment.doctor_id, day, slot_time, db)

    if slot is None:
        return tool_error("SLOT_NOT_AVAILABLE", "Это время недоступно для записи")

    data = AppointmentRescheduleIn(date=day, time=slot_time)
    updated = await crud_appointment.reschedule_appointment(
        appointment, slot["department_id"], data, db
    )

    if updated is None:
        return tool_error("SLOT_TAKEN", "Это время только что заняли")

    return tool_result(
        {
            "appointment_id": updated.id,
            "date": str(updated.date),
            "time": str(updated.time),
            "status": updated.status,
        }
    )


async def get_patient_appointments(
    db: AsyncSession, current_patient, patient_id: int, status: str | None = None
):
    if current_patient.id != patient_id:
        return tool_error(
            "PERMISSION_DENIED", "Смотреть можно только свои записи, не чужие"
        )

    appointments = await crud_appointment.get_patient_appointments(patient_id, db, status)

    return tool_result(
        [
            {
                "appointment_id": appointment.id,
                "doctor_id": appointment.doctor_id,
                "department_id": appointment.department_id,
                "date": str(appointment.date),
                "time": str(appointment.time),
                "status": appointment.status,
            }
            for appointment in appointments
        ]
    )


async def get_doctor_schedule(db: AsyncSession, doctor_id: int):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        return tool_error("DOCTOR_NOT_FOUND", "Врач не найден")

    schedules = await crud_schedule.get_schedules(doctor_id, db)

    if not schedules:
        return tool_error("NO_SCHEDULE", f"У врача {doctor.full_name} ещё нет расписания")

    return tool_result(
        [
            {
                "weekday": schedule.weekday,
                "department_id": schedule.department_id,
                "start_time": str(schedule.start_time),
                "end_time": str(schedule.end_time),
                "slot_duration": schedule.slot_duration,
            }
            for schedule in schedules
        ]
    )
