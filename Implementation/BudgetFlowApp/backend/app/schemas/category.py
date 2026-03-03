from datetime import datetime
from typing import Optional, List
import uuid

from pydantic import BaseModel, Field, ConfigDict


class RuleItem(BaseModel):
    pattern: str
    match: str = "contains"
    priority: int = 100


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(default="expense", pattern=r"^(income|expense)$")
    rules: List[RuleItem] = []


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = Field(None, pattern=r"^(income|expense)$")
    rules: Optional[List[RuleItem]] = None


class CategoryRead(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    name: str
    type: str
    rules: list
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CategorizeRequest(BaseModel):
    category_id: Optional[uuid.UUID] = None
