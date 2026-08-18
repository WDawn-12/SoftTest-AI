"""接口定义模型（接口测试模块）。"""
from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Interface(Base, TimestampMixin):
    """接口定义表（手动录入或 OpenAPI 导入）。"""

    __tablename__ = "interfaces"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="接口ID"
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="所属项目ID",
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="接口名称"
    )
    method: Mapped[str] = mapped_column(
        String(10), default="GET", nullable=False, comment="请求方法"
    )
    path: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="接口路径"
    )
    summary: Mapped[str | None] = mapped_column(
        String(500), comment="接口描述"
    )
    headers: Mapped[str | None] = mapped_column(Text, comment="请求头（JSON）")
    params: Mapped[str | None] = mapped_column(Text, comment="查询参数（JSON 数组）")
    body: Mapped[str | None] = mapped_column(Text, comment="请求体（JSON）")
