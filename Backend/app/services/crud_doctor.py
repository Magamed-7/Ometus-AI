from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.model_department import Department
from app.models.model_doctor import Doctor
from app.models.model_doctor_department import DoctorDepartment
from app.models.model_doctor_specialization import DoctorSpecialization
from app.models.model_user import User
from app.schemas.schema_doctor import DoctorCreateIn, DoctorUpdateIn


async def create_doctor(data: DoctorCreateIn, db: AsyncSession):
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        first_name=data.full_name,
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
):
    query = select(Doctor)

    if specialization:
        query = query.outerjoin(
            DoctorSpecialization, DoctorSpecialization.doctor_id == Doctor.id
        ).where(
            or_(
                Doctor.specialization.ilike(f"%{specialization}%"),
                DoctorSpecialization.name.ilike(f"%{specialization}%"),
            )
        )

    if department_id or filial_id:
        query = query.join(DoctorDepartment, DoctorDepartment.doctor_id == Doctor.id)

    if department_id:
        query = query.where(DoctorDepartment.department_id == department_id)

    if filial_id:
        query = query.join(Department, Department.id == DoctorDepartment.department_id).where(
            Department.filial_id == filial_id
        )

    result = await db.execute(query.distinct().order_by(Doctor.id))
    return result.scalars().all()


async def update_doctor(doctor: Doctor, data: DoctorUpdateIn, db: AsyncSession):
    doctor.full_name = data.full_name or doctor.full_name
    doctor.specialization = data.specialization or doctor.specialization

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
        .where(DoctorSpecialization.name == name)
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
        .where(DoctorSpecialization.name == name)
    )
    specialization = result.scalar_one_or_none()

    if specialization is None:
        return None

    await db.delete(specialization)
    await db.commit()
    return specialization
