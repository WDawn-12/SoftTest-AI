"""接口测试用例模型（接口测试模块）。"""
from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class InterfaceTestCase(Base, TimestampMixin):
    """接口测试用例表（AI 生成，支持人工编辑）。"""

    __tablename__ = "interface_test_cases"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="接口用例ID"
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="所属项目ID",
    )
    interface_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("interfaces.id", ondelete="SET NULL"),
        index=True,
        comment="来源接口ID",
    )
    case_no: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="用例编号（API0001）"
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="用例标题"
    )
    category: Mapped[str] = mapped_column(
        String(50),
        default="normal",
        comment="类别：normal/exception/boundary/security/parameter",
    )
    method: Mapped[str] = mapped_column(
        String(10), default="GET", nullable=False, comment="请求方法"
    )
    path: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="请求路径"
    )
    test_data: Mapped[str | None] = mapped_column(Text, comment="测试数据")
    request_payload: Mapped[str | None] = mapped_column(
        Text, comment="请求参数/请求体"
    )
    expected_status: Mapped[str | None] = mapped_column(
        String(50), comment="预期状态码"
    )
    expected_result: Mapped[str | None] = mapped_column(Text, comment="预期结果")
    priority: Mapped[str] = mapped_column(
        String(10), default="中", comment="优先级：高/中/低"
    )
    preconditions: Mapped[str | None] = mapped_column(Text, comment="前置条件")
    steps: Mapped[str | None] = mapped_column(Text, comment="测试步骤")
    remark: Mapped[str | None] = mapped_column(Text, comment="备注")
    status: Mapped[str] = mapped_column(String(20), default="draft", comment="状态")
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, comment="创建人"
    )
