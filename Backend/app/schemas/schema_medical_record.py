from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MedicalRecordCreateIn(BaseModel):
    kind: Literal["condition", "allergy", "medication"]
    name: str = Field(min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=500)


class MedicalRecordOut(BaseModel):
    id: int
    kind: str
    name: str
    note: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AiConsentIn(BaseModel):
    allowed: bool


class AiConsentOut(BaseModel):
    ai_consent: bool
