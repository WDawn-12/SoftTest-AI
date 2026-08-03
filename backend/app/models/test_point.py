"""测试点模型。"""
from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class TestPoint(Base, TimestampMixin):
    """测试点表（AI 生成，支持人工编辑）。"""

    __tablename__ = "test_points"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="测试点ID"
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
        ForeignKey("requirements.id", ondelete="CASCADE"),
        index=True,
        comment="来源需求ID",
    )
    module_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("modules.id", ondelete="SET NULL"),
        index=True,
        comment="所属模块ID",
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="测试点描述"
    )
    category: Mapped[str] = mapped_column(
        String(50),
        default="normal",
        comment="类别：normal/exception/boundary/security/compatibility",
    )
