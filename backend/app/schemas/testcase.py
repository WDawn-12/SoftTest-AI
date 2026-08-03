"""测试用例模块的 Pydantic 数据模型。"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Priority = Literal["高", "中", "低"]


class TestCaseOut(BaseModel):
    """测试用例信息响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    requirement_id: int | None
    module_id: int | None
    module_name: str | None
    case_no: str
    title: str
    test_point: str | None
    priority: str
    preconditions: str | None
    steps: str | None
    expected_result: str | None
    remark: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class TestCaseListOut(BaseModel):
    """测试用例分页列表响应。"""

    total: int
    page: int
    page_size: int
    items: list[TestCaseOut]


class TestCaseUpdate(BaseModel):
    """更新测试用例请求（人工编辑）。"""

    title: str | None = Field(default=None, min_length=1, max_length=200, description="功能名称")
    test_point: str | None = Field(default=None, max_length=500, description="测试点")
    priority: Priority | None = Field(default=None, description="优先级")
    preconditions: str | None = Field(default=None, description="前置条件")
    steps: str | None = Field(default=None, description="测试步骤（每行一步）")
    expected_result: str | None = Field(default=None, description="预期结果")
    remark: str | None = Field(default=None, description="备注")
