from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field


class ScheduleOut(BaseModel):
    id: int
    doctor_id: int
    department_id: int
    weekday: int
    start_time: time
    end_time: time
    slot_duration: int
    buffer_duration: int

    model_config = ConfigDict(from_attributes=True)


class ScheduleCreateIn(BaseModel):
    department_id: int
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    slot_duration: int = Field(default=20, ge=5, le=240)
    buffer_duration: int = Field(default=0, ge=0, le=120)


class ScheduleUpdateIn(BaseModel):
    department_id: int | None = None
    weekday: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    slot_duration: int | None = Field(default=None, ge=5, le=240)
    buffer_duration: int | None = Field(default=None, ge=0, le=120)


class DateScheduleOut(BaseModel):
    id: int
    doctor_id: int
    department_id: int
    date: date
    start_time: time
    end_time: time
    slot_duration: int
    buffer_duration: int

    model_config = ConfigDict(from_attributes=True)


class DateScheduleCreateIn(BaseModel):
    department_id: int
    date: date
    start_time: time
    end_time: time
    slot_duration: int = Field(default=20, ge=5, le=240)
    buffer_duration: int = Field(default=0, ge=0, le=120)


class AbsenceOut(BaseModel):
    id: int
    doctor_id: int
    date_from: date
    date_to: date
    reason: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AbsenceCreateIn(BaseModel):
    date_from: date
    date_to: date
    reason: str | None = None


class SlotOut(BaseModel):
    date: date
    time: time
    department_id: int


class DayPlanOut(BaseModel):
    date: date
    weekday: int
    status: str
    start_time: time | None = None
    end_time: time | None = None
    department_id: int | None = None
    absence_reason: str | None = None
    slots_free: int = 0
    slots_taken: int = 0
