"""测试用例模型。"""
from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class TestCase(Base, TimestampMixin):
    """测试用例表（字段与 Excel 导出格式一一对应）。"""

    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="用例ID"
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="所属项目ID",
    )
    module_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("modules.id", ondelete="SET NULL"),
        index=True,
        comment="所属模块ID",
    )
    case_no: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="用例编号"
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="功能名称"
    )
    test_point: Mapped[str | None] = mapped_column(
        String(500), comment="测试点"
    )
    priority: Mapped[str] = mapped_column(
        String(20), default="中", comment="优先级：高/中/低"
    )
    preconditions: Mapped[str | None] = mapped_column(Text, comment="前置条件")
    steps: Mapped[str | None] = mapped_column(Text, comment="测试步骤")
    expected_result: Mapped[str | None] = mapped_column(Text, comment="预期结果")
    remark: Mapped[str | None] = mapped_column(String(500), comment="备注")
    status: Mapped[str] = mapped_column(
        String(20), default="draft", comment="状态：draft/approved"
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="创建人用户ID",
    )
