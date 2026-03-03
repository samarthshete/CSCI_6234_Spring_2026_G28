from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
import uuid

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class BudgetItemCreate(BaseModel):
    category_id: uuid.UUID
    limit_amount: Decimal = Field(..., gt=0)


class BudgetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    period_start: date
    period_end: date
    period_type: str = Field(default="monthly", pattern=r"^(monthly|weekly|custom)$")
    thresholds: List[float] = [0.8, 0.9, 1.0]
    items: List[BudgetItemCreate] = []

    @model_validator(mode="after")
    def validate_period_and_items(self) -> "BudgetCreate":
        if self.period_end < self.period_start:
            raise ValueError("period_end must be >= period_start")
        cat_ids = [item.category_id for item in self.items]
        if len(cat_ids) != len(set(cat_ids)):
            raise ValueError("Duplicate category_id in items")
        return self

    @field_validator("thresholds")
    @classmethod
    def validate_thresholds(cls, v: List[float]) -> List[float]:
        if not v:
            raise ValueError("thresholds must not be empty")
        for t in v:
            if t <= 0 or t > 1.0:
                raise ValueError("Each threshold must be in (0, 1.0]")
        if len(v) != len(set(v)):
            raise ValueError("thresholds must contain unique values")
        if sorted(v) != v:
            raise ValueError("thresholds must be sorted in ascending order")
        if v[-1] != 1.0:
            raise ValueError("thresholds must include 1.0 as the last element")
        return v


class BudgetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    period_type: Optional[str] = Field(None, pattern=r"^(monthly|weekly|custom)$")
    thresholds: Optional[List[float]] = None
    items: Optional[List[BudgetItemCreate]] = None

    @field_validator("thresholds")
    @classmethod
    def validate_thresholds(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is None:
            return v
        if not v:
            raise ValueError("thresholds must not be empty")
        for t in v:
            if t <= 0 or t > 1.0:
                raise ValueError("Each threshold must be in (0, 1.0]")
        if len(v) != len(set(v)):
            raise ValueError("thresholds must contain unique values")
        if sorted(v) != v:
            raise ValueError("thresholds must be sorted in ascending order")
        if v[-1] != 1.0:
            raise ValueError("thresholds must include 1.0 as the last element")
        return v

    @model_validator(mode="after")
    def validate_items_no_dupes(self) -> "BudgetUpdate":
        if self.items is not None:
            cat_ids = [item.category_id for item in self.items]
            if len(cat_ids) != len(set(cat_ids)):
                raise ValueError("Duplicate category_id in items")
        return self


class BudgetItemRead(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    limit_amount: Decimal
    model_config = ConfigDict(from_attributes=True)


class BudgetRead(BaseModel):
    id: uuid.UUID
    name: str
    period_start: date
    period_end: date
    period_type: str
    thresholds: list
    items: List[BudgetItemRead] = []
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
