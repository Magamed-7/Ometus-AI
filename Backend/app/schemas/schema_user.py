from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["patient", "doctor", "admin", "registrar"]


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


class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class EmailChangeIn(BaseModel):
    email: EmailStr
    password: str


class RoleUpdateIn(BaseModel):
    role: Role
