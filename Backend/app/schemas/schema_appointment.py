from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict


class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    department_id: int
    date: date
    time: time
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppointmentCreateIn(BaseModel):
    doctor_id: int
    date: date
    time: time


class AppointmentRescheduleIn(BaseModel):
    date: date
    time: time


class DoctorAppointmentOut(BaseModel):
    id: int
    patient_id: int
    patient_name: str | None = None
    patient_phone: str | None = None
    department_id: int
    date: date
    time: time
    status: str
