"""接口测试模块的 Pydantic 数据模型。"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

HttpMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]

InterfaceCaseCategory = Literal[
    "normal", "exception", "boundary", "security", "parameter"
]


# ---------- 接口定义 ----------
class InterfaceIn(BaseModel):
    """新增/编辑接口请求。"""

    name: str = Field(..., min_length=1, max_length=200, description="接口名称")
    method: HttpMethod = Field(default="GET", description="请求方法")
    path: str = Field(..., min_length=1, max_length=500, description="接口路径")
    summary: str | None = Field(default=None, max_length=500, description="接口描述")
    headers: str | None = Field(default=None, description="请求头（JSON 文本）")
    params: str | None = Field(default=None, description="查询参数（JSON 文本）")
    body: str | None = Field(default=None, description="请求体（JSON 文本）")


class InterfaceUpdate(BaseModel):
    """编辑接口请求（部分字段可选）。"""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    method: HttpMethod | None = None
    path: str | None = Field(default=None, min_length=1, max_length=500)
    summary: str | None = Field(default=None, max_length=500)
    headers: str | None = None
    params: str | None = None
    body: str | None = None


class InterfaceOut(BaseModel):
    """接口信息响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    method: str
    path: str
    summary: str | None
    headers: str | None
    params: str | None
    body: str | None
    created_at: datetime
    updated_at: datetime


class InterfaceListOut(BaseModel):
    """接口分页列表响应。"""

    total: int
    page: int
    page_size: int
    items: list[InterfaceOut]


class OpenApiImportIn(BaseModel):
    """OpenAPI（Swagger）JSON 导入请求。"""

    spec: dict = Field(..., description="OpenAPI 3.x / Swagger 2.0 JSON 文档")


# ---------- 接口测试用例 ----------
class InterfaceCaseOut(BaseModel):
    """接口测试用例信息响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    interface_id: int | None
    interface_name: str | None
    case_no: str
    title: str
    category: str
    method: str
    path: str
    test_data: str | None
    request_payload: str | None
    expected_status: str | None
    expected_result: str | None
    priority: str
    preconditions: str | None
    steps: str | None
    remark: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class InterfaceCaseListOut(BaseModel):
    """接口测试用例分页列表响应。"""

    total: int
    page: int
    page_size: int
    items: list[InterfaceCaseOut]


class InterfaceCaseUpdate(BaseModel):
    """编辑接口测试用例请求（人工编辑）。"""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    category: InterfaceCaseCategory | None = None
    test_data: str | None = None
    request_payload: str | None = None
    expected_status: str | None = None
    expected_result: str | None = None
    priority: Literal["高", "中", "低"] | None = None
    preconditions: str | None = None
    steps: str | None = None
    remark: str | None = None
