import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatCreateSession, ChatSendMessage, ChatResponse,
    ChatSessionRead, ChatSessionListItem,
)
from app.services.advisor import advisor_service
from app.services.advisor.llm_provider import LLMProvider, OpenAIProvider

router = APIRouter(redirect_slashes=False)

_llm_instance: Optional[LLMProvider] = None


def get_llm() -> LLMProvider:
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            base_url=settings.OPENAI_BASE_URL,
        )
    return _llm_instance


def _check_enabled():
    if not settings.ADVISOR_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Advisor feature is disabled. Set ADVISOR_ENABLED=true.",
        )


@router.post("/sessions", response_model=ChatSessionListItem, status_code=201)
async def create_session(
    payload: ChatCreateSession,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_enabled()
    session = await advisor_service.create_session(db, current_user.id, payload.title)
    return session


@router.get("/sessions", response_model=List[ChatSessionListItem])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_enabled()
    return await advisor_service.list_sessions(db, current_user.id)


@router.get("/sessions/{session_id}", response_model=ChatSessionRead)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_enabled()
    return await advisor_service.get_session(db, current_user.id, session_id)


@router.post("/message", response_model=ChatResponse)
async def send_message(
    payload: ChatSendMessage,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm: LLMProvider = Depends(get_llm),
):
    _check_enabled()
    session, msg = await advisor_service.send_message(
        db, current_user.id, llm, payload.content, payload.session_id,
    )
    return ChatResponse(session_id=session.id, message=msg)
