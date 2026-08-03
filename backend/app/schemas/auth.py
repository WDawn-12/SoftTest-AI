"""认证与用户模块的 Pydantic 数据模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    """用户注册请求。"""

    username: str = Field(min_length=3, max_length=50, description="用户名")
    password: str = Field(min_length=6, max_length=64, description="密码")
    nickname: str | None = Field(default=None, max_length=50, description="昵称")
    email: str | None = Field(default=None, max_length=100, description="邮箱")


class UserOut(BaseModel):
    """用户信息响应（不含密码）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str | None
    email: str | None
    role: str
    status: int
    created_at: datetime


class TokenResponse(BaseModel):
    """登录成功响应。"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="令牌有效期（秒）")
    user: UserOut


class UpdateUserStatus(BaseModel):
    """更新用户状态请求。"""

    status: int = Field(ge=0, le=1, description="状态：1启用 0禁用")
