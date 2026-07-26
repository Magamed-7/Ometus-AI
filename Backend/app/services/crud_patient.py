from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_appointment import Appointment
from app.models.model_patient import Patient
from app.models.model_user import User
from app.schemas.schema_patient import DependentCreateIn, DependentUpdateIn, PatientUpdateIn

# папа, мама, бабушка, дедушка, старший брат или сестра — больше одному аккаунту не нужно,
# а без потолка один пользователь может наплодить тысячу валидных patient_id для записи
DEPENDENTS_LIMIT = 5


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


async def create_dependent(guardian: User, data: DependentCreateIn, db: AsyncSession):
    patient = Patient(
        user_id=None,
        guardian_user_id=guardian.id,
        full_name=data.full_name,
        date_of_birth=data.date_of_birth,
        phone=data.phone,
    )

    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


async def count_dependents(guardian_user_id: int, db: AsyncSession):
    result = await db.execute(
        select(func.count())
        .select_from(Patient)
        .where(Patient.guardian_user_id == guardian_user_id)
    )
    return result.scalar_one()


async def get_dependent(dependent_id: int, guardian_user_id: int, db: AsyncSession):
    result = await db.execute(
        select(Patient)
        .where(Patient.id == dependent_id)
        .where(Patient.guardian_user_id == guardian_user_id)
    )
    return result.scalar_one_or_none()


async def update_dependent(patient: Patient, data: DependentUpdateIn, db: AsyncSession):
    patient.full_name = data.full_name or patient.full_name
    patient.date_of_birth = data.date_of_birth or patient.date_of_birth
    patient.phone = data.phone or patient.phone

    await db.commit()
    await db.refresh(patient)
    return patient


async def delete_dependent(patient: Patient, db: AsyncSession):
    await db.delete(patient)
    await db.commit()


async def has_appointments(patient_id: int, db: AsyncSession):
    result = await db.execute(
        select(func.count()).select_from(Appointment).where(Appointment.patient_id == patient_id)
    )
    return result.scalar_one() > 0


async def get_dependents(guardian_user_id: int, db: AsyncSession):
    result = await db.execute(
        select(Patient)
        .where(Patient.guardian_user_id == guardian_user_id)
        .order_by(Patient.id)
    )
    return result.scalars().all()


async def is_bookable_by(patient_id: int, user_id: int, db: AsyncSession):
    patient = await get_by_id(patient_id, db)

    if patient is None:
        return False

    return patient.user_id == user_id or patient.guardian_user_id == user_id


async def get_contact(patient_id: int, db: AsyncSession):
    # у карточки родственника своего аккаунта нет, писать некому — значит пишем опекуну,
    # он эту запись и создавал
    patient = await get_by_id(patient_id, db)

    if patient is None:
        return None, None

    owner_id = patient.user_id or patient.guardian_user_id

    if owner_id is None:
        return None, patient.full_name

    user = await db.get(User, owner_id)

    if user is None:
        return None, patient.full_name

    return user.email, patient.full_name
