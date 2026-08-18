"""测试点模块的 Pydantic 数据模型。"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TestPointCategory = Literal[
    "normal",
    "exception",
    "boundary",
    "security",
    "compatibility",
    "performance",
]


class TestPointOut(BaseModel):
    """测试点信息响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    requirement_id: int | None
    module_id: int | None
    module_name: str | None
    name: str
    category: str
    created_at: datetime
    updated_at: datetime


class TestPointListOut(BaseModel):
    """测试点分页列表响应。"""

    total: int
    page: int
    page_size: int
    items: list[TestPointOut]


class TestPointUpdate(BaseModel):
    """更新测试点请求（人工编辑）。"""

    name: str | None = Field(default=None, min_length=1, max_length=255, description="测试点描述")
    category: TestPointCategory | None = Field(default=None, description="测试类别")
