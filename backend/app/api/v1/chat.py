"""AI 聊天接口：对话、历史、清空。"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DbDep, get_current_user, get_owned_project
from app.models.chat_history import ChatHistory
from app.models.user import User
from app.schemas.chat import (
    ChatHistoryOut,
    ChatMessageIn,
    ChatMessageOut,
    ChatReplyOut,
)
from app.services.chat_service import build_reply

router = APIRouter(prefix="/projects/{project_id}/chat", tags=["AI 聊天"])

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/messages", response_model=ChatReplyOut, summary="发送消息（AI 对话）")
def send_message(
    project_id: int,
    payload: ChatMessageIn,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> ChatReplyOut:
    """发送消息，保存用户消息与 AI 回复，支持上下文记忆。"""
    get_owned_project(db, project_id, current_user)
    user_message = ChatHistory(
        user_id=current_user.id,
        project_id=project_id,
        role="user",
        content=payload.content,
    )
    db.add(user_message)
    assistant = build_reply(db, current_user.id, project_id, payload.content)
    db.refresh(assistant)
    return ChatReplyOut(
        id=assistant.id, content=assistant.content, created_at=assistant.created_at
    )


@router.get("/history", response_model=ChatHistoryOut, summary="聊天历史")
def list_history(
    project_id: int,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=100, ge=1, le=500, description="每页条数"),
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> ChatHistoryOut:
    """分页查询当前用户在当前项目下的聊天记录（按时间正序）。"""
    get_owned_project(db, project_id, current_user)
    query = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id,
        ChatHistory.project_id == project_id,
    )
    total = query.count()
    items = (
        query.order_by(ChatHistory.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ChatHistoryOut(
        total=total, items=[ChatMessageOut.model_validate(item) for item in items]
    )


@router.delete(
    "/history",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="清空聊天记录",
)
def clear_history(
    project_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> None:
    """清空当前用户在当前项目下的聊天记录。"""
    get_owned_project(db, project_id, current_user)
    db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id,
        ChatHistory.project_id == project_id,
    ).delete()
    db.commit()
