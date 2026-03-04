import uuid
from datetime import date, datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field, ConfigDict, model_validator


REPORT_TYPES = ("monthly_summary", "category_breakdown", "budget_vs_actual", "transactions")
REPORT_FORMATS = ("pdf", "csv")


class ReportFilters(BaseModel):
    account_ids: Optional[List[uuid.UUID]] = None
    category_ids: Optional[List[uuid.UUID]] = None


class ReportCreate(BaseModel):
    type: Literal["monthly_summary", "category_breakdown", "budget_vs_actual", "transactions"]
    from_date: date
    to_date: date
    format: Literal["pdf", "csv"]
    filters: Optional[ReportFilters] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "ReportCreate":
        if self.to_date < self.from_date:
            raise ValueError("to_date must be >= from_date")
        delta = (self.to_date - self.from_date).days
        if delta > 366:
            raise ValueError("Date range must not exceed 366 days")
        return self


class ReportRead(BaseModel):
    id: uuid.UUID
    type: str
    format: str
    from_date: date
    to_date: date
    filters_json: Optional[dict] = None
    status: str
    error: Optional[str] = None
    download_url: Optional[str] = None
    job_id: Optional[uuid.UUID] = None
    job_status: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
