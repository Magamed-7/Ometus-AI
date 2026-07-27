from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal

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
    city: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class AskOut(BaseModel):
    action: str
    reply: str
    conversation_id: int
    message_id: int | None = None
    severity: int = 0
    language: str = "ru"
    detected_intent: str | None = None
    intent_confidence: float | None = None
    emr_used: bool = False
    specialization: str | None = None
    alternatives: list[str] | None = None
    suggestions: list[str] | None = None
    error_code: str | None = None
    doctors: list[dict] | None = None
    slots: list[dict] | None = None
    doctor_id: int | None = None
    doctor_name: str | None = None
    appointment: dict | None = None
    appointments: list[dict] | None = None
    schedule: list[dict] | None = None


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    action: str | None = None
    payload: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationHistoryOut(BaseModel):
    conversation_id: int
    title: str | None = None
    messages: list[MessageOut]


class ConversationOut(BaseModel):
    id: int
    title: str | None = None
    messages: int
    preview: str | None = None
    created_at: datetime
    updated_at: datetime


class ConversationRenameIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class FeedbackIn(BaseModel):
    message_id: int
    feedback: Literal["helpful", "partially", "not_helpful"]
    reason: str | None = Field(default=None, max_length=500)


class FeedbackOut(BaseModel):
    id: int
    message_id: int
    feedback: str
    reason: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ComplaintOut(BaseModel):
    reply: str
    reason: str | None = None
    created_at: datetime


class FeedbackSummaryOut(BaseModel):
    total: int
    helpful: int
    partially: int
    not_helpful: int
    helpful_rate: float | None = None
    recent_complaints: list[ComplaintOut]


class AiTaskOut(BaseModel):
    id: str
    status: str
    result_json: dict | None = None
    error: str | None = None
    created_at: datetime
    finished_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class LlmMetricOut(BaseModel):
    provider: str
    model: str
    calls: int
    succeeded: int
    failed: int
    success_rate: float
    avg_duration_ms: int
    prompt_tokens: int
    completion_tokens: int
    cost_usd: Decimal


class AiCostsOut(BaseModel):
    total_usd: Decimal
    budget_usd: Decimal
    budget_used_percent: float | None = None
    over_budget: bool
    prices_configured: bool
    by_model: list[LlmMetricOut]


class CheckupSuggestionOut(BaseModel):
    doctor_id: int
    doctor_name: str
    specialization: str
    last_visit: date
    reply: str
