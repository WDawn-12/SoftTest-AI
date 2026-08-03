"""Requirement Agent：需求解析 Agent（独立封装）。"""
import json
import re

from app.agents.llm import LLMProvider

# 需求解析系统提示词：约束模型输出结构化 JSON
SYSTEM_PROMPT = """你是一名资深的软件需求分析专家。请阅读用户提供的需求文档内容，完成以下分析：
1. 识别系统包含的功能模块；
2. 提取每个模块下的功能点；
3. 识别系统的用户角色；
4. 分析主要业务流程；
5. 识别潜在风险点（含风险类型、描述、等级）。

必须严格按以下 JSON 结构输出，不要输出任何多余文字或 Markdown 代码块：
{
  "summary": "需求概述（200字以内）",
  "modules": [
    {"name": "模块名称", "description": "模块职责说明", "functions": ["功能点1", "功能点2"]}
  ],
  "roles": ["角色1", "角色2"],
  "business_flows": [
    {"name": "流程名称", "steps": ["步骤1", "步骤2"]}
  ],
  "risks": [
    {"type": "风险类型", "description": "风险描述", "level": "高/中/低"}
  ]
}
要求：modules 至少 3 个；每个模块 functions 至少 2 个；roles 至少 2 个；
business_flows 至少 2 个；risks 至少 3 个。"""


class RequirementAgent:
    """需求解析 Agent：调用大模型从需求文档中提取结构化信息。"""

    def __init__(self, provider: LLMProvider):
        self._provider = provider

    @property
    def provider_name(self) -> str:
        """当前使用的模型供应商名称。"""
        return self._provider.name

    def parse(self, content: str, file_name: str) -> dict:
        """解析需求文本，返回结构化 JSON 字典。"""
        user_prompt = self._build_user_prompt(content, file_name)
        raw = self._provider.chat(SYSTEM_PROMPT, user_prompt)
        return self._extract_json(raw)

    def _build_user_prompt(self, content: str, file_name: str) -> str:
        return f"需求文档名称：{file_name}\n\n需求文档内容：\n{content}"

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
        data = json.loads(text[start : end + 1])
        # 校验必需字段
        for key in ("summary", "modules", "roles", "business_flows", "risks"):
            if key not in data:
                raise ValueError(f"模型输出缺少字段: {key}")
        return data
