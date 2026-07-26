from datetime import date

from sqlalchemy import and_, case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_appointment import Appointment
from app.models.model_doctor import Doctor
from app.models.model_doctor_department import DoctorDepartment


def status_count(status: str):
    return func.count(case((Appointment.status == status, Appointment.id)))


async def get_doctor_workload(
    db: AsyncSession,
    date_from: date,
    date_to: date,
    department_id: int | None = None,
):
    query = (
        select(
            Doctor.id,
            Doctor.full_name,
            Doctor.specialization,
            func.count(Appointment.id),
            status_count("booked"),
            status_count("completed"),
            status_count("cancelled"),
            status_count("no_show"),
        )
        .outerjoin(
            Appointment,
            and_(
                Appointment.doctor_id == Doctor.id,
                Appointment.date >= date_from,
                Appointment.date <= date_to,
            ),
        )
        .group_by(Doctor.id, Doctor.full_name, Doctor.specialization)
        .order_by(Doctor.id)
    )

    if department_id:
        # join именно к doctor_departments, а не к записям: врачи отделения, у которых
        # за период не было ни одной записи, обязаны попасть в отчёт с нулями —
        # иначе не видно, кто простаивает. Закреплено тестом
        query = query.join(DoctorDepartment, DoctorDepartment.doctor_id == Doctor.id).where(
            DoctorDepartment.department_id == department_id
        )

    result = await db.execute(query)

    return [
        {
            "doctor_id": row[0],
            "full_name": row[1],
            "specialization": row[2],
            "total": row[3],
            "booked": row[4],
            "completed": row[5],
            "cancelled": row[6],
            "no_show": row[7],
        }
        for row in result.all()
    ]


async def get_appointments_summary(db: AsyncSession, date_from: date, date_to: date):
    result = await db.execute(
        select(
            func.count(Appointment.id),
            status_count("booked"),
            status_count("completed"),
            status_count("cancelled"),
            status_count("no_show"),
            func.count(distinct(Appointment.doctor_id)),
            func.count(distinct(Appointment.patient_id)),
        )
        .where(Appointment.date >= date_from)
        .where(Appointment.date <= date_to)
    )
    row = result.one()

    # «задействовано врачей» считается по записям, а отчёт по загрузке перечисляет всех,
    # включая нулевых — числа расходились и выглядели как ошибка. Добавляем знаменатель:
    # сколько врачей вообще работает, чтобы «7 из 31» читалось однозначно
    total_doctors = await db.execute(
        select(func.count()).select_from(Doctor).where(Doctor.dismissed_at.is_(None))
    )

    return {
        "date_from": date_from,
        "date_to": date_to,
        "total": row[0],
        "booked": row[1],
        "completed": row[2],
        "cancelled": row[3],
        "no_show": row[4],
        "doctors": row[5],
        "doctors_total": total_doctors.scalar_one(),
        "patients": row[6],
    }
