"""Pydantic schemas: the shape and validation rules of data going in and out of the API."""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.services.currency_service import CURRENCIES

BillingCycle = Literal["weekly", "monthly", "quarterly", "yearly"]


def _clean_currency(value: str) -> str:
    code = value.strip().upper()
    if code not in CURRENCIES:
        raise ValueError(f"Unsupported currency '{value}'. Use one of: {', '.join(CURRENCIES)}")
    return code


def _clean_name(value: str) -> str:
    name = " ".join(value.split())
    if not name:
        raise ValueError("Name cannot be empty")
    return name


# ---------------------------------------------------------------- categories
class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        return _clean_name(value)


class CategoryOut(BaseModel):
    id: int
    name: str
    color: str


# ------------------------------------------------------------- subscriptions
class SubscriptionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, le=10_000_000)
    currency: str = "USD"
    billing_cycle: BillingCycle = "monthly"
    next_renewal: date
    category_id: Optional[int] = None
    is_active: bool = True
    notes: Optional[str] = Field(default=None, max_length=300)

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        return _clean_name(value)

    @field_validator("currency")
    @classmethod
    def _currency(cls, value: str) -> str:
        return _clean_currency(value)


class SubscriptionUpdate(BaseModel):
    """Every field is optional: send only what you want to change."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    price: Optional[float] = Field(default=None, gt=0, le=10_000_000)
    currency: Optional[str] = None
    billing_cycle: Optional[BillingCycle] = None
    next_renewal: Optional[date] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(default=None, max_length=300)

    @field_validator("name")
    @classmethod
    def _name(cls, value: Optional[str]) -> Optional[str]:
        return None if value is None else _clean_name(value)

    @field_validator("currency")
    @classmethod
    def _currency(cls, value: Optional[str]) -> Optional[str]:
        return None if value is None else _clean_currency(value)


class SubscriptionOut(BaseModel):
    id: int
    name: str
    price: float
    currency: str
    billing_cycle: BillingCycle
    next_renewal: date
    category_id: Optional[int]
    category_name: Optional[str]
    category_color: Optional[str]
    is_active: bool
    notes: Optional[str]
    created_at: Optional[datetime]
    # Calculated fields, expressed in the display (base) currency:
    base_currency: str
    price_base: float
    monthly_cost: float
    yearly_cost: float
    days_until_renewal: int
