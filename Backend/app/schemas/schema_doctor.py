from pydantic import BaseModel, ConfigDict, Field


class DoctorOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    specialization: str

    model_config = ConfigDict(from_attributes=True)


class DoctorCreateIn(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str
    specialization: str
    phone: str | None = None


class DoctorUpdateIn(BaseModel):
    full_name: str | None = None
    specialization: str | None = None


class DoctorDepartmentIn(BaseModel):
    department_id: int
