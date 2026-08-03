"""项目管理模块的 Pydantic 数据模型。"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProjectStatus = Literal["active", "finished", "archived"]


class ProjectCreate(BaseModel):
    """创建项目请求。"""

    name: str = Field(min_length=1, max_length=100, description="项目名称")
    description: str | None = Field(default=None, max_length=2000, description="项目描述")


class ProjectUpdate(BaseModel):
    """更新项目请求（部分字段更新）。"""

    name: str | None = Field(default=None, min_length=1, max_length=100, description="项目名称")
    description: str | None = Field(default=None, max_length=2000, description="项目描述")
    status: ProjectStatus | None = Field(default=None, description="项目状态")


class ProjectOut(BaseModel):
    """项目信息响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    status: str
    owner_id: int | None
    created_at: datetime
    updated_at: datetime


class ProjectListOut(BaseModel):
    """项目分页列表响应。"""

    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页条数")
    items: list[ProjectOut]
