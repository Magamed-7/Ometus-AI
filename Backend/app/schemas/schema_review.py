from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewOut(BaseModel):
    id: int
    rating: int
    text: str | None = None
    doctor_id: int | None = None
    doctor_name: str | None = None
    filial_id: int | None = None
    filial_name: str | None = None
    # только имя и первая буква фамилии: отзыв публичный, полное ФИО пациента
    # вместе с врачом и датой визита — это уже медицинская тайна
    author: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewSummaryOut(BaseModel):
    average: float | None = None
    total: int
    breakdown: dict[int, int]


class ReviewPageOut(BaseModel):
    items: list[ReviewOut]
    total: int
    page: int
    pages: int
    summary: ReviewSummaryOut


class ReviewCreateIn(BaseModel):
    appointment_id: int
    rating: int = Field(ge=1, le=5)
    text: str | None = Field(default=None, max_length=2000)


class ReviewModerateIn(BaseModel):
    is_published: bool


class ReviewAdminOut(ReviewOut):
    patient_id: int
    appointment_id: int
    is_published: bool
