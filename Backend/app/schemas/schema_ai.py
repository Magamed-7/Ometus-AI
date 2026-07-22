from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field


class AskIn(BaseModel):
    message: str
    doctor_id: int | None = None
    day: date | None = Field(default=None, alias="date")
    slot_time: time | None = Field(default=None, alias="time")
    confirm: bool = False

    model_config = ConfigDict(populate_by_name=True)


class AskOut(BaseModel):
    action: str
    reply: str
    specialization: str | None = None
    error_code: str | None = None
    doctors: list[dict] | None = None
    slots: list[dict] | None = None
    appointment: dict | None = None
