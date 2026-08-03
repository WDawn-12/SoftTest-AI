"""测试数据生成器模块的 Pydantic 数据模型。"""
from pydantic import BaseModel, Field


class TestDataRequest(BaseModel):
    """生成测试数据请求。"""

    field: str = Field(min_length=1, max_length=100, description="字段名称")
    type: str | None = Field(default=None, max_length=50, description="字段类型（可选，缺省自动识别）")
    count: int = Field(default=1, ge=1, le=10, description="每个类别生成数量")


class TestDataItem(BaseModel):
    """单条测试数据。"""

    case: str = Field(description="用例类别（正常/空值/超长/边界/注入等）")
    value: str = Field(description="测试数据值")


class TestDataResponse(BaseModel):
    """生成结果响应。"""

    field: str
    type: str
    data: list[TestDataItem]
