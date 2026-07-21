from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_department import Department
from app.schemas.schema_department import DepartmentCreateIn, DepartmentUpdateIn


async def create_department(data: DepartmentCreateIn, db: AsyncSession):
    department = Department(
        filial_id=data.filial_id,
        name=data.name,
        description=data.description,
    )

    db.add(department)
    await db.commit()
    await db.refresh(department)
    return department


async def get_departments(db: AsyncSession, filial_id: int | None = None):
    query = select(Department)

    if filial_id:
        query = query.where(Department.filial_id == filial_id)

    result = await db.execute(query.order_by(Department.id))
    return result.scalars().all()


async def get_by_id(department_id: int, db: AsyncSession):
    result = await db.execute(select(Department).where(Department.id == department_id))
    return result.scalar_one_or_none()


async def update_department(department: Department, data: DepartmentUpdateIn, db: AsyncSession):
    department.filial_id = data.filial_id or department.filial_id
    department.name = data.name or department.name
    department.description = data.description or department.description

    await db.commit()
    await db.refresh(department)
    return department


async def delete_department(department: Department, db: AsyncSession):
    await db.delete(department)
    await db.commit()
