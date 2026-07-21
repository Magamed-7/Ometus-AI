from datetime import date

from pydantic import BaseModel, ConfigDict


class PatientOut(BaseModel):
    id: int
    user_id: int
    full_name: str | None = None
    date_of_birth: date | None = None
    phone: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PatientUpdateIn(BaseModel):
    full_name: str | None = None
    date_of_birth: date | None = None
    phone: str | None = None
