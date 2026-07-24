from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class DoctorSpecialization(Base):
    __tablename__ = "doctor_specializations"
    __table_args__ = (
        UniqueConstraint("doctor_id", "name", name="uq_doctor_specialization"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
