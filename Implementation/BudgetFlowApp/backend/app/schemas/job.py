import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class JobRead(BaseModel):
    id: uuid.UUID
    type: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    payload: dict
    result: Optional[dict] = None
    error_message: Optional[str] = None
    error_trace: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
