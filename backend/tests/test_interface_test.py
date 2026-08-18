"""接口测试模块测试：接口 CRUD、OpenAPI 导入、接口用例生成与导出。"""
from conftest import get_headers, register_user


def _create_project(client, headers, name="接口项目"):
    resp = client.post(
        "/api/v1/projects", json={"name": name}, headers=headers
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_interface(client, project_id, headers, **overrides):
    payload = {
        "name": "用户搜索",
        "method": "GET",
        "path": "/api/users/search",
        "summary": "按关键词搜索用户",
        **overrides,
    }
    return client.post(
        f"/api/v1/projects/{project_id}/interfaces",
        json=payload,
        headers=headers,
    )


def test_create_interface(client, user_headers):
    pid = _create_project(client, user_headers)
    resp = _create_interface(client, pid, user_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "用户搜索"
    assert body["method"] == "GET"
    assert body["path"] == "/api/users/search"


def test_list_interfaces_with_search(client, user_headers):
    pid = _create_project(client, user_headers)
    _create_interface(client, pid, user_headers)
    _create_interface(
        client, pid, user_headers,
        name="创建用户", method="POST", path="/api/users",
    )
    resp = client.get(
        f"/api/v1/projects/{pid}/interfaces", headers=user_headers
    )
    assert resp.json()["total"] == 2
    resp = client.get(
        f"/api/v1/projects/{pid}/interfaces",
        params={"keyword": "用户搜索"},
        headers=user_headers,
    )
    assert resp.json()["total"] == 1


def test_update_interface(client, user_headers):
    pid = _create_project(client, user_headers)
    iid = _create_interface(client, pid, user_headers).json()["id"]
    resp = client.patch(
        f"/api/v1/projects/{pid}/interfaces/{iid}",
        json={"summary": "新描述", "method": "POST"},
        headers=user_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["summary"] == "新描述"
    assert resp.json()["method"] == "POST"


def test_delete_interface(client, user_headers):
    pid = _create_project(client, user_headers)
    iid = _create_interface(client, pid, user_headers).json()["id"]
    resp = client.delete(
        f"/api/v1/projects/{pid}/interfaces/{iid}", headers=user_headers
    )
    assert resp.status_code == 204
    resp = client.get(f"/api/v1/projects/{pid}/interfaces", headers=user_headers)
    assert resp.json()["total"] == 0


def test_import_openapi(client, user_headers):
    pid = _create_project(client, user_headers)
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "示例", "version": "1.0.0"},
        "paths": {
            "/api/users": {
                "get": {"summary": "用户列表"},
                "post": {"summary": "创建用户"},
            },
            "/api/users/{id}": {
                "get": {"summary": "用户详情"},
                "delete": {"summary": "删除用户"},
            },
        },
    }
    resp = client.post(
        f"/api/v1/projects/{pid}/interfaces/import-openapi",
        json={"spec": spec},
        headers=user_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 4
    methods = {item["method"] for item in resp.json()["items"]}
    assert methods == {"GET", "POST", "DELETE"}


def test_import_openapi_invalid(client, user_headers):
    pid = _create_project(client, user_headers)
    resp = client.post(
        f"/api/v1/projects/{pid}/interfaces/import-openapi",
        json={"spec": {"openapi": "3.0.0"}},
        headers=user_headers,
    )
    assert resp.status_code == 400


def test_generate_interface_cases_demo(client, user_headers):
    """demo 模式：3 个接口应生成 3×5=15 条用例。"""
    pid = _create_project(client, user_headers)
    _create_interface(client, pid, user_headers, path="/api/users/search")
    _create_interface(
        client, pid, user_headers, name="创建用户", method="POST", path="/api/users"
    )
    _create_interface(
        client, pid, user_headers, name="用户详情", path="/api/users/{id}"
    )
    resp = client.post(
        f"/api/v1/projects/{pid}/interfaces/generate-cases",
        json={},
        headers=user_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 15
    categories = {item["category"] for item in body["items"]}
    assert categories == {"normal", "exception", "boundary", "security", "parameter"}
    # 编号连续：API0001 起
    case_nos = [item["case_no"] for item in body["items"]]
    assert case_nos == [f"API{i:04d}" for i in range(1, 16)]


def test_generate_interface_cases_empty(client, user_headers):
    pid = _create_project(client, user_headers)
    resp = client.post(
        f"/api/v1/projects/{pid}/interfaces/generate-cases",
        json={},
        headers=user_headers,
    )
    assert resp.status_code == 400
    assert "接口" in resp.json()["detail"]


def test_list_interface_cases_with_filter(client, user_headers):
    pid = _create_project(client, user_headers)
    _create_interface(client, pid, user_headers)
    _create_interface(
        client, pid, user_headers, name="创建用户", method="POST", path="/api/users"
    )
    client.post(
        f"/api/v1/projects/{pid}/interfaces/generate-cases",
        json={},
        headers=user_headers,
    )
    resp = client.get(
        f"/api/v1/projects/{pid}/interface-cases", headers=user_headers
    )
    assert resp.json()["total"] == 10
    resp = client.get(
        f"/api/v1/projects/{pid}/interface-cases",
        params={"category": "security"},
        headers=user_headers,
    )
    assert resp.json()["total"] == 2
    resp = client.get(
        f"/api/v1/projects/{pid}/interface-cases",
        params={"keyword": "正常调用"},
        headers=user_headers,
    )
    assert resp.json()["total"] == 2


def test_update_interface_case(client, user_headers):
    pid = _create_project(client, user_headers)
    _create_interface(client, pid, user_headers)
    client.post(
        f"/api/v1/projects/{pid}/interfaces/generate-cases",
        json={},
        headers=user_headers,
    )
    case = client.get(
        f"/api/v1/projects/{pid}/interface-cases", headers=user_headers
    ).json()["items"][0]
    resp = client.patch(
        f"/api/v1/projects/{pid}/interface-cases/{case['id']}",
        json={"priority": "高", "title": "人工修改标题"},
        headers=user_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["priority"] == "高"
    assert resp.json()["title"] == "人工修改标题"


def test_delete_interface_case(client, user_headers):
    pid = _create_project(client, user_headers)
    _create_interface(client, pid, user_headers)
    client.post(
        f"/api/v1/projects/{pid}/interfaces/generate-cases",
        json={},
        headers=user_headers,
    )
    case = client.get(
        f"/api/v1/projects/{pid}/interface-cases", headers=user_headers
    ).json()["items"][0]
    resp = client.delete(
        f"/api/v1/projects/{pid}/interface-cases/{case['id']}",
        headers=user_headers,
    )
    assert resp.status_code == 204
    resp = client.get(
        f"/api/v1/projects/{pid}/interface-cases", headers=user_headers
    )
    assert resp.json()["total"] == 4


def test_export_interface_cases_excel(client, user_headers):
    pid = _create_project(client, user_headers)
    _create_interface(client, pid, user_headers)
    client.post(
        f"/api/v1/projects/{pid}/interfaces/generate-cases",
        json={},
        headers=user_headers,
    )
    resp = client.get(
        f"/api/v1/projects/{pid}/interface-cases/export", headers=user_headers
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith(
        "application/vnd.openxmlformats"
    )
    # xlsx 文件以 PK 开头（ZIP 魔数）
    assert resp.content[:2] == b"PK"


def test_interface_permission_isolation(client):
    """用户 B 不能访问用户 A 项目下的接口。"""
    register_user(client, "user_a", "pass12345")
    register_user(client, "user_b", "pass12345")
    headers_a = get_headers(client, "user_a", "pass12345")
    headers_b = get_headers(client, "user_b", "pass12345")
    pid = client.post(
        "/api/v1/projects", json={"name": "A的项目"}, headers=headers_a
    ).json()["id"]
    _create_interface(client, pid, headers_a)
    resp = client.get(
        f"/api/v1/projects/{pid}/interfaces", headers=headers_b
    )
    # 越权访问他人项目返回 404（不泄露项目存在性，与全项目约定一致）
    assert resp.status_code == 404
