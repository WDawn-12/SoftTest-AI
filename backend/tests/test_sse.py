"""SSE 流式接口测试：需求解析 / 测试点 / 测试用例 / AI 聊天。

验证事件流格式（event/data 结构）与结果内容，demo 模式无需 API Key。
"""
import json

REQ_TEXT = """# 图书管理系统

1. 管理员可以维护图书信息（新增、编辑、删除、查询）。
2. 读者可以查询图书、借阅图书、归还图书。
3. 系统支持按书名、作者、分类检索。
4. 图书借出后库存自动扣减，归还后恢复。
"""


def upload_requirement(client, headers, project_id, content=REQ_TEXT):
    """上传一个 markdown 需求文档。"""
    return client.post(
        f"/api/v1/projects/{project_id}/requirements/upload",
        files={"file": ("需求.md", content.encode("utf-8"), "text/markdown")},
        headers=headers,
    )


def parse_sse_events(text: str) -> list[tuple[str, object]]:
    """把 SSE 响应文本解析为 (event, data) 列表。"""
    events = []
    for block in text.strip().split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event, data = "message", ""
        for line in block.splitlines():
            if line.startswith("event:"):
                event = line[len("event:") :].strip()
            elif line.startswith("data:"):
                data = line[len("data:") :].strip()
        if data.startswith("{") or data.startswith("["):
            data = json.loads(data)
        events.append((event, data))
    return events


def get_stream(client, headers, url):
    """发起 SSE 请求，返回 (响应对象, 事件列表)。"""
    resp = client.post(url, headers=headers)
    return resp, parse_sse_events(resp.text)


def test_parse_stream(client, project_id, user_headers):
    """需求解析流式接口：status -> result。"""
    req = upload_requirement(client, user_headers, project_id)
    rid = req.json()["id"]

    resp, events = get_stream(
        client,
        user_headers,
        f"/api/v1/projects/{project_id}/requirements/{rid}/parse/stream",
    )
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("text/event-stream")

    names = [e for e, _ in events]
    assert "status" in names and "result" in names
    # 阶段进度包含 llm 阶段
    llm_data = next(d for e, d in events if e == "status" and d.get("stage") == "llm")
    assert llm_data["stage"] == "llm"
    # result 携带结构化解析结果
    result = next(d for e, d in events if e == "result")
    assert result["parse_status"] == "completed"
    assert "modules" in result["result"]
    assert result["result"]["modules"][0]["name"]


def test_parse_stream_error_handling(client, project_id, user_headers):
    """需求无文本内容时 result 中 parse_status 为 failed（非异常路径）。"""
    req = upload_requirement(client, user_headers, project_id, content="")
    rid = req.json()["id"]

    resp, events = get_stream(
        client,
        user_headers,
        f"/api/v1/projects/{project_id}/requirements/{rid}/parse/stream",
    )
    assert resp.status_code == 200
    result = next(d for e, d in events if e == "result")
    assert result["parse_status"] == "failed"
    assert result["error_message"]


def test_test_points_stream(client, project_id, user_headers):
    """测试点生成流式接口：status -> result（五类测试点）。"""
    req = upload_requirement(client, user_headers, project_id)
    rid = req.json()["id"]
    client.post(
        f"/api/v1/projects/{project_id}/requirements/{rid}/parse",
        headers=user_headers,
    )

    resp, events = get_stream(
        client,
        user_headers,
        f"/api/v1/projects/{project_id}/requirements/{rid}/test-points/generate/stream",
    )
    assert resp.status_code == 200
    result = next(d for e, d in events if e == "result")
    assert isinstance(result, list) and len(result) > 0
    categories = {item["category"] for item in result}
    assert categories >= {"normal", "exception", "boundary", "security", "compatibility"}


def test_test_cases_stream(client, project_id, user_headers):
    """测试用例生成流式接口：status -> result（含测试数据）。"""
    req = upload_requirement(client, user_headers, project_id)
    rid = req.json()["id"]
    client.post(
        f"/api/v1/projects/{project_id}/requirements/{rid}/parse",
        headers=user_headers,
    )
    client.post(
        f"/api/v1/projects/{project_id}/requirements/{rid}/test-points/generate",
        headers=user_headers,
    )

    resp, events = get_stream(
        client,
        user_headers,
        f"/api/v1/projects/{project_id}/requirements/{rid}/test-cases/generate/stream",
    )
    assert resp.status_code == 200
    result = next(d for e, d in events if e == "result")
    assert isinstance(result, list) and len(result) > 0
    first = result[0]
    assert first["title"] and first["steps"] and first["expected_result"]


def test_chat_stream(client, project_id, user_headers):
    """AI 聊天流式接口：delta 增量 -> result（完整回复已保存）。"""
    resp = client.post(
        f"/api/v1/projects/{project_id}/chat/messages/stream",
        json={"content": "请总结这个项目的主要风险"},
        headers=user_headers,
    )
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("text/event-stream")

    events = parse_sse_events(resp.text)
    names = [e for e, _ in events]
    assert "delta" in names and "result" in names
    # delta 逐块拼接等于 result 的完整内容
    delta_text = "".join(d["content"] for e, d in events if e == "delta")
    result = next(d for e, d in events if e == "result")
    assert result["content"]
    assert delta_text == result["content"]
    assert result["id"] > 0


def test_chat_stream_persists_history(client, project_id, user_headers):
    """流式聊天后，对话历史中应有用户消息与助手回复。"""
    resp = client.post(
        f"/api/v1/projects/{project_id}/chat/messages/stream",
        json={"content": "你好"},
        headers=user_headers,
    )
    assert resp.status_code == 200

    history = client.get(
        f"/api/v1/projects/{project_id}/chat/history",
        headers=user_headers,
    ).json()
    roles = [item["role"] for item in history["items"]]
    assert roles == ["user", "assistant"]
