from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_service import Service
from app.schemas.schema_service import ServiceCreateIn, ServiceUpdateIn


def visible_only(query, include_hidden: bool):
    return query if include_hidden else query.where(Service.is_active.is_(True))


async def list_services(
    db: AsyncSession,
    category: str | None = None,
    department_id: int | None = None,
    filial_id: int | None = None,
    search: str | None = None,
    include_hidden: bool = False,
):
    query = visible_only(select(Service), include_hidden)

    if category:
        query = query.where(Service.category == category)

    if department_id:
        query = query.where(Service.department_id == department_id)

    if filial_id:
        query = query.where(Service.filial_id == filial_id)

    if search:
        pattern = f"%{search.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(Service.name).like(pattern),
                func.lower(Service.description).like(pattern),
            )
        )

    result = await db.execute(query.order_by(Service.category, Service.name))
    return result.scalars().all()


async def get_by_id(service_id: int, db: AsyncSession):
    result = await db.execute(select(Service).where(Service.id == service_id))
    return result.scalar_one_or_none()


async def get_by_name(name: str, db: AsyncSession):
    result = await db.execute(select(Service).where(Service.name == name))
    return result.scalar_one_or_none()


async def create_service(data: ServiceCreateIn, db: AsyncSession):
    service = Service(
        name=data.name,
        description=data.description,
        category=data.category,
        price=data.price,
        currency=data.currency,
        duration_minutes=data.duration_minutes,
        department_id=data.department_id,
        filial_id=data.filial_id,
        is_active=data.is_active,
    )

    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


async def update_service(service: Service, data: ServiceUpdateIn, db: AsyncSession):
    service.name = data.name or service.name
    service.description = data.description or service.description
    service.category = data.category or service.category
    service.price = service.price if data.price is None else data.price
    service.currency = data.currency or service.currency
    service.duration_minutes = data.duration_minutes or service.duration_minutes
    service.department_id = data.department_id or service.department_id
    service.filial_id = data.filial_id or service.filial_id
    service.is_active = service.is_active if data.is_active is None else data.is_active

    await db.commit()
    await db.refresh(service)
    return service


async def delete_service(service: Service, db: AsyncSession):
    await db.delete(service)
    await db.commit()
