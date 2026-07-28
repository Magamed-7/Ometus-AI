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


class DailyPointOut(BaseModel):
    """Один день на графике. Дни без записей тоже приходят, с нулями:

    если пропустить пустые даты, линия соединит 10-е с 14-м и провал в записях
    превратится в ровный отрезок — на графике это читается как «всё в порядке».
    """

    date: date
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
