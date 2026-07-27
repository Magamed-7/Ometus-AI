from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

SERVICE_CATEGORIES = ["consultation", "diagnostics", "analysis", "treatment"]


class ServiceOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    category: str
    price: Decimal
    currency: str
    duration_minutes: int | None = None
    department_id: int | None = None
    filial_id: int | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ServiceCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    category: str = Field(pattern="^(consultation|diagnostics|analysis|treatment)$")
    price: Decimal = Field(ge=0, decimal_places=2, max_digits=10)
    currency: str = Field(default="TJS", min_length=3, max_length=3)
    duration_minutes: int | None = Field(default=None, ge=1, le=600)
    department_id: int | None = None
    filial_id: int | None = None
    is_active: bool = True


class ServiceUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    category: str | None = Field(
        default=None, pattern="^(consultation|diagnostics|analysis|treatment)$"
    )
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=10)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    duration_minutes: int | None = Field(default=None, ge=1, le=600)
    department_id: int | None = None
    filial_id: int | None = None
    is_active: bool | None = None
