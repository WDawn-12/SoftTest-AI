"""系统管理模块的 Pydantic 数据模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SettingsOut(BaseModel):
    """系统设置响应。"""

    settings: dict[str, str]


class SettingsUpdate(BaseModel):
    """系统设置更新请求。"""

    values: dict[str, str]


class OperationLogOut(BaseModel):
    """操作日志条目。"""

    id: int
    user_id: int | None
    username: str | None
    action: str
    module: str
    detail: str | None
    ip: str | None
    created_at: datetime


class OperationLogListOut(BaseModel):
    """操作日志分页响应。"""

    total: int
    page: int
    page_size: int
    items: list[OperationLogOut]


class AiCallLogOut(BaseModel):
    """AI 调用日志条目。"""

    id: int
    user_id: int | None
    username: str | None
    agent: str
    provider: str | None
    prompt_length: int
    response_length: int
    duration_ms: int
    status: str
    error_message: str | None
    created_at: datetime


class AiCallLogListOut(BaseModel):
    """AI 调用日志分页响应。"""

    total: int
    page: int
    page_size: int
    items: list[AiCallLogOut]
