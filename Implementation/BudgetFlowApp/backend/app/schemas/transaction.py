from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
import uuid

from pydantic import BaseModel, ConfigDict, model_validator


class TransactionRead(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    posted_date: date
    amount: Decimal
    description: str
    currency: str
    merchant_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    category_confidence: Optional[Decimal] = None
    categorization_source: Optional[str] = None
    needs_manual: bool = False
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RowError(BaseModel):
    row: int
    message: str


class ImportSessionRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    account_id: uuid.UUID
    status: str
    total_rows: int
    imported_count: int
    duplicate_count: int
    failed_count: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    row_errors: Optional[List[RowError]] = None
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="wrap")
    @classmethod
    def extract_row_errors(cls, data, handler):
        obj = handler(data)
        if hasattr(data, "metadata_json") and data.metadata_json and "row_errors" in data.metadata_json:
            obj.row_errors = [RowError(**e) for e in data.metadata_json["row_errors"]]
        return obj


class ImportQueuedResponse(BaseModel):
    import_session_id: uuid.UUID
    job_id: uuid.UUID
    status: str = "queued"
