"""项目模型。"""
from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    """测试项目表。"""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="项目ID"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="项目名称"
    )
    description: Mapped[str | None] = mapped_column(Text, comment="项目描述")
    status: Mapped[str] = mapped_column(
        String(20), default="active", comment="状态：active/finished/archived"
    )
    owner_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="创建人用户ID",
    )

    # 被测系统（System Under Test）信息
    system_name: Mapped[str | None] = mapped_column(
        String(100), comment="被测系统名称"
    )
    test_url: Mapped[str | None] = mapped_column(String(500), comment="测试网址")
    system_type: Mapped[str | None] = mapped_column(
        String(20), comment="系统类型：Web后台/Web网站/微信小程序/Android/iOS"
    )
    browser_type: Mapped[str | None] = mapped_column(
        String(20), comment="浏览器类型：Chrome/Edge/Firefox"
    )
    login_username: Mapped[str | None] = mapped_column(
        String(100), comment="测试账号"
    )
    login_password: Mapped[str | None] = mapped_column(
        String(255), comment="测试密码（加密存储）"
    )
    system_description: Mapped[str | None] = mapped_column(Text, comment="系统描述")
