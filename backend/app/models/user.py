"""用户模型。"""
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """系统用户表。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="用户ID"
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False, comment="用户名"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="密码哈希（bcrypt）"
    )
    nickname: Mapped[str | None] = mapped_column(String(50), comment="昵称")
    email: Mapped[str | None] = mapped_column(String(100), comment="邮箱")
    role: Mapped[str] = mapped_column(
        String(20), default="user", comment="角色：admin/user"
    )
    status: Mapped[int] = mapped_column(default=1, comment="状态：1启用 0禁用")
