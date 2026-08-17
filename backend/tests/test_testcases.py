"""测试用例接口测试：demo 模式生成、编号规则、编辑删除、Excel 导出。"""
REQ_TEXT = """# 图书管理系统
1. 管理员可以维护图书信息（新增、编辑、删除、查询）。
2. 读者可以查询图书、借阅图书、归还图书。
3. 系统支持按书名、作者、分类检索。
"""


def prepare_generated(client, headers, project_id):
    """上传 → 解析 → 生成测试点 → 生成测试用例，返回测试点/用例数据。"""
    upload = client.post(
        f"/api/v1/projects/{project_id}/requirements/upload",
        files={"file": ("需求.md", REQ_TEXT.encode("utf-8"), "text/markdown")},
        headers=headers,
    )
    rid = upload.json()["id"]
    client.post(
        f"/api/v1/projects/{project_id}/requirements/{rid}/parse", headers=headers
    )
    client.post(
        f"/api/v1/projects/{project_id}/requirements/{rid}/test-points/generate",
        headers=headers,
    )
    resp = client.post(
        f"/api/v1/projects/{project_id}/requirements/{rid}/test-cases/generate",
        headers=headers,
    )
    return rid, resp


def test_generate_test_cases(client, project_id, user_headers):
    rid, resp = prepare_generated(client, user_headers, project_id)
    assert resp.status_code == 200
    cases = resp.json()
    assert len(cases) >= 5
    for case in cases:
        assert case["case_no"].startswith("TC")
        assert case["case_no"][2:].isdigit()
        assert case["priority"] in ("高", "中", "低")
        assert case["title"]
        assert case["steps"]


def test_case_no_sequential(client, project_id, user_headers):
    rid, resp = prepare_generated(client, user_headers, project_id)
    numbers = [int(c["case_no"][2:]) for c in resp.json()]
    assert numbers == sorted(numbers)
    assert numbers[0] == 1
    assert numbers == list(range(1, len(numbers) + 1))


def test_generate_without_test_points_returns_400(client, project_id, user_headers):
    upload = client.post(
        f"/api/v1/projects/{project_id}/requirements/upload",
        files={"file": ("需求.md", REQ_TEXT.encode("utf-8"), "text/markdown")},
        headers=user_headers,
    )
    rid = upload.json()["id"]
    resp = client.post(
        f"/api/v1/projects/{project_id}/requirements/{rid}/test-cases/generate",
        headers=user_headers,
    )
    assert resp.status_code == 400


def test_list_test_cases(client, project_id, user_headers):
    prepare_generated(client, user_headers, project_id)
    resp = client.get(
        f"/api/v1/projects/{project_id}/test-cases", headers=user_headers
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 5


def test_filter_test_cases_by_priority(client, project_id, user_headers):
    prepare_generated(client, user_headers, project_id)
    resp = client.get(
        f"/api/v1/projects/{project_id}/test-cases",
        params={"priority": "高"},
        headers=user_headers,
    )
    assert resp.status_code == 200
    assert all(c["priority"] == "高" for c in resp.json()["items"])


def test_edit_test_case(client, project_id, user_headers):
    prepare_generated(client, user_headers, project_id)
    pid = project_id
    case = client.get(
        f"/api/v1/projects/{pid}/test-cases", headers=user_headers
    ).json()["items"][0]
    resp = client.patch(
        f"/api/v1/projects/{pid}/test-cases/{case['id']}",
        json={"expected_result": "人工修订后的预期结果"},
        headers=user_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["expected_result"] == "人工修订后的预期结果"


def test_delete_test_case(client, project_id, user_headers):
    prepare_generated(client, user_headers, project_id)
    pid = project_id
    case = client.get(
        f"/api/v1/projects/{pid}/test-cases", headers=user_headers
    ).json()["items"][0]
    before = client.get(
        f"/api/v1/projects/{pid}/test-cases", headers=user_headers
    ).json()["total"]
    resp = client.delete(
        f"/api/v1/projects/{pid}/test-cases/{case['id']}", headers=user_headers
    )
    assert resp.status_code == 204
    after = client.get(
        f"/api/v1/projects/{pid}/test-cases", headers=user_headers
    ).json()["total"]
    assert after == before - 1


def test_export_excel(client, project_id, user_headers):
    prepare_generated(client, user_headers, project_id)
    resp = client.get(
        f"/api/v1/projects/{project_id}/test-cases/export", headers=user_headers
    )
    assert resp.status_code == 200
    # xlsx 文件魔数 PK\x03\x04
    assert resp.content[:4] == b"PK\x03\x04"
    assert "spreadsheetml" in resp.headers["content-type"]


def test_regenerate_replaces_old_cases(client, project_id, user_headers):
    rid, first = prepare_generated(client, user_headers, project_id)
    second = client.post(
        f"/api/v1/projects/{project_id}/requirements/{rid}/test-cases/generate",
        headers=user_headers,
    )
    assert second.status_code == 200
    total = client.get(
        f"/api/v1/projects/{project_id}/test-cases", headers=user_headers
    ).json()["total"]
    # 重新生成会先删除旧用例，数量不翻倍
    assert total == len(second.json())
