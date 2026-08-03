"""功能模块模型。"""
from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Module(Base, TimestampMixin):
    """功能模块表（由 AI 从需求中提取）。"""

    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="模块ID"
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="所属项目ID",
    )
    requirement_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("requirements.id", ondelete="SET NULL"),
        comment="来源需求ID",
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="模块名称"
    )
    description: Mapped[str | None] = mapped_column(Text, comment="模块描述")
    sort_order: Mapped[int] = mapped_column(default=0, comment="排序号")
