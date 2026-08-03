"""需求文档模型。"""
from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Requirement(Base, TimestampMixin):
    """需求文档表。"""

    __tablename__ = "requirements"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="需求ID"
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="所属项目ID",
    )
    file_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="原始文件名"
    )
    file_path: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="文件存储路径"
    )
    file_type: Mapped[str | None] = mapped_column(
        String(20), comment="文件类型：docx/pdf/txt"
    )
    file_size: Mapped[int | None] = mapped_column(comment="文件大小（字节）")
    content: Mapped[str | None] = mapped_column(
        Text, comment="文档提取的纯文本内容"
    )
    parse_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="解析状态：pending/parsing/completed/failed",
    )
    parse_result: Mapped[str | None] = mapped_column(
        Text, comment="AI 解析结果（JSON 文本）"
    )
    error_message: Mapped[str | None] = mapped_column(
        String(500), comment="解析失败原因"
    )
