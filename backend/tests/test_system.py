"""系统管理、测试数据生成器、仪表盘接口测试。"""


def test_generator_auto_identify_username(client, user_headers):
    resp = client.post(
        "/api/v1/generator/test-data",
        json={"field": "username"},
        headers=user_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["field"] == "username"
    assert body["type"] == "username"
    categories = {item["case"] for item in body["data"]}
    assert "正常" in categories and "SQL注入" in categories


def test_generator_requires_auth(client):
    resp = client.post("/api/v1/generator/test-data", json={"field": "username"})
    assert resp.status_code == 401


def test_generator_unknown_type_defaults(client, user_headers):
    resp = client.post(
        "/api/v1/generator/test-data",
        json={"field": "some_random_field"},
        headers=user_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["type"] == "string"


def test_admin_get_settings(client, admin_headers):
    resp = client.get("/api/v1/system/settings", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "ai_provider" in body["settings"]
    assert "prompt_requirement" in body["settings"]


def test_regular_user_forbidden_from_settings(client, user_headers):
    resp = client.get("/api/v1/system/settings", headers=user_headers)
    assert resp.status_code == 403


def test_admin_update_settings(client, admin_headers):
    resp = client.put(
        "/api/v1/system/settings",
        json={"values": {"ai_provider": "demo", "openai_model": "gpt-4o-mini"}},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["settings"]["ai_provider"] == "demo"


def test_dashboard_stats(client, project_id, user_headers):
    resp = client.get("/api/v1/dashboard/stats", headers=user_headers)
    assert resp.status_code == 200
    body = resp.json()
    for key in (
        "project_count",
        "requirement_count",
        "test_point_count",
        "test_case_count",
        "chat_count",
        "recent_projects",
    ):
        assert key in body
    assert body["project_count"] >= 1


def test_operation_logs_recorded(client, project_id, user_headers, admin_headers):
    resp = client.get("/api/v1/system/logs/operations", headers=admin_headers)
    assert resp.status_code == 200
    # 创建项目已写入操作日志
    assert resp.json()["total"] >= 1


def test_ai_call_logs_recorded(client, project_id, user_headers, admin_headers):
    # 走一次解析，生成 AI 调用日志
    upload = client.post(
        f"/api/v1/projects/{project_id}/requirements/upload",
        files={"file": ("需求.md", "# 需求\n1. 功能A\n2. 功能B".encode("utf-8"), "text/markdown")},
        headers=user_headers,
    )
    rid = upload.json()["id"]
    client.post(
        f"/api/v1/projects/{project_id}/requirements/{rid}/parse",
        headers=user_headers,
    )
    resp = client.get("/api/v1/system/logs/ai", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
    assert resp.json()["items"][0]["agent"] == "Requirement"
