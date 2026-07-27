from datetime import date, time

import pytest

from app.models.model_appointment import Appointment
from app.services import email as email_service
from tests.conftest import verify_email

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
MY_ABSENCES_URL = "/api/schedules/me/absences"
PATIENT_URL = "/api/users/me/patient"
DEPENDENTS_URL = "/api/users/me/dependents"
ADMIN_FILIALS_URL = "/api/admin/filials"
ADMIN_DEPARTMENTS_URL = "/api/admin/departments"
ADMIN_DOCTORS_URL = "/api/admin/doctors"

FILIAL_DATA = {"name": "Ometus Центр", "city": "Душанбе", "address": "ул. Рудаки 100"}
DOCTOR_DATA = {
    "email": "doctor@ometus.test",
    "full_name": "Иванова Мария",
    "specialization": "Кардиолог",
}
ABSENCE = {"date_from": "2026-08-01", "date_to": "2026-08-10", "reason": "Больничный"}


@pytest.fixture
def sent_letters(monkeypatch):
    letters = []

    async def fake_deliver(email, doctor_name, day, slot_time, patient_name=None):
        letters.append(
            {
                "email": email,
                "doctor": doctor_name,
                "date": day,
                "time": slot_time,
                "patient": patient_name,
            }
        )
        return True

    monkeypatch.setattr(email_service, "deliver_appointment_cancelled", fake_deliver)
    return letters


async def register(client, email, password="secret1234", **extra):
    response = await client.post(
        REGISTER_URL, json={"email": email, "password": password, **extra}
    )
    if response.status_code == 200:
        await verify_email(client, email)

    return response


async def auth_headers(client, email, password="secret1234"):
    login = await client.post(LOGIN_URL, json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def setup_doctor(client, db):
    from sqlalchemy import select

    from app.models.model_user import User

    await register(client, "admin@ometus.test")
    user = (
        await db.execute(select(User).where(User.email == "admin@ometus.test"))
    ).scalar_one()
    user.role = "admin"
    await db.commit()
    admin = await auth_headers(client, "admin@ometus.test")

    filial = await client.post(ADMIN_FILIALS_URL, json=FILIAL_DATA, headers=admin)
    department = await client.post(
        ADMIN_DEPARTMENTS_URL,
        json={"filial_id": filial.json()["id"], "name": "Кардиология"},
        headers=admin,
    )
    doctor = await client.post(ADMIN_DOCTORS_URL, json=DOCTOR_DATA, headers=admin)
    doctor_id = doctor.json()["id"]
    await client.post(
        f"{ADMIN_DOCTORS_URL}/{doctor_id}/departments",
        json={"department_id": department.json()["id"]},
        headers=admin,
    )

    doctor_password = doctor.json()["password"]
    headers = await auth_headers(client, DOCTOR_DATA["email"], doctor_password)
    return doctor_id, department.json()["id"], headers


async def book_directly(db, patient_id, doctor_id, department_id, day=date(2026, 8, 3)):
    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department_id,
        date=day,
        time=time(9, 0),
        status="booked",
    )
    db.add(appointment)
    await db.commit()
    return appointment


async def test_patient_gets_a_letter_when_the_doctor_falls_ill(client, db, sent_letters):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    await register(client, "patient@ometus.test", first_name="Азиз")
    card = await client.get(PATIENT_URL, headers=await auth_headers(client, "patient@ometus.test"))
    await book_directly(db, card.json()["id"], doctor_id, department_id)

    response = await client.post(MY_ABSENCES_URL, json=ABSENCE, headers=doctor_headers)

    assert response.status_code == 200
    assert len(sent_letters) == 1
    letter = sent_letters[0]
    assert letter["email"] == "patient@ometus.test"
    assert letter["doctor"] == "Иванова Мария"
    assert letter["date"] == date(2026, 8, 3)
    assert letter["time"] == time(9, 0)


async def test_letter_about_a_relative_goes_to_the_guardian(client, db, sent_letters):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    await register(client, "guardian@ometus.test")
    guardian = await auth_headers(client, "guardian@ometus.test")
    relative = await client.post(
        DEPENDENTS_URL, json={"full_name": "Бабушка Ольга"}, headers=guardian
    )
    await book_directly(db, relative.json()["id"], doctor_id, department_id)

    await client.post(MY_ABSENCES_URL, json=ABSENCE, headers=doctor_headers)

    assert len(sent_letters) == 1
    assert sent_letters[0]["email"] == "guardian@ometus.test"
    assert sent_letters[0]["patient"] == "Бабушка Ольга"


async def test_untouched_days_send_nothing(client, db, sent_letters):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    await register(client, "patient@ometus.test")
    card = await client.get(PATIENT_URL, headers=await auth_headers(client, "patient@ometus.test"))
    await book_directly(db, card.json()["id"], doctor_id, department_id, day=date(2026, 9, 1))

    await client.post(MY_ABSENCES_URL, json=ABSENCE, headers=doctor_headers)

    assert sent_letters == []


async def test_broken_smtp_does_not_break_the_absence(client, db, monkeypatch):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    await register(client, "patient@ometus.test")
    card = await client.get(PATIENT_URL, headers=await auth_headers(client, "patient@ometus.test"))
    appointment = await book_directly(db, card.json()["id"], doctor_id, department_id)

    def explode(*args, **kwargs):
        raise OSError("SMTP недоступен")

    monkeypatch.setattr(email_service, "send_appointment_cancelled", explode)

    response = await client.post(MY_ABSENCES_URL, json=ABSENCE, headers=doctor_headers)
    await db.refresh(appointment)

    assert response.status_code == 200
    assert appointment.status == "cancelled"


def test_letter_says_nothing_about_the_doctors_diagnosis(monkeypatch):
    sent = {}

    def capture(to, subject, body):
        sent.update({"to": to, "subject": subject, "body": body})

    monkeypatch.setattr(email_service, "send_email", capture)
    email_service.send_appointment_cancelled(
        "patient@ometus.test", "Иванова Мария", date(2026, 8, 3), time(9, 0), "Азиз"
    )

    assert "Иванова Мария" in sent["body"]
    assert "03.08.2026" in sent["body"]
    assert "09:00" in sent["body"]
    assert "больничн" not in sent["body"].lower()
    assert "отпуск" not in sent["body"].lower()
