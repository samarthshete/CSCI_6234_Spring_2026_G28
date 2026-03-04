import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


class ChatCreateSession(BaseModel):
    title: Optional[str] = None


class ChatSendMessage(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[uuid.UUID] = None


class ChatMessageRead(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    tool_name: Optional[str] = None
    tool_payload: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionRead(BaseModel):
    id: uuid.UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageRead] = []

    model_config = ConfigDict(from_attributes=True)


class ChatSessionListItem(BaseModel):
    id: uuid.UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    message: ChatMessageRead
