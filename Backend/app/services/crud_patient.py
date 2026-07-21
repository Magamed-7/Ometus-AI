from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_patient import Patient
from app.models.model_user import User
from app.schemas.schema_patient import PatientUpdateIn


async def create_patient(user: User, db: AsyncSession):
    full_name = " ".join(part for part in [user.first_name, user.last_name] if part)

    patient = Patient(
        user_id=user.id,
        full_name=full_name or None,
        phone=user.phone,
    )

    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


async def get_by_id(patient_id: int, db: AsyncSession):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    return result.scalar_one_or_none()


async def get_by_user_id(user_id: int, db: AsyncSession):
    result = await db.execute(select(Patient).where(Patient.user_id == user_id))
    return result.scalar_one_or_none()


async def update_patient(patient: Patient, data: PatientUpdateIn, db: AsyncSession):
    patient.full_name = data.full_name or patient.full_name
    patient.date_of_birth = data.date_of_birth or patient.date_of_birth
    patient.phone = data.phone or patient.phone

    await db.commit()
    await db.refresh(patient)
    return patient
