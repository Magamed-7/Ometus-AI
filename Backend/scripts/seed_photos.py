import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db.database import get_session_factory

# модель пользователя нужна не для запроса, а чтобы SQLAlchemy разрешил
# внешний ключ doctors.user_id
from app.models import model_user  # noqa: F401
from app.models.model_doctor import Doctor

# Портреты лежат во фронтенде: Frontend/public/img/doctors/doctor-NN-400.webp.
# 400px хватает с запасом — самый крупный аватар на странице 112px, дальше
# только экран с двойной плотностью.
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

            # снимков 11, врачей больше — раздаём по кругу. Лицо на карточке
            # всё равно иллюстрация, а не документ: настоящее фото врача
            # загрузит админ через PATCH /api/admin/doctors/{id}
            doctor.photo_url = PHOTOS[position % len(PHOTOS)]
            filled += 1

        await db.commit()
        print(f"фотографий проставлено: {filled}, уже было: {skipped}")


if __name__ == "__main__":
    asyncio.run(seed())
