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
