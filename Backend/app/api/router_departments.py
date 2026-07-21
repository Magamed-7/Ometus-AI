from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.db.database import get_db
from app.schemas.schema_department import DepartmentOut
from app.services import crud_department

departments_router = APIRouter(prefix="/api/departments", tags=["Departments"])


@departments_router.get("", response_model=list[DepartmentOut])
async def get_departments(filial_id: int | None = None, db: AsyncSession = Depends(get_db)):
    return await crud_department.get_departments(db, filial_id)


@departments_router.get("/{department_id}", response_model=DepartmentOut)
async def get_department(department_id: int, db: AsyncSession = Depends(get_db)):
    department = await crud_department.get_by_id(department_id, db)

    if department is None:
        raise AppError(
            code="DEPARTMENT_NOT_FOUND", message="Отделение не найдено", status_code=404
        )

    return department
