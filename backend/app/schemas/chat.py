"""AI 聊天模块的 Pydantic 数据模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageIn(BaseModel):
    """发送聊天消息请求。"""

    content: str = Field(min_length=1, max_length=4000, description="消息内容")


class ChatReplyOut(BaseModel):
    """AI 回复响应。"""

    id: int
    content: str
    created_at: datetime


class ChatMessageOut(BaseModel):
    """聊天记录条目。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime


class ChatHistoryOut(BaseModel):
    """聊天历史响应。"""

    total: int
    items: list[ChatMessageOut]
