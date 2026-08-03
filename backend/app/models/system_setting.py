"""系统设置模型。"""
from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class SystemSetting(Base, TimestampMixin):
    """系统设置表（模型配置、API Key、Prompt 模板等）。"""

    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="设置ID"
    )
    setting_key: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False, comment="配置键"
    )
    setting_value: Mapped[str | None] = mapped_column(Text, comment="配置值")
    description: Mapped[str | None] = mapped_column(String(255), comment="配置说明")
