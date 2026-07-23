from datetime import datetime, time

from sqlalchemy import DateTime, ForeignKey, Integer, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class DoctorSchedule(Base):
    __tablename__ = "doctor_schedule"
    __table_args__ = (
        UniqueConstraint("doctor_id", "department_id", "weekday", name="uq_doctor_schedule_day"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False, index=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"), nullable=False, index=True
    )
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    slot_duration: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    buffer_duration: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
