from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.permissions import require_role
from app.core.errors import AppError
from app.db.database import get_db
from app.schemas.schema_department import (
    DepartmentCreateIn,
    DepartmentOut,
    DepartmentUpdateIn,
)
from app.schemas.schema_filial import FilialCreateIn, FilialOut, FilialUpdateIn
from app.services import crud_department, crud_filial

admin_router = APIRouter(prefix="/api/admin", tags=["Admin"])


@admin_router.post("/filials", response_model=FilialOut)
async def create_filial(
    data: FilialCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    return await crud_filial.create_filial(data, db)


@admin_router.put("/filials/{filial_id}", response_model=FilialOut)
async def update_filial(
    filial_id: int,
    data: FilialUpdateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    filial = await crud_filial.get_by_id(filial_id, db)

    if filial is None:
        raise AppError(code="FILIAL_NOT_FOUND", message="Филиал не найден", status_code=404)

    return await crud_filial.update_filial(filial, data, db)


@admin_router.delete("/filials/{filial_id}")
async def delete_filial(
    filial_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    filial = await crud_filial.get_by_id(filial_id, db)

    if filial is None:
        raise AppError(code="FILIAL_NOT_FOUND", message="Филиал не найден", status_code=404)

    await crud_filial.delete_filial(filial, db)
    return {"message": "Филиал удалён"}


@admin_router.post("/departments", response_model=DepartmentOut)
async def create_department(
    data: DepartmentCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    filial = await crud_filial.get_by_id(data.filial_id, db)

    if filial is None:
        raise AppError(code="FILIAL_NOT_FOUND", message="Филиал не найден", status_code=404)

    return await crud_department.create_department(data, db)


@admin_router.put("/departments/{department_id}", response_model=DepartmentOut)
async def update_department(
    department_id: int,
    data: DepartmentUpdateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    department = await crud_department.get_by_id(department_id, db)

    if department is None:
        raise AppError(
            code="DEPARTMENT_NOT_FOUND", message="Отделение не найдено", status_code=404
        )

    return await crud_department.update_department(department, data, db)


@admin_router.delete("/departments/{department_id}")
async def delete_department(
    department_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    department = await crud_department.get_by_id(department_id, db)

    if department is None:
        raise AppError(
            code="DEPARTMENT_NOT_FOUND", message="Отделение не найдено", status_code=404
        )

    await crud_department.delete_department(department, db)
    return {"message": "Отделение удалено"}
