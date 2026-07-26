from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

FEEDBACK_VALUES = ["helpful", "partially", "not_helpful"]


class AiFeedback(Base):
    __tablename__ = "ai_feedback"
    # одна оценка на сообщение от одного пациента: повторная правит прежнюю,
    # иначе один недовольный клик мог бы перевесить всю статистику
    __table_args__ = (UniqueConstraint("message_id", "patient_id", name="uq_feedback_message"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("ai_messages.id"), nullable=False, index=True
    )
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    feedback: Mapped[str] = mapped_column(String, nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
