from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_filial import Filial
from app.schemas.schema_filial import FilialCreateIn, FilialUpdateIn


async def create_filial(data: FilialCreateIn, db: AsyncSession):
    filial = Filial(
        name=data.name,
        city=data.city,
        address=data.address,
        phone=data.phone,
    )

    db.add(filial)
    await db.commit()
    await db.refresh(filial)
    return filial


async def get_filials(db: AsyncSession, city: str | None = None):
    query = select(Filial)

    if city:
        query = query.where(Filial.city == city)

    result = await db.execute(query.order_by(Filial.id))
    return result.scalars().all()


async def get_by_id(filial_id: int, db: AsyncSession):
    result = await db.execute(select(Filial).where(Filial.id == filial_id))
    return result.scalar_one_or_none()


async def update_filial(filial: Filial, data: FilialUpdateIn, db: AsyncSession):
    filial.name = data.name or filial.name
    filial.city = data.city or filial.city
    filial.address = data.address or filial.address
    filial.phone = data.phone or filial.phone

    await db.commit()
    await db.refresh(filial)
    return filial


async def delete_filial(filial: Filial, db: AsyncSession):
    await db.delete(filial)
    await db.commit()
