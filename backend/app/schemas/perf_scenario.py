"""性能测试场景模块的 Pydantic 数据模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PerfScenarioIn(BaseModel):
    """新建性能场景请求。"""

    name: str = Field(..., min_length=1, max_length=200, description="场景名称")
    description: str | None = Field(default=None, max_length=500, description="场景描述")
    thread_count: int = Field(default=50, ge=1, le=10000, description="并发用户数")
    loop_count: int = Field(default=10, ge=1, le=100000, description="循环次数")
    ramp_up: int = Field(default=10, ge=1, le=3600, description="启动时间（秒）")
    think_time_ms: int = Field(default=500, ge=0, le=600000, description="思考时间（毫秒）")
    base_url: str = Field(default="localhost", min_length=1, max_length=200, description="目标主机/IP（不含协议端口）")
    base_port: str = Field(default="8000", min_length=1, max_length=10, description="目标端口")
    interface_ids: list[int] | None = Field(default=None, description="关联接口ID列表，空=全部接口")


class PerfScenarioUpdate(BaseModel):
    """编辑性能场景请求（部分字段可选）。"""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    thread_count: int | None = Field(default=None, ge=1, le=10000)
    loop_count: int | None = Field(default=None, ge=1, le=100000)
    ramp_up: int | None = Field(default=None, ge=1, le=3600)
    think_time_ms: int | None = Field(default=None, ge=0, le=600000)
    base_url: str | None = Field(default=None, min_length=1, max_length=200)
    base_port: str | None = Field(default=None, min_length=1, max_length=10)
    interface_ids: list[int] | None = None


class PerfScenarioOut(BaseModel):
    """性能场景信息响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    description: str | None
    thread_count: int
    loop_count: int
    ramp_up: int
    think_time_ms: int
    base_url: str
    base_port: str
    interface_ids: list[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PerfScenarioListOut(BaseModel):
    """性能场景分页列表响应。"""

    total: int
    page: int
    page_size: int
    items: list[PerfScenarioOut]
