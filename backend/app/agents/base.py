"""AI Agent 基类：提供模型供应商注入与 JSON 输出解析等公共能力。"""
import json
import re
from abc import ABC

from app.agents.llm import LLMProvider


class BaseAgent(ABC):
    """AI Agent 基类。"""

    def __init__(self, provider: LLMProvider):
        self._provider = provider

    @property
    def provider_name(self) -> str:
        """当前使用的模型供应商名称。"""
        return self._provider.name

    def _extract_json(self, raw: str) -> dict:
        """从模型输出中提取 JSON（兼容代码块包裹与前后多余文本）。"""
        text = raw.strip()
        # 去掉 ```json ... ``` 代码块
        fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
        if fence:
            text = fence.group(1).strip()
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("模型输出中未找到有效的 JSON")
        return json.loads(text[start : end + 1])
