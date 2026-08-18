"""SSE 流式接口真实环境冒烟测试：起 uvicorn + SQLite + demo 模式，走完整链路。"""
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8001/api/v1"


def http(method, url, data=None, token=None, headers=None):
    req_headers = {"Content-Type": "application/json"}
    if token:
        req_headers["Authorization"] = f"Bearer {token}"
    if headers:
        req_headers.update(headers)
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status, resp.headers, resp.read()


def main():
    # 1. 注册（已存在则跳过）+ 登录
    try:
        http("POST", f"{BASE}/auth/register", {"username": "sse_demo", "password": "pass123456"})
    except urllib.error.HTTPError as exc:
        if exc.code != 400:  # 400 = 用户名已存在，正常
            raise
    # login 是 OAuth2 表单
    body = urllib.parse.urlencode({"username": "sse_demo", "password": "pass123456"}).encode()
    req = urllib.request.Request(f"{BASE}/auth/login", data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        token = json.loads(resp.read())["access_token"]

    # 2. 建项目
    _, _, raw = http("POST", f"{BASE}/projects", {"name": "SSE 冒烟项目"}, token)
    pid = json.loads(raw)["id"]
    print(f"[ok] project id={pid}")

    # 3. 上传需求
    import io
    content = "# 图书管理系统\n\n1. 管理员维护图书信息。\n2. 读者借阅归还图书。"
    boundary = "----wb-test-boundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="req.md"\r\n'
        f"Content-Type: text/markdown\r\n\r\n"
        f"{content}\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    req = urllib.request.Request(
        f"{BASE}/projects/{pid}/requirements/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        rid = json.loads(resp.read())["id"]
    print(f"[ok] requirement id={rid}")

    # 4. 解析（SSE 流式）
    print("\n=== parse/stream ===")
    req = urllib.request.Request(
        f"{BASE}/projects/{pid}/requirements/{rid}/parse/stream",
        headers={"Authorization": f"Bearer {token}"},
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=60) as resp:
        print(f"content-type: {resp.headers.get('content-type')}")
        chunks = resp.read().decode()
    print(f"duration: {time.time() - t0:.2f}s, {len(chunks)} bytes")
    for block in chunks.strip().split("\n\n"):
        print("  ", " | ".join(line for line in block.splitlines() if line))

    # 5. 聊天（SSE 逐字流）
    print("\n=== chat/messages/stream ===")
    req = urllib.request.Request(
        f"{BASE}/projects/{pid}/chat/messages/stream",
        data=json.dumps({"content": "你好，介绍一下你自己"}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    t0 = time.time()
    first_chunk_time = None
    with urllib.request.urlopen(req, timeout=60) as resp:
        print(f"content-type: {resp.headers.get('content-type')}")
        chunks = resp.read().decode()
    print(f"duration: {time.time() - t0:.2f}s, {len(chunks)} bytes")
    for block in chunks.strip().split("\n\n"):
        lines = [l for l in block.splitlines() if l]
        if lines:
            print("  ", " | ".join(lines[:1]))
    print("\n[ALL OK]")


if __name__ == "__main__":
    main()
