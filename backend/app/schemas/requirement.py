"""需求文档模块的 Pydantic 数据模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RequirementOut(BaseModel):
    """需求文档列表项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    file_name: str
    file_type: str
    file_size: int
    parse_status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class RequirementDetailOut(RequirementOut):
    """需求文档详情（含提取的文本内容）。"""

    content: str | None


class RequirementListOut(BaseModel):
    """需求文档分页列表响应。"""

    total: int
    page: int
    page_size: int
    items: list[RequirementOut]


class ParseResultOut(BaseModel):
    """AI 解析结果响应。"""

    requirement_id: int
    parse_status: str
    error_message: str | None
    result: dict | None
