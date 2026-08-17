"""pytest 全局夹具：SQLite 测试库 + API 客户端 + 认证辅助。

关键设计：
- 环境变量必须在导入任何 app 模块之前设置（settings 是模块级单例，带 lru_cache）；
- 通过 dependency_overrides 把 get_db 指向测试库，不触碰真实 MySQL；
- 每个测试结束后清空所有表，保证用例相互隔离；
- AI 使用 demo 模式，全程不需要 API Key。
"""
import os
import tempfile

_TMP_DIR = tempfile.mkdtemp(prefix="aitest_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_TMP_DIR, 'test.db')}"
os.environ["AI_PROVIDER"] = "demo"
os.environ["DEBUG"] = "false"
os.environ["UPLOAD_DIR"] = os.path.join(_TMP_DIR, "uploads")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

# SQLite 只对 INTEGER PRIMARY KEY 自增，BIGINT 不会；
# 测试库编译时把 BigInteger 降级为 INTEGER，兼容生产环境的 BIGINT 主键模型
@compiles(BigInteger, "sqlite")
def _compile_bigint_sqlite(type_, compiler, **kw):
    return "INTEGER"

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User

engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def _init_db():
    """会话级：创建全部数据表（会话结束自动清理）。"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _override_get_db():
    """FastAPI 依赖覆盖：请求期间使用测试库会话。"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture()
def client():
    """FastAPI 测试客户端。"""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db():
    """可直接操作测试库的会话。"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _clean_tables(db):
    """每个测试结束后清空所有表，保证用例隔离。"""
    yield
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()


# ---------- 认证辅助 ----------


def register_user(client, username="testuser", password="testpass123", **extra):
    """注册一个普通用户。"""
    return client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password, **extra},
    )


def login(client, username, password):
    """用户名密码登录（OAuth2 表单）。"""
    return client.post(
        "/api/v1/auth/login", data={"username": username, "password": password}
    )


def get_headers(client, username="testuser", password="testpass123"):
    """登录并返回携带 JWT 的请求头。"""
    token = login(client, username, password).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def user_headers(client):
    """注册并登录一个普通用户，返回携带 JWT 的请求头。"""
    resp = register_user(client)
    assert resp.status_code == 201
    return get_headers(client)


@pytest.fixture()
def admin_headers(client, db):
    """直插一个管理员账号并登录，返回携带 JWT 的请求头。"""
    db.add(
        User(
            username="admin01",
            password_hash=hash_password("adminpass123"),
            nickname="Admin",
            role="admin",
            status=1,
        )
    )
    db.commit()
    return get_headers(client, "admin01", "adminpass123")


@pytest.fixture()
def project_id(client, user_headers):
    """创建并返回一个测试项目 ID。"""
    resp = client.post(
        "/api/v1/projects", json={"name": "图书管理系统"}, headers=user_headers
    )
    assert resp.status_code == 201
    return resp.json()["id"]
