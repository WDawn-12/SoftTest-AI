"""数据库引擎与会话管理（SQLAlchemy）。"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 连接复用前自动探测有效性
    pool_recycle=3600,  # 防止 MySQL 服务端空闲连接被回收
    echo=settings.DEBUG,
)

# 会话工厂：每个请求使用独立会话
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """FastAPI 依赖：提供数据库会话并在请求结束后关闭。"""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
