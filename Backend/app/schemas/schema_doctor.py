from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class DoctorOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    specialization: str
    photo_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DoctorCreateIn(BaseModel):
    email: EmailStr
    password: str | None = None
    full_name: str
    specialization: str
    phone: str | None = None
    photo_url: str | None = Field(default=None, max_length=255)


class DoctorCreateOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    specialization: str
    password: str

    model_config = ConfigDict(from_attributes=True)


class DoctorUpdateIn(BaseModel):
    full_name: str | None = None
    specialization: str | None = None
    photo_url: str | None = Field(default=None, max_length=255)


class DoctorDepartmentIn(BaseModel):
    department_id: int


class SpecializationOut(BaseModel):
    id: int
    doctor_id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class SpecializationIn(BaseModel):
    name: str = Field(min_length=1)


class DoctorDismissIn(BaseModel):
    dismissed_at: date
    confirm: bool = False


class DoctorDismissOut(BaseModel):
    id: int
    full_name: str
    dismissed_at: date | None = None
    upcoming_appointments: int = 0

    model_config = ConfigDict(from_attributes=True)
