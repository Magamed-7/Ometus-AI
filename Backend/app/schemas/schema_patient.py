from datetime import date

from pydantic import BaseModel, ConfigDict


class PatientOut(BaseModel):
    id: int
    user_id: int | None = None
    guardian_user_id: int | None = None
    full_name: str | None = None
    date_of_birth: date | None = None
    phone: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PatientUpdateIn(BaseModel):
    full_name: str | None = None
    date_of_birth: date | None = None
    phone: str | None = None


class DependentCreateIn(BaseModel):
    full_name: str
    date_of_birth: date | None = None
    phone: str | None = None
