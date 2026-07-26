from datetime import date, datetime, time

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
    language: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class AskOut(BaseModel):
    action: str
    reply: str
    conversation_id: int
    severity: int = 0
    language: str = "ru"
    specialization: str | None = None
    alternatives: list[str] | None = None
    error_code: str | None = None
    doctors: list[dict] | None = None
    slots: list[dict] | None = None
    appointment: dict | None = None
    appointments: list[dict] | None = None
    schedule: list[dict] | None = None


class MessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationHistoryOut(BaseModel):
    conversation_id: int
    messages: list[MessageOut]


class CheckupSuggestionOut(BaseModel):
    doctor_id: int
    doctor_name: str
    specialization: str
    last_visit: date
    reply: str
