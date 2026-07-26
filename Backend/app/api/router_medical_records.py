from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.permissions import get_current_patient
from app.core.errors import AppError
from app.db.database import get_db
from app.schemas.schema_medical_record import (
    AiConsentIn,
    AiConsentOut,
    MedicalRecordCreateIn,
    MedicalRecordOut,
)
from app.services import crud_medical_record

medical_records_router = APIRouter(prefix="/api/patients/me", tags=["Medical records"])


@medical_records_router.get("/medical-records", response_model=list[MedicalRecordOut])
async def list_my_records(
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    return await crud_medical_record.get_records(patient.id, db)


@medical_records_router.post("/medical-records", response_model=MedicalRecordOut)
async def add_my_record(
    data: MedicalRecordCreateIn,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    return await crud_medical_record.create_record(patient.id, data, db)


@medical_records_router.delete("/medical-records/{record_id}")
async def delete_my_record(
    record_id: int,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    record = await crud_medical_record.get_by_id(record_id, db)

    if record is None or record.patient_id != patient.id:
        raise AppError(code="RECORD_NOT_FOUND", message="Запись не найдена", status_code=404)

    await crud_medical_record.delete_record(record, db)
    return {"message": "Запись удалена"}


@medical_records_router.get("/ai-consent", response_model=AiConsentOut)
async def get_my_consent(patient=Depends(get_current_patient)):
    return {"ai_consent": patient.ai_consent}


@medical_records_router.put("/ai-consent", response_model=AiConsentOut)
async def set_my_consent(
    data: AiConsentIn,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    updated = await crud_medical_record.set_consent(patient, data.allowed, db)
    return {"ai_consent": updated.ai_consent}
