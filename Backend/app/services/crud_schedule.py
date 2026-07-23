from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_absence import DoctorAbsence
from app.models.model_date_schedule import DoctorDateSchedule
from app.models.model_schedule import DoctorSchedule
from app.schemas.schema_schedule import (
    AbsenceCreateIn,
    DateScheduleCreateIn,
    ScheduleCreateIn,
    ScheduleUpdateIn,
)
from app.services import crud_appointment


async def create_schedule(doctor_id: int, data: ScheduleCreateIn, db: AsyncSession):
    schedule = DoctorSchedule(
        doctor_id=doctor_id,
        department_id=data.department_id,
        weekday=data.weekday,
        start_time=data.start_time,
        end_time=data.end_time,
        slot_duration=data.slot_duration,
        buffer_duration=data.buffer_duration,
    )

    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def get_schedules(doctor_id: int, db: AsyncSession):
    result = await db.execute(
        select(DoctorSchedule)
        .where(DoctorSchedule.doctor_id == doctor_id)
        .order_by(DoctorSchedule.weekday, DoctorSchedule.start_time)
    )
    return result.scalars().all()


async def get_schedule_by_id(schedule_id: int, db: AsyncSession):
    result = await db.execute(select(DoctorSchedule).where(DoctorSchedule.id == schedule_id))
    return result.scalar_one_or_none()


async def get_schedule_by_weekday(doctor_id: int, weekday: int, db: AsyncSession):
    result = await db.execute(
        select(DoctorSchedule)
        .where(DoctorSchedule.doctor_id == doctor_id)
        .where(DoctorSchedule.weekday == weekday)
        .order_by(DoctorSchedule.start_time)
    )
    return result.scalars().all()


async def update_schedule(schedule: DoctorSchedule, data: ScheduleUpdateIn, db: AsyncSession):
    schedule.department_id = data.department_id or schedule.department_id
    schedule.weekday = schedule.weekday if data.weekday is None else data.weekday
    schedule.start_time = data.start_time or schedule.start_time
    schedule.end_time = data.end_time or schedule.end_time
    schedule.slot_duration = data.slot_duration or schedule.slot_duration
    schedule.buffer_duration = (
        schedule.buffer_duration if data.buffer_duration is None else data.buffer_duration
    )

    await db.commit()
    await db.refresh(schedule)
    return schedule


async def delete_schedule(schedule: DoctorSchedule, db: AsyncSession):
    await db.delete(schedule)
    await db.commit()


async def create_absence(doctor_id: int, data: AbsenceCreateIn, db: AsyncSession):
    absence = DoctorAbsence(
        doctor_id=doctor_id,
        date_from=data.date_from,
        date_to=data.date_to,
        reason=data.reason,
    )

    db.add(absence)
    await db.commit()
    await db.refresh(absence)
    return absence


async def get_absences(doctor_id: int, db: AsyncSession):
    result = await db.execute(
        select(DoctorAbsence)
        .where(DoctorAbsence.doctor_id == doctor_id)
        .order_by(DoctorAbsence.date_from)
    )
    return result.scalars().all()


async def get_absence_by_id(absence_id: int, db: AsyncSession):
    result = await db.execute(select(DoctorAbsence).where(DoctorAbsence.id == absence_id))
    return result.scalar_one_or_none()


async def delete_absence(absence: DoctorAbsence, db: AsyncSession):
    await db.delete(absence)
    await db.commit()


async def create_date_schedule(doctor_id: int, data: DateScheduleCreateIn, db: AsyncSession):
    schedule = DoctorDateSchedule(
        doctor_id=doctor_id,
        department_id=data.department_id,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        slot_duration=data.slot_duration,
        buffer_duration=data.buffer_duration,
    )

    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def get_date_schedules(doctor_id: int, db: AsyncSession):
    result = await db.execute(
        select(DoctorDateSchedule)
        .where(DoctorDateSchedule.doctor_id == doctor_id)
        .order_by(DoctorDateSchedule.date, DoctorDateSchedule.start_time)
    )
    return result.scalars().all()


async def get_date_schedules_on(doctor_id: int, day: date, db: AsyncSession):
    result = await db.execute(
        select(DoctorDateSchedule)
        .where(DoctorDateSchedule.doctor_id == doctor_id)
        .where(DoctorDateSchedule.date == day)
        .order_by(DoctorDateSchedule.start_time)
    )
    return result.scalars().all()


async def get_date_schedule_by_id(schedule_id: int, db: AsyncSession):
    result = await db.execute(
        select(DoctorDateSchedule).where(DoctorDateSchedule.id == schedule_id)
    )
    return result.scalar_one_or_none()


async def delete_date_schedule(schedule: DoctorDateSchedule, db: AsyncSession):
    await db.delete(schedule)
    await db.commit()


async def is_absent(doctor_id: int, day: date, db: AsyncSession):
    result = await db.execute(
        select(DoctorAbsence)
        .where(DoctorAbsence.doctor_id == doctor_id)
        .where(DoctorAbsence.date_from <= day)
        .where(DoctorAbsence.date_to >= day)
    )
    return result.scalars().first() is not None


def slice_slots(day: date, schedules, taken):
    slots = []

    for schedule in schedules:
        current = datetime.combine(day, schedule.start_time)
        end = datetime.combine(day, schedule.end_time)
        length = timedelta(minutes=schedule.slot_duration)
        stride = timedelta(minutes=schedule.slot_duration + schedule.buffer_duration)

        while current + length <= end:
            if current.time() not in taken:
                slots.append(
                    {
                        "date": day,
                        "time": current.time(),
                        "department_id": schedule.department_id,
                    }
                )
            current = current + stride

    return slots


async def get_available_slots(doctor_id: int, day: date, db: AsyncSession):
    if await is_absent(doctor_id, day, db):
        return []

    overrides = await get_date_schedules_on(doctor_id, day, db)
    schedules = overrides or await get_schedule_by_weekday(doctor_id, day.weekday(), db)
    taken = await crud_appointment.get_taken_times(doctor_id, day, db)
    return slice_slots(day, schedules, taken)


async def find_slot(doctor_id: int, day: date, slot_time: time, db: AsyncSession):
    slots = await get_available_slots(doctor_id, day, db)

    for slot in slots:
        if slot["time"] == slot_time:
            return slot

    return None
