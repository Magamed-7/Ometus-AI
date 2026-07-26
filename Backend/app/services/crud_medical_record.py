from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_medical_record import PatientMedicalRecord
from app.models.model_patient import Patient
from app.schemas.schema_medical_record import MedicalRecordCreateIn


async def create_record(patient_id: int, data: MedicalRecordCreateIn, db: AsyncSession):
    record = PatientMedicalRecord(
        patient_id=patient_id,
        kind=data.kind,
        name=data.name,
        note=data.note,
    )

    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_records(patient_id: int, db: AsyncSession):
    result = await db.execute(
        select(PatientMedicalRecord)
        .where(PatientMedicalRecord.patient_id == patient_id)
        .order_by(PatientMedicalRecord.kind, PatientMedicalRecord.id)
    )
    return result.scalars().all()


async def get_by_id(record_id: int, db: AsyncSession):
    result = await db.execute(
        select(PatientMedicalRecord).where(PatientMedicalRecord.id == record_id)
    )
    return result.scalar_one_or_none()


async def delete_record(record: PatientMedicalRecord, db: AsyncSession):
    await db.delete(record)
    await db.commit()


async def set_consent(patient: Patient, allowed: bool, db: AsyncSession):
    patient.ai_consent = allowed

    await db.commit()
    await db.refresh(patient)
    return patient
