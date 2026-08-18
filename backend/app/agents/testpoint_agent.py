"""TestPoint Agent：测试点生成 Agent（独立封装）。"""
import json

from app.agents.base import BaseAgent

# 测试点生成系统提示词：约束模型输出六类测试点
SYSTEM_PROMPT = """你是一名资深的软件测试设计专家。根据给定的功能模块与功能点，为每个功能点设计测试点。
每个功能点必须覆盖以下 6 类测试：
- normal（正常流程测试）：验证功能按预期正常工作
- exception（异常流程测试）：验证非法输入、异常操作时系统的表现
- boundary（边界值测试）：验证输入边界条件（最小、最大、空值等）
- security（安全测试）：验证权限控制、越权访问、注入等安全场景
- compatibility（兼容性测试）：验证不同浏览器、设备、分辨率下的兼容性
- performance（性能测试）：验证响应时间、并发处理、资源占用、大数据量下的表现

必须严格按以下 JSON 结构输出，不要输出任何多余文字或 Markdown 代码块：
{
  "test_points": [
    {"category": "normal|exception|boundary|security|compatibility|performance", "module": "所属模块名", "name": "测试点描述"}
  ]
}
要求：每个功能点 6 类各至少 1 条测试点。"""


class TestPointAgent(BaseAgent):
    """测试点生成 Agent：根据功能点生成五类测试点。"""

    def generate(
        self,
        functions: list[dict],
        content: str,
        file_name: str,
        system_prompt: str | None = None,
        project_context: str = "",
    ) -> dict:
        """生成测试点，返回结构化 JSON 字典。"""
        user_prompt = self._build_user_prompt(
            functions, content, file_name, project_context
        )
        raw = self._provider.chat(system_prompt or SYSTEM_PROMPT, user_prompt)
        data = self._extract_json(raw)
        points = data.get("test_points")
        if not isinstance(points, list) or not points:
            raise ValueError("模型输出缺少 test_points 字段")
        return data

    def _build_user_prompt(
        self,
        functions: list[dict],
        content: str,
        file_name: str,
        project_context: str = "",
    ) -> str:
        functions_json = json.dumps(functions, ensure_ascii=False)
        parts = [f"需求文档名称：{file_name}"]
        if project_context:
            parts.append(f"被测系统信息：\n{project_context}")
        parts.append(f"功能模块与功能点：\n```json\n{functions_json}\n```")
        parts.append(f"需求文档内容：\n{content}")
        return "\n\n".join(parts)
