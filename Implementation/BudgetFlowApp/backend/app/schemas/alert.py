from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict


class AlertRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    budget_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    threshold_percent: Decimal
    spent_amount: Decimal
    limit_amount: Decimal
    period_start: date
    period_end: date
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
