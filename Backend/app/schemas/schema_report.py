from datetime import date

from pydantic import BaseModel


class DoctorWorkloadOut(BaseModel):
    doctor_id: int
    full_name: str
    specialization: str
    total: int
    booked: int
    completed: int
    cancelled: int
    no_show: int


class AppointmentsSummaryOut(BaseModel):
    date_from: date
    date_to: date
    total: int
    booked: int
    completed: int
    cancelled: int
    no_show: int
    doctors: int
    doctors_total: int = 0
    patients: int
