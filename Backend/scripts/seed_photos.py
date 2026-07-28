import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db.database import get_session_factory

from app.models import model_user
from app.models.model_doctor import Doctor

PHOTOS = [f"/img/doctors/doctor-{index:02d}-400.webp" for index in range(1, 12)]


async def seed():
    factory = get_session_factory()

    async with factory() as db:
        doctors = (await db.execute(select(Doctor).order_by(Doctor.id))).scalars().all()
        filled = 0
        skipped = 0

        for position, doctor in enumerate(doctors):
            if doctor.photo_url:
                skipped += 1
                continue

            doctor.photo_url = PHOTOS[position % len(PHOTOS)]
            filled += 1

        await db.commit()
        print(f"фотографий проставлено: {filled}, уже было: {skipped}")


if __name__ == "__main__":
    asyncio.run(seed())
