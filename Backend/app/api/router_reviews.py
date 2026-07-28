from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.permissions import get_current_patient
from app.core.errors import AppError
from app.db.database import get_db
from app.schemas.schema_review import (
    MyReviewOut,
    ReviewCreateIn,
    ReviewOut,
    ReviewPageOut,
    ReviewSummaryOut,
)
from app.services import crud_appointment, crud_review

reviews_router = APIRouter(prefix="/api/reviews", tags=["Reviews"])


@reviews_router.get("", response_model=ReviewPageOut)
async def get_reviews(
    doctor_id: int | None = None,
    filial_id: int | None = None,
    page: int = 1,
    db: AsyncSession = Depends(get_db),
):
    items, total, pages = await crud_review.list_reviews(db, doctor_id, filial_id, page)
    stats = await crud_review.summary(db, doctor_id, filial_id)
    return {
        "items": items,
        "total": total,
        "page": max(page, 1),
        "pages": pages,
        "summary": stats,
    }


@reviews_router.get("/summary", response_model=ReviewSummaryOut)
async def get_summary(
    doctor_id: int | None = None,
    filial_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await crud_review.summary(db, doctor_id, filial_id)


@reviews_router.get("/mine", response_model=list[MyReviewOut])
async def get_my_reviews(
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    return await crud_review.list_own(patient.id, db)


@reviews_router.post("", response_model=ReviewOut, status_code=201)
async def leave_review(
    data: ReviewCreateIn,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    appointment = await crud_appointment.get_by_id(data.appointment_id, db)

    if appointment is None or appointment.patient_id != patient.id:
        raise AppError(
            code="APPOINTMENT_NOT_FOUND", message="Запись не найдена", status_code=404
        )

    if appointment.status != "completed":
        raise AppError(
            code="APPOINTMENT_NOT_COMPLETED",
            message="Оставить отзыв можно только после состоявшегося приёма",
            status_code=409,
        )

    if await crud_review.get_by_appointment(appointment.id, db):
        raise AppError(
            code="REVIEW_ALREADY_LEFT",
            message="Отзыв об этом приёме уже оставлен",
            status_code=409,
        )

    review = await crud_review.create_review(patient.id, appointment, data, db)
    return await crud_review.get_view(review.id, db)
