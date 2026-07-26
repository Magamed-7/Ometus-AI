from pydantic import BaseModel, ConfigDict


class FilialOut(BaseModel):
    id: int
    name: str
    legal_name: str | None = None
    inn: str | None = None
    city: str
    address: str
    phone: str | None = None
    license_number: str | None = None
    clinic_type: str | None = None
    opening_hours: str | None = None

    model_config = ConfigDict(from_attributes=True)


class FilialCreateIn(BaseModel):
    name: str
    legal_name: str | None = None
    inn: str | None = None
    city: str
    address: str
    phone: str | None = None
    license_number: str | None = None
    clinic_type: str | None = None
    opening_hours: str | None = None


class FilialUpdateIn(BaseModel):
    name: str | None = None
    legal_name: str | None = None
    inn: str | None = None
    city: str | None = None
    address: str | None = None
    phone: str | None = None
    license_number: str | None = None
    clinic_type: str | None = None
    opening_hours: str | None = None
