from pydantic import BaseModel, ConfigDict


class FilialOut(BaseModel):
    id: int
    name: str
    city: str
    address: str
    phone: str | None = None

    model_config = ConfigDict(from_attributes=True)


class FilialCreateIn(BaseModel):
    name: str
    city: str
    address: str
    phone: str | None = None


class FilialUpdateIn(BaseModel):
    name: str | None = None
    city: str | None = None
    address: str | None = None
    phone: str | None = None
