"""操作日志模型。"""
from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class OperationLog(Base, TimestampMixin):
    """操作日志表。"""

    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="日志ID"
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        comment="操作用户ID",
    )
    action: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="操作动作"
    )
    module: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="操作模块"
    )
    detail: Mapped[str | None] = mapped_column(Text, comment="操作详情")
    ip: Mapped[str | None] = mapped_column(String(50), comment="操作来源 IP")
