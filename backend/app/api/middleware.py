"""操作日志中间件：记录 API 写操作（POST/PUT/PATCH/DELETE）。"""
import logging

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.operation_log import OperationLog

logger = logging.getLogger(__name__)

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
MAX_BODY_BYTES = 8192


class OperationLogMiddleware:
    """纯 ASGI 中间件：捕获请求体并写入操作日志。"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        method = scope.get("method", "")
        if (
            scope["type"] != "http"
            or method not in WRITE_METHODS
            or not path.startswith("/api/")
        ):
            await self.app(scope, receive, send)
            return

        chunks: list[bytes] = []

        async def buffered_receive():
            message = await receive()
            if message["type"] == "http.request":
                chunks.append(message.get("body", b""))
            return message

        async def send_wrapper(message):
            await send(message)
            # 响应发送完毕后写入日志
            if message["type"] == "http.response.body" and not message.get(
                "more_body", False
            ):
                _write_operation_log(scope, chunks)

        await self.app(scope, buffered_receive, send_wrapper)


def _write_operation_log(scope, chunks: list[bytes]) -> None:
    """写入一条操作日志（失败不影响业务请求）。"""
    try:
        body = b"".join(chunks)[:MAX_BODY_BYTES]
        headers = {k.decode(errors="replace"): v.decode(errors="replace") for k, v in scope.get("headers", [])}
        if "multipart" in headers.get("content-type", ""):
            detail = "<文件上传>"
        else:
            detail = body.decode("utf-8", errors="replace")[:500]
        client = scope.get("client") or ("", 0)
        db = SessionLocal()
        try:
            db.add(
                OperationLog(
                    user_id=_extract_user_id(scope),
                    action=f"{scope.get('method', '')} {scope.get('path', '')}",
                    module=_module_from_path(scope.get("path", "")),
                    detail=detail or None,
                    ip=client[0],
                )
            )
            db.commit()
        finally:
            db.close()
    except Exception:  # 日志写入异常不能影响业务
        logger.exception("写入操作日志失败")


def _extract_user_id(scope) -> int | None:
    """从 Authorization 头解析用户 ID（尽力而为，失败返回 None）。"""
    auth = ""
    for key, value in scope.get("headers", []):
        if key == b"authorization":
            auth = value.decode(errors="replace")
    if not auth.startswith("Bearer "):
        return None
    try:
        payload = decode_access_token(auth[7:])
        return int(payload.get("sub", 0)) or None
    except Exception:
        return None


def _module_from_path(path: str) -> str:
    """从 API 路径提取业务模块名。"""
    parts = path.strip("/").split("/")
    for part in parts:
        if part in {"projects", "auth", "users", "system"}:
            return part
    return parts[-1] if parts else ""
