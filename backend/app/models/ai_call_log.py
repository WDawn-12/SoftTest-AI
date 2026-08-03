"""AI 调用日志模型。"""
from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AiCallLog(Base, TimestampMixin):
    """AI 调用日志表。"""

    __tablename__ = "ai_call_logs"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="日志ID"
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        comment="操作用户ID",
    )
    agent: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Agent：Requirement/TestPoint/TestCase/Chat"
    )
    provider: Mapped[str | None] = mapped_column(
        String(20), comment="模型供应商：openai/deepseek/demo"
    )
    prompt_length: Mapped[int] = mapped_column(Integer, default=0, comment="提示词长度")
    response_length: Mapped[int] = mapped_column(Integer, default=0, comment="回复长度")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, comment="耗时（毫秒）")
    status: Mapped[str] = mapped_column(
        String(20), default="success", comment="状态：success/failed"
    )
    error_message: Mapped[str | None] = mapped_column(
        String(500), comment="失败原因"
    )
