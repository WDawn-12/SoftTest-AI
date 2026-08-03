"""被测系统管理（System Under Test）模块的 Pydantic 数据模型。"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 系统类型与浏览器枚举
SYSTEM_TYPES = ("Web后台", "Web网站", "微信小程序", "Android", "iOS")
BROWSER_TYPES = ("Chrome", "Edge", "Firefox")


def validate_http_url(value: str | None) -> str | None:
    """校验 URL：必须为 http/https 开头。"""
    if value and not value.startswith(("http://", "https://")):
        raise ValueError("测试网址必须以 http:// 或 https:// 开头")
    return value


class SutIn(BaseModel):
    """创建被测系统请求。"""

    system_name: str = Field(min_length=1, max_length=100, description="系统名称")
    test_url: str = Field(max_length=500, description="系统地址(URL)")
    system_type: Literal["Web后台", "Web网站", "微信小程序", "Android", "iOS"] = Field(
        default="Web网站", description="系统类型"
    )
    browser_type: Literal["Chrome", "Edge", "Firefox"] = Field(
        default="Chrome", description="浏览器类型"
    )
    login_username: str | None = Field(default=None, max_length=100, description="测试账号")
    login_password: str | None = Field(default=None, max_length=200, description="测试密码（加密保存）")
    system_description: str | None = Field(default=None, max_length=2000, description="系统描述")

    @field_validator("test_url")
    @classmethod
    def _check_url(cls, value: str) -> str:
        return validate_http_url(value) or ""


class SutUpdate(BaseModel):
    """更新被测系统请求（部分字段）。"""

    system_name: str | None = Field(default=None, min_length=1, max_length=100)
    test_url: str | None = Field(default=None, max_length=500)
    system_type: Literal["Web后台", "Web网站", "微信小程序", "Android", "iOS"] | None = None
    browser_type: Literal["Chrome", "Edge", "Firefox"] | None = None
    login_username: str | None = Field(default=None, max_length=100)
    login_password: str | None = Field(default=None, max_length=200)
    system_description: str | None = Field(default=None, max_length=2000)

    @field_validator("test_url")
    @classmethod
    def _check_url(cls, value: str | None) -> str | None:
        return validate_http_url(value)


class SutOut(BaseModel):
    """被测系统信息响应（密码返回解密值，仅授权用户可访问）。"""

    system_name: str | None
    test_url: str | None
    system_type: str | None
    browser_type: str | None
    login_username: str | None
    login_password: str | None
    system_description: str | None


class TestConnectionOut(BaseModel):
    """测试连接结果响应。"""

    success: bool
    http_status: int | None = None
    response_time_ms: int | None = None
    message: str
