"""被测系统服务：项目上下文构建与连接测试。"""
import time

import httpx

from app.models.project import Project


def build_project_context(project: Project) -> str:
    """构建被测系统上下文（供 AI Agent 分析时使用）。"""
    parts = [f"项目名称：{project.name}"]
    if project.system_name:
        parts.append(f"被测系统名称：{project.system_name}")
    if project.test_url:
        parts.append(f"测试网址：{project.test_url}")
    if project.system_type:
        parts.append(f"系统类型：{project.system_type}")
    if project.browser_type:
        parts.append(f"浏览器：{project.browser_type}")
    return "\n".join(parts)


async def test_connection(url: str | None) -> dict:
    """请求目标 URL，检测网络连接、HTTP 状态码与响应时间。"""
    if not url:
        return {
            "success": False,
            "http_status": None,
            "response_time_ms": None,
            "message": "未配置测试网址",
        }
    if not url.startswith(("http://", "https://")):
        return {
            "success": False,
            "http_status": None,
            "response_time_ms": None,
            "message": "测试网址格式不正确（需以 http:// 或 https:// 开头）",
        }
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(
            timeout=10.0, follow_redirects=True, verify=False
        ) as client:
            response = await client.get(url)
        elapsed = int((time.monotonic() - start) * 1000)
        success = response.status_code < 400
        message = (
            f"连接成功，HTTP {response.status_code}，耗时 {elapsed} ms"
            if success
            else f"HTTP {response.status_code}，耗时 {elapsed} ms"
        )
        return {
            "success": success,
            "http_status": response.status_code,
            "response_time_ms": elapsed,
            "message": message,
        }
    except httpx.TimeoutException:
        return {
            "success": False,
            "http_status": None,
            "response_time_ms": None,
            "message": "连接超时（超过 10 秒）",
        }
    except Exception as exc:
        return {
            "success": False,
            "http_status": None,
            "response_time_ms": None,
            "message": f"网络连接失败：{type(exc).__name__}",
        }
