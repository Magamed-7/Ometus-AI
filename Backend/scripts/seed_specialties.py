import asyncio
import sys
from datetime import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.database import get_session_factory
from app.models.model_department import Department
from app.models.model_doctor import Doctor
from app.models.model_doctor_department import DoctorDepartment
from app.models.model_schedule import DoctorSchedule
from app.models.model_user import User
from app.services.crud_doctor import generate_password, split_full_name

# в клинике не было ни одного хирурга, пульмонолога, аллерголога и ещё шести
# специализаций, которые ассистент умеет распознавать: он находил специализацию
# и тут же отвечал «врачей нет». Скрипт закрывает разрыв между словарём и клиникой
DEPARTMENTS = [
    ("Хирургия", 1, [
        ("Назаров Далер Сафарович", "Хирург"),
        ("Юсупова Гулнора Акбаровна", "Хирург"),
        ("Мирзоев Хуршед Тоирович", "Кардиохирург"),
    ]),
    ("Пульмонология", 2, [
        ("Каримов Сухроб Азизович", "Пульмонолог"),
        ("Шарипова Нигина Фаридовна", "Пульмонолог"),
    ]),
    ("Аллергология", 2, [
        ("Хакимов Джамшед Умарович", "Аллерголог"),
        ("Наботова Ситора Илхомовна", "Аллерголог"),
    ]),
    ("Ревматология", 3, [
        ("Собиров Бахтиёр Икромович", "Ревматолог"),
        ("Рахимова Мехрангез Давлатовна", "Ревматолог"),
    ]),
    ("Онкология", 1, [
        ("Асроров Фирдавс Каримович", "Онколог"),
        ("Табарова Зарина Хайруллоевна", "Онколог"),
    ]),
    ("Инфекционные болезни", 3, [
        ("Джураев Рустам Шодиевич", "Инфекционист"),
        ("Файзиева Малика Нуриддиновна", "Инфекционист"),
    ]),
    ("Нефрология", 3, [
        ("Одинаев Комрон Абдуллоевич", "Нефролог"),
    ]),
    ("Психотерапия", 2, [
        ("Сафаров Иброхим Муродович", "Психотерапевт"),
        ("Холова Дилноза Рахматовна", "Психотерапевт"),
    ]),
    ("Акушерство", 3, [
        ("Амонова Зулфия Саидовна", "Акушер"),
        ("Кобилова Шахло Джамоловна", "Акушер"),
    ]),
]

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ж": "zh", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
    "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

WORKDAYS = [(0, 2, 4), (1, 3, 5), (0, 1, 3), (2, 4, 5)]

START_TIME = time(9, 0)
END_TIME = time(17, 0)


def translit(word: str):
    return "".join(TRANSLIT.get(letter, letter) for letter in word.lower().replace("ё", "е"))


# почта строится как у уже засеянных врачей: «Саидов Фарход» → farkhod.saidov@ometus.tj
def make_email(full_name: str):
    parts = full_name.split()
    return f"{translit(parts[1])}.{translit(parts[0])}@ometus.tj"


async def get_or_create_department(name: str, filial_id: int, db):
    found = await db.execute(
        select(Department).where(
            func.lower(Department.name) == name.lower(), Department.filial_id == filial_id
        )
    )
    department = found.scalar_one_or_none()

    if department:
        return department, False

    department = Department(name=name, filial_id=filial_id)
    db.add(department)
    await db.flush()
    return department, True


async def get_or_create_doctor(full_name: str, specialization: str, db):
    email = make_email(full_name)
    found = await db.execute(select(User).where(func.lower(User.email) == email))
    user = found.scalar_one_or_none()

    if user:
        existing = await db.execute(select(Doctor).where(Doctor.user_id == user.id))
        return existing.scalar_one_or_none(), None

    password = generate_password()
    first_name, last_name = split_full_name(full_name)
    user = User(
        email=email,
        hashed_password=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        role="doctor",
        # врача заводит клиника, а не он сам: подтверждать почту ему нечем
        is_verified=True,
    )
    db.add(user)
    await db.flush()

    doctor = Doctor(user_id=user.id, full_name=full_name, specialization=specialization)
    db.add(doctor)
    await db.flush()
    return doctor, password


async def attach_department(doctor_id: int, department_id: int, db):
    found = await db.execute(
        select(DoctorDepartment).where(
            DoctorDepartment.doctor_id == doctor_id,
            DoctorDepartment.department_id == department_id,
        )
    )

    if found.scalar_one_or_none():
        return

    db.add(DoctorDepartment(doctor_id=doctor_id, department_id=department_id))


async def add_schedule(doctor_id: int, department_id: int, weekdays, slot: int, db):
    for weekday in weekdays:
        found = await db.execute(
            select(DoctorSchedule).where(
                DoctorSchedule.doctor_id == doctor_id,
                DoctorSchedule.department_id == department_id,
                DoctorSchedule.weekday == weekday,
            )
        )

        if found.scalar_one_or_none():
            continue

        db.add(
            DoctorSchedule(
                doctor_id=doctor_id,
                department_id=department_id,
                weekday=weekday,
                start_time=START_TIME,
                end_time=END_TIME,
                slot_duration=slot,
            )
        )


async def seed():
    created_departments = 0
    created_doctors = []
    index = 0

    async with get_session_factory()() as db:
        for name, filial_id, doctors in DEPARTMENTS:
            department, is_new = await get_or_create_department(name, filial_id, db)
            created_departments += int(is_new)

            for full_name, specialization in doctors:
                doctor, password = await get_or_create_doctor(full_name, specialization, db)

                if password:
                    created_doctors.append((make_email(full_name), password))

                await attach_department(doctor.id, department.id, db)
                await add_schedule(
                    doctor.id,
                    department.id,
                    WORKDAYS[index % len(WORKDAYS)],
                    20 if index % 2 else 30,
                    db,
                )
                index += 1

        await db.commit()

    print(f"Отделений заведено: {created_departments}")
    print(f"Врачей заведено: {len(created_doctors)}")

    for email, password in created_doctors:
        print(f"  {email}  {password}")

    if not created_doctors:
        print("Всё уже на месте — повторный запуск ничего не менял")


if __name__ == "__main__":
    asyncio.run(seed())
