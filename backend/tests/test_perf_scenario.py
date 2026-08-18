"""性能测试场景模块测试：场景 CRUD、导出 JMeter 压测脚本。"""
import xml.etree.ElementTree as ET


def _create_project(client, headers, name="压测项目"):
    resp = client.post(
        "/api/v1/projects", json={"name": name}, headers=headers
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_interface(client, project_id, headers, **overrides):
    payload = {
        "name": "健康检查",
        "method": "GET",
        "path": "/api/v1/health",
        **overrides,
    }
    return client.post(
        f"/api/v1/projects/{project_id}/interfaces",
        json=payload,
        headers=headers,
    )


def _create_scenario(client, project_id, headers, **overrides):
    payload = {
        "name": "100 并发压测",
        "description": "负载测试",
        "thread_count": 100,
        "loop_count": 50,
        "ramp_up": 30,
        "think_time_ms": 800,
        "base_url": "localhost",
        "base_port": "8000",
        **overrides,
    }
    return client.post(
        f"/api/v1/projects/{project_id}/perf-scenarios",
        json=payload,
        headers=headers,
    )


def test_create_scenario(client, user_headers):
    pid = _create_project(client, user_headers)
    resp = _create_scenario(client, pid, user_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "100 并发压测"
    assert body["thread_count"] == 100
    assert body["loop_count"] == 50
    assert body["ramp_up"] == 30
    assert body["think_time_ms"] == 800
    assert body["base_url"] == "localhost"
    assert body["interface_ids"] == []


def test_list_scenarios_with_search(client, user_headers):
    pid = _create_project(client, user_headers)
    _create_scenario(client, pid, user_headers)
    _create_scenario(client, pid, user_headers, name="登录接口压测")
    resp = client.get(
        f"/api/v1/projects/{pid}/perf-scenarios", headers=user_headers
    )
    assert resp.json()["total"] == 2
    resp = client.get(
        f"/api/v1/projects/{pid}/perf-scenarios",
        params={"keyword": "登录"},
        headers=user_headers,
    )
    assert resp.json()["total"] == 1


def test_update_scenario(client, user_headers):
    pid = _create_project(client, user_headers)
    sid = _create_scenario(client, pid, user_headers).json()["id"]
    resp = client.patch(
        f"/api/v1/projects/{pid}/perf-scenarios/{sid}",
        json={"thread_count": 500, "think_time_ms": 0},
        headers=user_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["thread_count"] == 500
    assert body["think_time_ms"] == 0


def test_delete_scenario(client, user_headers):
    pid = _create_project(client, user_headers)
    sid = _create_scenario(client, pid, user_headers).json()["id"]
    resp = client.delete(
        f"/api/v1/projects/{pid}/perf-scenarios/{sid}",
        headers=user_headers,
    )
    assert resp.status_code == 204
    resp = client.get(
        f"/api/v1/projects/{pid}/perf-scenarios/{sid}",
        headers=user_headers,
    )
    assert resp.status_code == 404


def test_export_scenario_jmeter(client, user_headers):
    """导出压测脚本：线程组参数来自场景、含思考时间、sampler 正确。"""
    pid = _create_project(client, user_headers)
    _create_interface(client, pid, user_headers)
    client.post(
        f"/api/v1/projects/{pid}/interfaces/generate-cases",
        json={},
        headers=user_headers,
    )
    sid = _create_scenario(client, pid, user_headers).json()["id"]
    resp = client.get(
        f"/api/v1/projects/{pid}/perf-scenarios/{sid}/export/jmeter",
        headers=user_headers,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/xml")
    root = ET.fromstring(resp.content)
    assert root.tag == "jmeterTestPlan"
    text = resp.content.decode("utf-8")
    # 线程组参数来自场景配置
    assert 'ThreadGroup.num_threads">100<' in text
    assert 'LoopController.loops">50<' in text
    assert 'ThreadGroup.ramp_time">30<' in text
    # 思考时间 Constant Timer
    assert "ConstantTimer" in text
    assert 'ConstantTimer.delay">800<' in text
    # 5 类用例 → 5 个 sampler
    assert text.count('testclass="HTTPSamplerProxy"') == 5
    # 树结构（官方约定）
    assert '</HTTPSamplerProxy><hashTree>' in text
    # guiclass 官方值
    assert 'guiclass="ArgumentsPanel"' in text
    assert 'guiclass="ThreadGroupGui"' in text
    # 场景 base_url 变量
    assert "base_url" in text


def test_export_scenario_no_cases(client, user_headers):
    """没有接口用例时导出应报 400。"""
    pid = _create_project(client, user_headers)
    sid = _create_scenario(client, pid, user_headers).json()["id"]
    resp = client.get(
        f"/api/v1/projects/{pid}/perf-scenarios/{sid}/export/jmeter",
        headers=user_headers,
    )
    assert resp.status_code == 400


def test_scenario_permission_isolation(client):
    """用户 B 不能访问用户 A 项目下的场景（404 防泄露）。"""
    from conftest import get_headers, register_user

    register_user(client, "user_a", "pass12345")
    register_user(client, "user_b", "pass12345")
    headers_a = get_headers(client, "user_a", "pass12345")
    headers_b = get_headers(client, "user_b", "pass12345")
    pid = _create_project(client, headers_a, name="A的项目")
    sid = _create_scenario(client, pid, headers_a).json()["id"]
    resp = client.get(
        f"/api/v1/projects/{pid}/perf-scenarios/{sid}",
        headers=headers_b,
    )
    assert resp.status_code == 404
