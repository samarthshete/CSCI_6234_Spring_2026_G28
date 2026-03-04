import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatSession, ChatMessage
from app.services.advisor.llm_provider import LLMProvider, openai_tool_schema
from app.services.advisor.prompt import SYSTEM_PROMPT
from app.services.advisor.tool_registry import execute_tool

MAX_CONTEXT_MESSAGES = 10
MAX_TOOL_ROUNDS = 3


async def create_session(
    db: AsyncSession, user_id: uuid.UUID, title: Optional[str] = None,
) -> ChatSession:
    session = ChatSession(user_id=user_id, title=title or "New conversation")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def list_sessions(db: AsyncSession, user_id: uuid.UUID) -> List[ChatSession]:
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
    )
    return list(result.scalars().unique().all())


async def get_session(
    db: AsyncSession, user_id: uuid.UUID, session_id: uuid.UUID,
) -> ChatSession:
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == user_id,
        )
    )
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


def _build_context(messages: List[ChatMessage]) -> list[dict]:
    """Build the LLM messages array from recent chat history."""
    context: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    recent = messages[-MAX_CONTEXT_MESSAGES:]
    for m in recent:
        if m.role == "tool":
            payload = m.tool_payload or {}
            content = json.dumps(payload)[:2000]
            context.append({
                "role": "tool",
                "tool_call_id": f"call_{m.tool_name}",
                "content": content,
            })
        elif m.role == "assistant" and m.tool_name:
            context.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": f"call_{m.tool_name}",
                    "type": "function",
                    "function": {
                        "name": m.tool_name,
                        "arguments": json.dumps(m.tool_payload or {}),
                    },
                }],
            })
        else:
            context.append({"role": m.role, "content": m.content or ""})
    return context


async def send_message(
    db: AsyncSession,
    user_id: uuid.UUID,
    llm: LLMProvider,
    content: str,
    session_id: Optional[uuid.UUID] = None,
) -> tuple[ChatSession, ChatMessage]:
    if session_id:
        session = await get_session(db, user_id, session_id)
    else:
        session = await create_session(db, user_id, title=content[:80])

    user_msg = ChatMessage(session_id=session.id, role="user", content=content)
    db.add(user_msg)
    await db.flush()

    all_messages = list(session.messages) + [user_msg]
    tools_schema = openai_tool_schema()

    for _ in range(MAX_TOOL_ROUNDS):
        context = _build_context(all_messages)

        try:
            resp = await llm.chat_completion(context, tools=tools_schema)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM service is unavailable. Please try again later.",
            )

        choice = resp["choices"][0]
        msg = choice["message"]

        if msg.get("tool_calls"):
            tc = msg["tool_calls"][0]
            fn_name = tc["function"]["name"]
            try:
                fn_args = json.loads(tc["function"]["arguments"])
            except (json.JSONDecodeError, KeyError):
                fn_args = {}

            tool_call_msg = ChatMessage(
                session_id=session.id, role="assistant", content="",
                tool_name=fn_name, tool_payload=fn_args,
            )
            db.add(tool_call_msg)
            await db.flush()

            tool_result = await execute_tool(fn_name, db, user_id, fn_args)

            tool_result_msg = ChatMessage(
                session_id=session.id, role="tool", content="",
                tool_name=fn_name, tool_payload=tool_result,
            )
            db.add(tool_result_msg)
            await db.flush()

            all_messages.extend([tool_call_msg, tool_result_msg])
            continue

        assistant_text = msg.get("content") or "I could not generate a response."
        assistant_msg = ChatMessage(
            session_id=session.id, role="assistant", content=assistant_text,
        )
        db.add(assistant_msg)
        session.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(assistant_msg)
        return session, assistant_msg

    fallback = ChatMessage(
        session_id=session.id, role="assistant",
        content="I gathered the data but could not formulate a response. Please try rephrasing your question.",
    )
    db.add(fallback)
    session.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(fallback)
    return session, fallback
