from pydantic import BaseModel, ConfigDict, EmailStr, Field


class DoctorOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    specialization: str

    model_config = ConfigDict(from_attributes=True)


class DoctorCreateIn(BaseModel):
    email: EmailStr
    password: str | None = None
    full_name: str
    specialization: str
    phone: str | None = None


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


class DoctorDepartmentIn(BaseModel):
    department_id: int


class SpecializationOut(BaseModel):
    id: int
    doctor_id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class SpecializationIn(BaseModel):
    name: str = Field(min_length=1)
