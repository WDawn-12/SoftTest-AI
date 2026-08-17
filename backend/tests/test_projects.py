"""项目管理接口测试：CRUD、分页、搜索、权限隔离。"""
from conftest import get_headers, register_user


def test_create_project(client, user_headers):
    resp = client.post(
        "/api/v1/projects",
        json={"name": "电商平台", "description": "核心交易流程"},
        headers=user_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "电商平台"
    assert body["status"] == "active"


def test_create_project_requires_auth(client):
    resp = client.post("/api/v1/projects", json={"name": "未登录"})
    assert resp.status_code == 401


def test_list_projects(client, user_headers):
    for i in range(3):
        client.post("/api/v1/projects", json={"name": f"项目{i}"}, headers=user_headers)
    resp = client.get("/api/v1/projects", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 3
    assert len(resp.json()["items"]) == 3


def test_search_projects(client, user_headers):
    client.post("/api/v1/projects", json={"name": "图书管理系统"}, headers=user_headers)
    client.post("/api/v1/projects", json={"name": "电商平台"}, headers=user_headers)
    resp = client.get(
        "/api/v1/projects", params={"keyword": "图书"}, headers=user_headers
    )
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["name"] == "图书管理系统"


def test_get_project_detail(client, user_headers):
    pid = client.post(
        "/api/v1/projects", json={"name": "商城"}, headers=user_headers
    ).json()["id"]
    resp = client.get(f"/api/v1/projects/{pid}", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "商城"


def test_update_project(client, user_headers):
    pid = client.post(
        "/api/v1/projects", json={"name": "旧名"}, headers=user_headers
    ).json()["id"]
    resp = client.patch(
        f"/api/v1/projects/{pid}", json={"name": "新名"}, headers=user_headers
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "新名"


def test_delete_project(client, user_headers):
    pid = client.post(
        "/api/v1/projects", json={"name": "待删"}, headers=user_headers
    ).json()["id"]
    resp = client.delete(f"/api/v1/projects/{pid}", headers=user_headers)
    assert resp.status_code == 204
    assert (
        client.get(f"/api/v1/projects/{pid}", headers=user_headers).status_code == 404
    )


def test_project_not_found(client, user_headers):
    resp = client.get("/api/v1/projects/99999", headers=user_headers)
    assert resp.status_code == 404


def test_user_cannot_access_others_project(client):
    register_user(client, username="user_a", password="pass123456")
    headers_a = get_headers(client, "user_a", "pass123456")
    pid = client.post(
        "/api/v1/projects", json={"name": "A的项目"}, headers=headers_a
    ).json()["id"]

    register_user(client, username="user_b", password="pass123456")
    headers_b = get_headers(client, "user_b", "pass123456")
    # 越权访问他人项目应返回 404（不泄露项目存在性）
    assert client.get(f"/api/v1/projects/{pid}", headers=headers_b).status_code == 404
    assert client.get("/api/v1/projects", headers=headers_b).json()["total"] == 0


def test_admin_can_see_all_projects(client, admin_headers):
    register_user(client, username="someone", password="pass123456")
    headers = get_headers(client, "someone", "pass123456")
    client.post("/api/v1/projects", json={"name": "别人的"}, headers=headers)
    resp = client.get("/api/v1/projects", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
