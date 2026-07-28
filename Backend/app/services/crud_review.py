from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_department import Department
from app.models.model_doctor import Doctor
from app.models.model_filial import Filial
from app.models.model_patient import Patient
from app.models.model_review import Review
from app.schemas.schema_review import ReviewCreateIn

PER_PAGE = 9


def short_author(full_name: str | None):
    parts = (full_name or "").split()

    if len(parts) >= 2:
        return f"{parts[0]} {parts[1][0]}."

    return parts[0] if parts else "Пациент"


def apply_filters(query, doctor_id: int | None, filial_id: int | None, published_only: bool):
    if published_only:
        query = query.where(Review.is_published.is_(True))

    if doctor_id:
        query = query.where(Review.doctor_id == doctor_id)

    if filial_id:
        query = query.where(Review.filial_id == filial_id)

    return query


def joined_query():
    return (
        select(Review, Patient.full_name, Doctor.full_name, Filial.name)
        .join(Patient, Patient.id == Review.patient_id)
        .outerjoin(Doctor, Doctor.id == Review.doctor_id)
        .outerjoin(Filial, Filial.id == Review.filial_id)
    )


def as_view(review, patient_name, doctor_name, filial_name):
    return {
        "id": review.id,
        "rating": review.rating,
        "text": review.text,
        "doctor_id": review.doctor_id,
        "doctor_name": doctor_name,
        "filial_id": review.filial_id,
        "filial_name": filial_name,
        "author": short_author(patient_name),
        "created_at": review.created_at,
        "patient_id": review.patient_id,
        "appointment_id": review.appointment_id,
        "is_published": review.is_published,
    }


async def get_view(review_id: int, db: AsyncSession):
    row = (await db.execute(joined_query().where(Review.id == review_id))).first()
    return as_view(*row) if row else None


async def list_reviews(
    db: AsyncSession,
    doctor_id: int | None = None,
    filial_id: int | None = None,
    page: int = 1,
    published_only: bool = True,
):
    query = apply_filters(joined_query(), doctor_id, filial_id, published_only)

    counted = apply_filters(select(func.count(Review.id)), doctor_id, filial_id, published_only)
    total = (await db.execute(counted)).scalar_one()

    page = max(page, 1)
    result = await db.execute(
        query.order_by(Review.created_at.desc(), Review.id.desc())
        .limit(PER_PAGE)
        .offset((page - 1) * PER_PAGE)
    )

    items = [as_view(*row) for row in result.all()]
    pages = (total + PER_PAGE - 1) // PER_PAGE
    return items, total, pages


async def summary(
    db: AsyncSession,
    doctor_id: int | None = None,
    filial_id: int | None = None,
    published_only: bool = True,
):
    query = apply_filters(
        select(Review.rating, func.count(Review.id)).group_by(Review.rating),
        doctor_id,
        filial_id,
        published_only,
    )
    rows = (await db.execute(query)).all()

    breakdown = {star: 0 for star in range(1, 6)}
    total = 0
    weighted = 0

    for rating, count in rows:
        breakdown[rating] = count
        total += count
        weighted += rating * count

    average = round(weighted / total, 1) if total else None
    return {"average": average, "total": total, "breakdown": breakdown}


async def get_by_id(review_id: int, db: AsyncSession):
    result = await db.execute(select(Review).where(Review.id == review_id))
    return result.scalar_one_or_none()


async def get_by_appointment(appointment_id: int, db: AsyncSession):
    result = await db.execute(select(Review).where(Review.appointment_id == appointment_id))
    return result.scalar_one_or_none()


async def list_own(patient_id: int, db: AsyncSession):
    result = await db.execute(
        joined_query().where(Review.patient_id == patient_id).order_by(Review.created_at.desc())
    )
    return [
        as_view(review, patient_name, doctor_name, filial_name)
        for review, patient_name, doctor_name, filial_name in result.all()
    ]


async def create_review(patient_id: int, appointment, data: ReviewCreateIn, db: AsyncSession):
    filial_id = (
        await db.execute(
            select(Department.filial_id).where(Department.id == appointment.department_id)
        )
    ).scalar_one_or_none()

    review = Review(
        patient_id=patient_id,
        doctor_id=appointment.doctor_id,
        filial_id=filial_id,
        appointment_id=appointment.id,
        rating=data.rating,
        text=data.text,
    )

    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


async def set_published(review: Review, is_published: bool, db: AsyncSession):
    review.is_published = is_published
    await db.commit()
    await db.refresh(review)
    return review


async def delete_review(review: Review, db: AsyncSession):
    await db.delete(review)
    await db.commit()
