"""测试点接口测试：demo 模式生成五类测试点、筛选、编辑、删除。"""
from conftest import get_headers, register_user

REQ_TEXT = """# 图书管理系统
1. 管理员可以维护图书信息（新增、编辑、删除、查询）。
2. 读者可以查询图书、借阅图书、归还图书。
3. 系统支持按书名、作者、分类检索。
"""


def prepare_parsed(client, headers, project_id):
    """上传并解析需求，返回 requirement_id。"""
    resp = client.post(
        f"/api/v1/projects/{project_id}/requirements/upload",
        files={"file": ("需求.md", REQ_TEXT.encode("utf-8"), "text/markdown")},
        headers=headers,
    )
    rid = resp.json()["id"]
    client.post(
        f"/api/v1/projects/{project_id}/requirements/{rid}/parse", headers=headers
    )
    return rid


def generate_points(client, headers, project_id, rid):
    return client.post(
        f"/api/v1/projects/{project_id}/requirements/{rid}/test-points/generate",
        headers=headers,
    )


def test_generate_five_categories(client, project_id, user_headers):
    rid = prepare_parsed(client, user_headers, project_id)
    resp = generate_points(client, user_headers, project_id, rid)
    assert resp.status_code == 200
    points = resp.json()
    assert len(points) >= 5
    categories = {p["category"] for p in points}
    assert {"normal", "exception", "boundary", "security", "compatibility"} <= categories
    assert all(p["name"] for p in points)


def test_generate_without_parse_fallback(client, project_id, user_headers):
    """未解析需求也能生成（服务层有兜底功能点）。"""
    resp = client.post(
        f"/api/v1/projects/{project_id}/requirements/upload",
        files={"file": ("需求.md", REQ_TEXT.encode("utf-8"), "text/markdown")},
        headers=user_headers,
    )
    rid = resp.json()["id"]
    resp = generate_points(client, user_headers, project_id, rid)
    assert resp.status_code == 200
    assert len(resp.json()) > 0


def test_list_test_points(client, project_id, user_headers):
    rid = prepare_parsed(client, user_headers, project_id)
    generate_points(client, user_headers, project_id, rid)
    resp = client.get(
        f"/api/v1/projects/{project_id}/test-points", headers=user_headers
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 5


def test_filter_by_category(client, project_id, user_headers):
    rid = prepare_parsed(client, user_headers, project_id)
    generate_points(client, user_headers, project_id, rid)
    resp = client.get(
        f"/api/v1/projects/{project_id}/test-points",
        params={"category": "security"},
        headers=user_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["total"] > 0
    assert all(p["category"] == "security" for p in resp.json()["items"])


def test_edit_test_point(client, project_id, user_headers):
    rid = prepare_parsed(client, user_headers, project_id)
    generate_points(client, user_headers, project_id, rid)
    pid = project_id
    tp = client.get(
        f"/api/v1/projects/{pid}/test-points", headers=user_headers
    ).json()["items"][0]
    resp = client.patch(
        f"/api/v1/projects/{pid}/test-points/{tp['id']}",
        json={"name": "人工修正后的测试点"},
        headers=user_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "人工修正后的测试点"


def test_delete_test_point(client, project_id, user_headers):
    rid = prepare_parsed(client, user_headers, project_id)
    generate_points(client, user_headers, project_id, rid)
    pid = project_id
    tp = client.get(
        f"/api/v1/projects/{pid}/test-points", headers=user_headers
    ).json()["items"][0]
    before = client.get(
        f"/api/v1/projects/{pid}/test-points", headers=user_headers
    ).json()["total"]
    resp = client.delete(
        f"/api/v1/projects/{pid}/test-points/{tp['id']}", headers=user_headers
    )
    assert resp.status_code == 204
    after = client.get(
        f"/api/v1/projects/{pid}/test-points", headers=user_headers
    ).json()["total"]
    assert after == before - 1
