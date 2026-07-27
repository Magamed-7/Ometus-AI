from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict

AppointmentStatus = Literal["booked", "completed", "cancelled", "no_show"]


class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    department_id: int
    date: date
    time: time
    status: AppointmentStatus
    is_emergency: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppointmentCreateIn(BaseModel):
    doctor_id: int
    date: date
    time: time
    patient_id: int | None = None


class EmergencyAppointmentIn(BaseModel):
    patient_id: int
    doctor_id: int
    department_id: int
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
    status: AppointmentStatus


class AdminAppointmentOut(BaseModel):
    id: int
    patient_id: int
    patient_name: str | None = None
    patient_phone: str | None = None
    doctor_id: int
    doctor_name: str
    specialization: str
    department_id: int
    date: date
    time: time
    status: AppointmentStatus
    is_emergency: bool
    created_at: datetime
