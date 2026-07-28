from datetime import date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import clinic_now
from app.schemas.schema_appointment import AppointmentCreateIn, AppointmentRescheduleIn
from app.services import (
    crud_appointment,
    crud_department,
    crud_doctor,
    crud_patient,
    crud_schedule,
)

SEARCH_DAYS_AHEAD = 14

# Паспорта инструментов. Раньше модель выбирала намерение по короткому списку слов
# и не знала ни что делает инструмент, ни какие у него параметры, ни когда его звать
# нельзя — отсюда и «покажи время у Марии Андреевны» в виде списка неврологов.
# Описания уходят в промпт классификатора и написаны для модели: что делает, что нужно
# на входе, когда выбирать и чего не делать.
TOOLS = [
    {
        "name": "find_doctors",
        "intent": "find_doctor",
        "description": "Find a doctor by specialty or by what the patient complains about. "
        "Pick this when the patient names a specialty ('I need a cardiologist'), "
        "describes a symptom ('my throat hurts'), or asks to book without naming a doctor.",
        "parameters": {
            "specialization": "specialty name, only if the patient stated it",
            "city": "branch city, if the patient named one",
        },
        "never": "Do not pick this when the patient named a specific doctor, "
        "or when the request is about an appointment that already exists.",
    },
    {
        "name": "get_open_days",
        "intent": "open_days",
        "description": "List the days on which a known doctor still has free time. "
        "Pick this when the doctor is known but the patient has not named a day.",
        "parameters": {"doctor_id": "doctor identifier"},
        "never": "Never choose a day yourself. With no date from the patient, ask which day "
        "instead of showing the nearest one.",
    },
    {
        "name": "get_available_time",
        "intent": "slots",
        "description": "Show a doctor's free hours on one specific day. "
        "Pick this only when both the doctor and the day are known.",
        "parameters": {
            "doctor_id": "doctor identifier",
            "date": "date as YYYY-MM-DD",
        },
        "never": "Do not pick this without a date — use get_open_days for that.",
    },
    {
        "name": "book_appointment",
        "intent": "book",
        "description": "Book the appointment. "
        "Pick this only after the patient has confirmed the doctor, the date and the time.",
        "parameters": {
            "doctor_id": "doctor identifier",
            "date": "date as YYYY-MM-DD",
            "time": "time as HH:MM",
        },
        "never": "Never book without an explicit confirmation from the patient.",
    },
    {
        "name": "cancel_appointment",
        "intent": "cancel",
        "description": "Cancel the patient's appointment. Pick this when asked to cancel a visit.",
        "parameters": {"appointment_id": "appointment number, if the patient gave one"},
        "never": "Never cancel someone else's appointment, and do not confuse cancelling "
        "with rescheduling.",
    },
    {
        "name": "reschedule_appointment",
        "intent": "reschedule",
        "description": "Move an existing appointment to another date or time. "
        "Pick this when the patient asks to move a visit rather than drop it.",
        "parameters": {
            "appointment_id": "appointment number, if named",
            "date": "new date as YYYY-MM-DD",
            "time": "new time as HH:MM",
        },
        "never": "Do not reschedule when the patient asks to cancel.",
    },
    {
        "name": "get_patient_appointments",
        "intent": "my_appointments",
        "description": "Show the patient their own appointments. "
        "Pick this for 'my appointments', 'when am I booked', 'show my visits'.",
        "parameters": {},
        "never": "Never show appointments belonging to anyone else.",
    },
    {
        "name": "get_doctor_schedule",
        "intent": "doctor_schedule",
        "description": "Show a doctor's working schedule — which weekdays they see patients. "
        "Pick this for 'when does the doctor work', 'what are their hours'.",
        "parameters": {"doctor_id": "doctor identifier"},
        "never": "Do not confuse this with get_available_time: this is the weekly grid, "
        "not the free hours on a date.",
    },
]


def describe_tools(intents=None):
    lines = []

    for tool in TOOLS:
        if intents is not None and tool["intent"] not in intents:
            continue

        parameters = ", ".join(f"{name} — {hint}" for name, hint in tool["parameters"].items())
        line = f"{tool['intent']} ({tool['name']}): {tool['description']}"

        if parameters:
            line += f" Parameters: {parameters}."

        lines.append(f"{line} {tool['never']}")

    return "\n".join(lines)


def tool_error(code: str, message: str):
    return {"ok": False, "error": {"code": code, "message": message}}


def tool_result(data):
    return {"ok": True, "data": data}


def is_future(day: date, slot_time: time):
    return datetime.combine(day, slot_time) >= clinic_now()


async def find_doctors(
    db: AsyncSession,
    specialization: str | None = None,
    department: str | None = None,
    city: str | None = None,
):
    department_id = None

    if department:
        departments = await crud_department.get_departments(db)
        matched = [item for item in departments if department.lower() in item.name.lower()]

        if not matched:
            return tool_error(
                "DEPARTMENT_NOT_FOUND", f"Отделение «{department}» не найдено"
            )

        exact = [item for item in matched if item.name.lower() == department.lower()]

        if len(matched) > 1 and len(exact) != 1:
            return tool_error(
                "DEPARTMENT_AMBIGUOUS",
                "Уточните отделение: подходит несколько — "
                + ", ".join(f"{item.name} (#{item.id})" for item in matched),
            )

        department_id = (exact or matched)[0].id

    doctors = await crud_doctor.search_doctors(db, specialization, department_id, city=city)
    other_city = False

    if not doctors and city:
        doctors = await crud_doctor.search_doctors(db, specialization, department_id)
        other_city = bool(doctors)

    if not doctors:
        return tool_error("DOCTORS_NOT_FOUND", "Подходящих врачей не нашлось")

    return tool_result(
        [
            {
                "doctor_id": doctor.id,
                "full_name": doctor.full_name,
                "specialization": doctor.specialization,
                "photo_url": doctor.photo_url,
                "other_city": other_city,
            }
            for doctor in doctors
        ]
    )


async def get_available_time(db: AsyncSession, doctor_id: int, day: date | None = None):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        return tool_error("DOCTOR_NOT_FOUND", "Врач не найден")

    if day:
        days = [day]
    else:
        today = clinic_now().date()
        days = [today + timedelta(days=shift) for shift in range(SEARCH_DAYS_AHEAD)]

    found = []
    workdays = {schedule.weekday for schedule in await crud_schedule.get_schedules(doctor_id, db)}

    for current in days:
        if not day and current.weekday() not in workdays:
            continue

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


async def get_open_days(db: AsyncSession, doctor_id: int, limit: int = 7):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        return tool_error("DOCTOR_NOT_FOUND", "Врач не найден")

    today = clinic_now().date()
    found = []

    for shift in range(SEARCH_DAYS_AHEAD * 2):
        current = today + timedelta(days=shift)
        slots = [
            slot
            for slot in await crud_schedule.get_available_slots(doctor_id, current, db)
            if is_future(current, slot["time"])
        ]

        if slots:
            found.append({"date": str(current), "slots_free": len(slots)})

        if len(found) >= limit:
            break

    if not found:
        return tool_error(
            "NO_SLOTS",
            f"У врача {doctor.full_name} нет свободного времени "
            f"в ближайшие {SEARCH_DAYS_AHEAD * 2} дней",
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
    if current_patient.id != patient_id and not await crud_patient.is_bookable_by(
        patient_id, current_patient.user_id, db
    ):
        return tool_error(
            "PERMISSION_DENIED", "Записать можно только себя или своего родственника"
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
