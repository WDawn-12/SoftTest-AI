"""性能测试场景模型。"""
from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class PerfScenario(Base, TimestampMixin):
    """性能测试场景表：配置并发/循环/ramp-up/思考时间/目标地址与接口选择。"""

    __tablename__ = "perf_scenarios"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="场景ID"
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="所属项目ID",
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="场景名称")
    description: Mapped[str | None] = mapped_column(
        String(500), comment="场景描述"
    )
    thread_count: Mapped[int] = mapped_column(
        Integer, default=50, nullable=False, comment="并发用户数"
    )
    loop_count: Mapped[int] = mapped_column(
        Integer, default=10, nullable=False, comment="循环次数"
    )
    ramp_up: Mapped[int] = mapped_column(
        Integer, default=10, nullable=False, comment="启动时间（秒）"
    )
    think_time_ms: Mapped[int] = mapped_column(
        Integer, default=500, nullable=False, comment="思考时间（毫秒）"
    )
    base_url: Mapped[str] = mapped_column(
        String(200), default="localhost", nullable=False, comment="目标主机/IP"
    )
    base_port: Mapped[str] = mapped_column(
        String(10), default="8000", nullable=False, comment="目标端口"
    )
    interface_ids: Mapped[str | None] = mapped_column(
        Text, comment="关联接口ID列表（JSON 数组，空=全部接口）"
    )
