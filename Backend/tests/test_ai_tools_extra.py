# Отдельный файл, чтобы не толкаться с правками test_ai_tools.py:
# здесь только проверки инструментов из раздела 7.0 Fix_bugs.md.
from datetime import date, timedelta

from app.ai import mcp_tools
from app.models.model_department import Department
from app.models.model_doctor import Doctor
from app.models.model_filial import Filial
from app.models.model_patient import Patient
from app.models.model_user import User


async def make_department(db, filial_name, department_name):
    filial = Filial(name=filial_name, city="Душанбе", address="ул. Рудаки 100")
    db.add(filial)
    await db.flush()

    department = Department(filial_id=filial.id, name=department_name)
    db.add(department)
    await db.commit()
    await db.refresh(department)
    return department


async def test_ambiguous_department_is_not_picked_silently(db):
    await make_department(db, "Ometus Центр", "Кардиология")
    await make_department(db, "Ometus Сомони", "Кардиология детская")

    result = await mcp_tools.find_doctors(db, department="Кардиолог")

    assert result["ok"] is False
    assert result["error"]["code"] == "DEPARTMENT_AMBIGUOUS"


async def test_exact_department_name_wins_over_substring(db):
    department = await make_department(db, "Ometus Центр", "Кардиология")
    await make_department(db, "Ometus Сомони", "Кардиология детская")

    user = User(email="doc@ometus.test", hashed_password="x", role="doctor", is_verified=True)
    db.add(user)
    await db.flush()
    doctor = Doctor(user_id=user.id, full_name="Иванова Мария", specialization="Кардиолог")
    db.add(doctor)
    await db.commit()

    from app.models.model_doctor_department import DoctorDepartment

    db.add(DoctorDepartment(doctor_id=doctor.id, department_id=department.id))
    await db.commit()

    result = await mcp_tools.find_doctors(db, department="Кардиология")

    assert result["ok"] is True
    assert result["data"][0]["full_name"] == "Иванова Мария"


async def test_ai_can_book_a_relative(db):
    guardian_user = User(
        email="guardian@ometus.test", hashed_password="x", role="patient", is_verified=True
    )
    db.add(guardian_user)
    await db.flush()

    guardian = Patient(user_id=guardian_user.id, full_name="Опекун")
    relative = Patient(guardian_user_id=guardian_user.id, full_name="Бабушка")
    db.add_all([guardian, relative])
    await db.commit()
    await db.refresh(guardian)
    await db.refresh(relative)

    # врача нет — значит дальше проверки прав дело не идёт, но именно она нас и интересует:
    # раньше здесь возвращалось PERMISSION_DENIED
    result = await mcp_tools.book_appointment(
        db,
        guardian,
        doctor_id=999,
        patient_id=relative.id,
        day=date.today() + timedelta(days=1),
        slot_time=mcp_tools.time(9, 0),
    )

    assert result["error"]["code"] == "DOCTOR_NOT_FOUND"


async def test_ai_still_refuses_a_stranger(db):
    user = User(email="me@ometus.test", hashed_password="x", role="patient", is_verified=True)
    stranger_user = User(
        email="stranger@ometus.test", hashed_password="x", role="patient", is_verified=True
    )
    db.add_all([user, stranger_user])
    await db.flush()

    mine = Patient(user_id=user.id, full_name="Я")
    stranger = Patient(user_id=stranger_user.id, full_name="Чужой")
    db.add_all([mine, stranger])
    await db.commit()
    await db.refresh(mine)
    await db.refresh(stranger)

    result = await mcp_tools.book_appointment(
        db,
        mine,
        doctor_id=999,
        patient_id=stranger.id,
        day=date.today() + timedelta(days=1),
        slot_time=mcp_tools.time(9, 0),
    )

    assert result["error"]["code"] == "PERMISSION_DENIED"
