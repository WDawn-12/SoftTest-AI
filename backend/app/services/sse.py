"""SSE（Server-Sent Events）消息格式化工具。"""
import json
from typing import Any


def sse_event(event: str, data: Any) -> str:
    """格式化一条 SSE 事件。

    事件格式：
        event: <事件名>
        data: <JSON 或纯文本>

    事件之间以空行分隔，符合 text/event-stream 规范。
    """
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"
