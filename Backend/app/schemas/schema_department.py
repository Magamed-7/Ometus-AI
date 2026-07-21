from pydantic import BaseModel, ConfigDict


class DepartmentOut(BaseModel):
    id: int
    filial_id: int
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DepartmentCreateIn(BaseModel):
    filial_id: int
    name: str
    description: str | None = None


class DepartmentUpdateIn(BaseModel):
    filial_id: int | None = None
    name: str | None = None
    description: str | None = None
