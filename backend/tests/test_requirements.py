"""需求文档接口测试：上传、列表、解析（demo 模式）、详情、删除。"""
from conftest import get_headers, register_user

REQ_TEXT = """# 图书管理系统

1. 管理员可以维护图书信息（新增、编辑、删除、查询）。
2. 读者可以查询图书、借阅图书、归还图书。
3. 系统支持按书名、作者、分类检索。
4. 图书借出后库存自动扣减，归还后恢复。
"""


def upload(client, headers, project_id, content=REQ_TEXT, filename="需求.md"):
    """上传一个 markdown 需求文档。"""
    return client.post(
        f"/api/v1/projects/{project_id}/requirements/upload",
        files={"file": (filename, content.encode("utf-8"), "text/markdown")},
        headers=headers,
    )


def test_upload_markdown(client, project_id, user_headers):
    resp = upload(client, user_headers, project_id)
    assert resp.status_code == 201
    body = resp.json()
    assert body["file_name"] == "需求.md"
    assert body["file_type"] == "md"
    assert body["parse_status"] == "pending"
    assert body["file_size"] > 0


def test_upload_txt(client, project_id, user_headers):
    resp = client.post(
        f"/api/v1/projects/{project_id}/requirements/upload",
        files={"file": ("需求.txt", "纯文本需求内容".encode("utf-8"), "text/plain")},
        headers=user_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["file_type"] == "txt"


def test_upload_invalid_extension(client, project_id, user_headers):
    resp = client.post(
        f"/api/v1/projects/{project_id}/requirements/upload",
        files={"file": ("evil.exe", b"MZ...", "application/octet-stream")},
        headers=user_headers,
    )
    assert resp.status_code == 400


def test_upload_requires_auth(client, project_id):
    resp = client.post(
        f"/api/v1/projects/{project_id}/requirements/upload",
        files={"file": ("a.md", b"x", "text/markdown")},
    )
    assert resp.status_code == 401


def test_list_requirements(client, project_id, user_headers):
    upload(client, user_headers, project_id)
    upload(client, user_headers, project_id, filename="第二个需求.md")
    resp = client.get(
        f"/api/v1/projects/{project_id}/requirements", headers=user_headers
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_requirement_detail_contains_content(client, project_id, user_headers):
    rid = upload(client, user_headers, project_id).json()["id"]
    resp = client.get(
        f"/api/v1/projects/{project_id}/requirements/{rid}", headers=user_headers
    )
    assert resp.status_code == 200
    assert "图书管理系统" in (resp.json()["content"] or "")


def test_parse_requirement_demo(client, project_id, user_headers):
    rid = upload(client, user_headers, project_id).json()["id"]
    resp = client.post(
        f"/api/v1/projects/{project_id}/requirements/{rid}/parse",
        headers=user_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["parse_status"] == "completed"
    result = body["result"]
    assert result is not None
    assert len(result["modules"]) >= 3
    assert len(result["roles"]) >= 2
    assert len(result["business_flows"]) >= 2
    assert len(result["risks"]) >= 3


def test_parse_result_endpoint(client, project_id, user_headers):
    rid = upload(client, user_headers, project_id).json()["id"]
    client.post(
        f"/api/v1/projects/{project_id}/requirements/{rid}/parse",
        headers=user_headers,
    )
    resp = client.get(
        f"/api/v1/projects/{project_id}/requirements/{rid}/parse-result",
        headers=user_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["result"] is not None


def test_delete_requirement(client, project_id, user_headers):
    rid = upload(client, user_headers, project_id).json()["id"]
    resp = client.delete(
        f"/api/v1/projects/{project_id}/requirements/{rid}", headers=user_headers
    )
    assert resp.status_code == 204
    resp = client.get(
        f"/api/v1/projects/{project_id}/requirements", headers=user_headers
    )
    assert resp.json()["total"] == 0


def test_requirement_cross_project_isolation(client):
    """A 用户不能访问 B 用户项目下的需求。"""
    register_user(client, username="user_a", password="pass123456")
    headers_a = get_headers(client, "user_a", "pass123456")
    pid_a = client.post(
        "/api/v1/projects", json={"name": "A项目"}, headers=headers_a
    ).json()["id"]
    upload(client, headers_a, pid_a)

    register_user(client, username="user_b", password="pass123456")
    headers_b = get_headers(client, "user_b", "pass123456")
    assert (
        client.get(f"/api/v1/projects/{pid_a}/requirements", headers=headers_b).status_code
        == 404
    )
