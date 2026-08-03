"""应用配置：从环境变量 / .env 文件读取。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置项。"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 应用信息
    APP_NAME: str = "AITestAgent"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # 数据库连接串（SQLAlchemy 格式）
    DATABASE_URL: str = (
        "mysql+pymysql://aitest:aitest123456@127.0.0.1:3306/aitest_agent?charset=utf8mb4"
    )

    # CORS 允许的前端来源
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:80"]

    # JWT 密钥（第二阶段登录功能使用，生产环境务必修改）
    SECRET_KEY: str = "please-change-me-in-production"

    # JWT 配置
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 令牌有效期：默认 1 天

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"  # 上传文件保存目录（相对后端运行目录）
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # 单文件大小上限：20MB


@lru_cache
def get_settings() -> Settings:
    """获取全局配置（带缓存，避免重复读取文件）。"""
    return Settings()


# 模块级单例：业务代码直接引用
settings = get_settings()
