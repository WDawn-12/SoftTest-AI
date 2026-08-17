"""认证接口测试：注册、登录、令牌校验、权限隔离。"""
from conftest import get_headers, login, register_user


def test_register_success(client):
    resp = register_user(client, username="alice", password="secret123")
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "alice"
    assert body["role"] == "user"
    # 密码哈希绝不能出现在响应中
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_username(client):
    register_user(client, username="alice")
    resp = register_user(client, username="alice")
    assert resp.status_code == 400
    assert "已存在" in resp.json()["detail"]


def test_register_short_password_rejected(client):
    resp = register_user(client, username="bob", password="123")
    assert resp.status_code == 422


def test_login_success(client):
    register_user(client, username="alice", password="secret123")
    resp = login(client, "alice", "secret123")
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "alice"


def test_login_wrong_password(client):
    register_user(client, username="alice", password="secret123")
    resp = login(client, "alice", "wrong-pass")
    assert resp.status_code == 401


def test_login_unknown_user(client):
    resp = login(client, "nobody", "whatever123")
    assert resp.status_code == 401


def test_disabled_user_login_forbidden(client, db):
    from app.core.security import hash_password
    from app.models.user import User

    db.add(
        User(
            username="blocked",
            password_hash=hash_password("pass12345"),
            role="user",
            status=0,
        )
    )
    db.commit()
    resp = login(client, "blocked", "pass12345")
    assert resp.status_code == 403


def test_me_returns_current_user(client, user_headers):
    resp = client.get("/api/v1/users/me", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


def test_me_requires_token(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_admin_can_list_users(client, admin_headers):
    register_user(client, username="alice")
    resp = client.get("/api/v1/users", headers=admin_headers)
    assert resp.status_code == 200
    names = [u["username"] for u in resp.json()]
    assert "alice" in names


def test_regular_user_cannot_list_users(client, user_headers):
    resp = client.get("/api/v1/users", headers=user_headers)
    assert resp.status_code == 403


def test_admin_can_disable_user(client, admin_headers, db):
    from app.models.user import User

    register_user(client, username="alice", password="secret123")
    uid = db.query(User).filter(User.username == "alice").one().id
    resp = client.patch(
        f"/api/v1/users/{uid}/status", json={"status": 0}, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == 0
    # 禁用后无法登录
    assert login(client, "alice", "secret123").status_code == 403
