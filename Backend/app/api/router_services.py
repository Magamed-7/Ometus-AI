from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.db.database import get_db
from app.schemas.schema_service import ServiceOut
from app.services import crud_service

services_router = APIRouter(prefix="/api/services", tags=["Services"])


@services_router.get("", response_model=list[ServiceOut])
async def get_services(
    category: str | None = None,
    department_id: int | None = None,
    filial_id: int | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await crud_service.list_services(db, category, department_id, filial_id, search)


@services_router.get("/{service_id}", response_model=ServiceOut)
async def get_service(service_id: int, db: AsyncSession = Depends(get_db)):
    service = await crud_service.get_by_id(service_id, db)

    if service is None or not service.is_active:
        raise AppError(code="SERVICE_NOT_FOUND", message="Услуга не найдена", status_code=404)

    return service
