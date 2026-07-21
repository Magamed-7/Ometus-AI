from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.db.database import get_db
from app.schemas.schema_filial import FilialOut
from app.services import crud_filial

filials_router = APIRouter(prefix="/api/filials", tags=["Filials"])


@filials_router.get("", response_model=list[FilialOut])
async def get_filials(city: str | None = None, db: AsyncSession = Depends(get_db)):
    return await crud_filial.get_filials(db, city)


@filials_router.get("/{filial_id}", response_model=FilialOut)
async def get_filial(filial_id: int, db: AsyncSession = Depends(get_db)):
    filial = await crud_filial.get_by_id(filial_id, db)

    if filial is None:
        raise AppError(code="FILIAL_NOT_FOUND", message="Филиал не найден", status_code=404)

    return filial
