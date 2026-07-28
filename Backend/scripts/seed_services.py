import asyncio
import sys
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db.database import get_session_factory

from app.models import model_department, model_filial
from app.models.model_service import Service

SERVICES = [
    (
        "consultation",
        "Приём терапевта (первичный)",
        "Осмотр, сбор анамнеза, постановка предварительного диагноза.",
        "150.00",
        20,
    ),
    (
        "consultation",
        "Консультация кардиолога (первичная)",
        "Включает интерпретацию существующих результатов ЭКГ.",
        "200.00",
        20,
    ),
    (
        "consultation",
        "Повторный приём любого специалиста",
        "Корректировка плана лечения по результатам анализов.",
        "100.00",
        20,
    ),
    (
        "diagnostics",
        "УЗИ органов брюшной полости",
        "Печень, жёлчный пузырь, поджелудочная железа, селезёнка.",
        "180.00",
        30,
    ),
    (
        "diagnostics",
        "ЭКГ с расшифровкой",
        "12 отведений, заключение врача функциональной диагностики.",
        "80.00",
        15,
    ),
    (
        "analysis",
        "Общий анализ крови (ОАК)",
        "С лейкоцитарной формулой и СОЭ.",
        "60.00",
        10,
    ),
    (
        "analysis",
        "Биохимический анализ (стандарт)",
        "8 показателей: глюкоза, холестерин, АЛТ, АСТ и другие.",
        "240.00",
        10,
    ),
]


async def seed():
    factory = get_session_factory()

    async with factory() as db:
        added = 0
        skipped = 0

        for category, name, description, price, duration in SERVICES:
            exists = (
                await db.execute(select(Service).where(Service.name == name))
            ).scalar_one_or_none()

            if exists:
                skipped += 1
                continue

            db.add(
                Service(
                    name=name,
                    description=description,
                    category=category,
                    price=Decimal(price),
                    duration_minutes=duration,
                )
            )
            added += 1

        await db.commit()
        print(f"услуг добавлено: {added}, уже было: {skipped}")


if __name__ == "__main__":
    asyncio.run(seed())
