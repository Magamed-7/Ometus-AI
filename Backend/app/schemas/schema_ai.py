from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field


class AskIn(BaseModel):
    message: str
    doctor_id: int | None = None
    appointment_id: int | None = None
    day: date | None = Field(default=None, alias="date")
    slot_time: time | None = Field(default=None, alias="time")
    confirm: bool = False
    intent: str | None = None
    conversation_id: int | None = None
    severity: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class AskOut(BaseModel):
    action: str
    reply: str
    conversation_id: int
    severity: int = 0
    specialization: str | None = None
    alternatives: list[str] | None = None
    error_code: str | None = None
    doctors: list[dict] | None = None
    slots: list[dict] | None = None
    appointment: dict | None = None
    appointments: list[dict] | None = None
    schedule: list[dict] | None = None
