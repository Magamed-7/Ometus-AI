from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id: Mapped[int | None] = mapped_column(
        ForeignKey("doctors.id"), nullable=True, index=True
    )
    filial_id: Mapped[int | None] = mapped_column(
        ForeignKey("filials.id"), nullable=True, index=True
    )
    # один приём — один отзыв: без этого пациент накрутит рейтинг врача с одного визита
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id"), nullable=False, unique=True
    )
    rating: Mapped[int] = mapped_column(nullable=False, index=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sql_text("true"), index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
