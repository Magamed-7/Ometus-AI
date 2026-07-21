from typing import Literal

from pydantic import BaseModel, ConfigDict

Role = Literal["patient", "doctor", "admin"]


class UserOut(BaseModel):
    id: int
    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    role: Role

    model_config = ConfigDict(from_attributes=True)


class UserUpdateIn(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
