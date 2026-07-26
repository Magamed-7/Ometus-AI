import secrets
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import clinic_today
from app.core.security import hash_password
from app.models.model_appointment import Appointment
from app.models.model_department import Department
from app.models.model_doctor import Doctor
from app.models.model_doctor_department import DoctorDepartment
from app.models.model_doctor_specialization import DoctorSpecialization
from app.models.model_filial import Filial
from app.models.model_user import User
from app.schemas.schema_doctor import DoctorCreateIn, DoctorUpdateIn


def generate_password(length: int = 20) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def split_full_name(full_name: str):
    # «Иванова Мария Петровна» → first_name «Мария Петровна», last_name «Иванова».
    # ФИО целиком в first_name разъезжается с карточкой врача с первой же секунды:
    # в users одно имя, в doctors другое, и в профиле врач видит бессмыслицу
    parts = full_name.split()

    if not parts:
        return None, None

    if len(parts) == 1:
        return parts[0], None

    return " ".join(parts[1:]), parts[0]


async def create_doctor(data: DoctorCreateIn, db: AsyncSession):
    password = data.password or generate_password()
    first_name, last_name = split_full_name(data.full_name)

    user = User(
        email=data.email,
        hashed_password=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        phone=data.phone,
        role="doctor",
        is_verified=True,
    )

    db.add(user)
    await db.flush()

    doctor = Doctor(
        user_id=user.id,
        full_name=data.full_name,
        specialization=data.specialization,
    )

    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)

    doctor.password = password
    return doctor


async def get_by_id(doctor_id: int, db: AsyncSession):
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    return result.scalar_one_or_none()


async def get_by_user_id(user_id: int, db: AsyncSession):
    result = await db.execute(select(Doctor).where(Doctor.user_id == user_id))
    return result.scalar_one_or_none()


async def search_doctors(
    db: AsyncSession,
    specialization: str | None = None,
    department_id: int | None = None,
    filial_id: int | None = None,
    city: str | None = None,
):
    # уволенный врач исчезает из поиска с даты увольнения; до неё к нему ещё можно попасть
    query = select(Doctor).where(
        or_(Doctor.dismissed_at.is_(None), Doctor.dismissed_at > clinic_today())
    )

    if specialization:
        query = query.outerjoin(
            DoctorSpecialization, DoctorSpecialization.doctor_id == Doctor.id
        ).where(
            or_(
                Doctor.specialization.ilike(f"%{specialization}%"),
                DoctorSpecialization.name.ilike(f"%{specialization}%"),
            )
        )

    if department_id or filial_id or city:
        query = query.join(DoctorDepartment, DoctorDepartment.doctor_id == Doctor.id)

    if department_id:
        query = query.where(DoctorDepartment.department_id == department_id)

    if filial_id or city:
        query = query.join(Department, Department.id == DoctorDepartment.department_id)

    if filial_id:
        query = query.where(Department.filial_id == filial_id)

    if city:
        query = query.join(Filial, Filial.id == Department.filial_id).where(
            Filial.city.ilike(city.strip())
        )

    result = await db.execute(query.distinct().order_by(Doctor.id))
    return result.scalars().all()


async def update_doctor(doctor: Doctor, data: DoctorUpdateIn, db: AsyncSession):
    doctor.full_name = data.full_name or doctor.full_name
    doctor.specialization = data.specialization or doctor.specialization

    # ФИО правится в одном месте, но лежит в двух таблицах — держим их вместе
    if data.full_name:
        user = await db.get(User, doctor.user_id)

        if user is not None:
            user.first_name, user.last_name = split_full_name(data.full_name)

    await db.commit()
    await db.refresh(doctor)
    return doctor


async def get_departments(doctor_id: int, db: AsyncSession):
    result = await db.execute(
        select(Department)
        .join(DoctorDepartment, DoctorDepartment.department_id == Department.id)
        .where(DoctorDepartment.doctor_id == doctor_id)
        .order_by(Department.id)
    )
    return result.scalars().all()


async def assign_department(doctor_id: int, department_id: int, db: AsyncSession):
    result = await db.execute(
        select(DoctorDepartment)
        .where(DoctorDepartment.doctor_id == doctor_id)
        .where(DoctorDepartment.department_id == department_id)
    )

    if result.scalar_one_or_none():
        return None

    assignment = DoctorDepartment(doctor_id=doctor_id, department_id=department_id)
    db.add(assignment)
    await db.commit()
    return assignment


async def remove_department(doctor_id: int, department_id: int, db: AsyncSession):
    result = await db.execute(
        select(DoctorDepartment)
        .where(DoctorDepartment.doctor_id == doctor_id)
        .where(DoctorDepartment.department_id == department_id)
    )
    assignment = result.scalar_one_or_none()

    if assignment is None:
        return None

    await db.delete(assignment)
    await db.commit()
    return assignment


async def get_specializations(doctor_id: int, db: AsyncSession):
    result = await db.execute(
        select(DoctorSpecialization)
        .where(DoctorSpecialization.doctor_id == doctor_id)
        .order_by(DoctorSpecialization.id)
    )
    return result.scalars().all()


async def add_specialization(doctor_id: int, name: str, db: AsyncSession):
    result = await db.execute(
        select(DoctorSpecialization)
        .where(DoctorSpecialization.doctor_id == doctor_id)
        # регистр не важен: «Кардиолог» и «кардиолог» — одна специализация,
        # а в remove имя ещё и приезжает из пути URL в процентной кодировке
        .where(func.lower(DoctorSpecialization.name) == name.strip().lower())
    )

    if result.scalar_one_or_none():
        return None

    specialization = DoctorSpecialization(doctor_id=doctor_id, name=name)
    db.add(specialization)
    await db.commit()
    await db.refresh(specialization)
    return specialization


async def remove_specialization(doctor_id: int, name: str, db: AsyncSession):
    result = await db.execute(
        select(DoctorSpecialization)
        .where(DoctorSpecialization.doctor_id == doctor_id)
        # регистр не важен: «Кардиолог» и «кардиолог» — одна специализация,
        # а в remove имя ещё и приезжает из пути URL в процентной кодировке
        .where(func.lower(DoctorSpecialization.name) == name.strip().lower())
    )
    specialization = result.scalar_one_or_none()

    if specialization is None:
        return None

    await db.delete(specialization)
    await db.commit()
    return specialization


async def count_upcoming_appointments(doctor_id: int, since: date, db: AsyncSession):
    # активные записи после даты увольнения — именно о них надо предупредить админа
    result = await db.execute(
        select(func.count())
        .select_from(Appointment)
        .where(Appointment.doctor_id == doctor_id)
        .where(Appointment.date >= since)
        .where(Appointment.status == "booked")
    )
    return result.scalar_one()


async def dismiss_doctor(doctor: Doctor, dismissed_at: date, db: AsyncSession):
    doctor.dismissed_at = dismissed_at

    await db.commit()
    await db.refresh(doctor)
    return doctor


async def restore_doctor(doctor: Doctor, db: AsyncSession):
    doctor.dismissed_at = None

    await db.commit()
    await db.refresh(doctor)
    return doctor


def is_dismissed_on(doctor: Doctor, day: date):
    return doctor.dismissed_at is not None and day >= doctor.dismissed_at
