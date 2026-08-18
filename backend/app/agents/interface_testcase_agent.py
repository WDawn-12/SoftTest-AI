"""InterfaceTestCase Agent：根据接口定义生成接口测试用例（独立封装）。"""
import json

from app.agents.base import BaseAgent

# 接口测试用例生成系统提示词：约束模型输出完整接口用例结构
SYSTEM_PROMPT = """你是一名资深的接口测试专家。根据给定的接口定义列表，为每个接口设计接口测试用例。
每个接口必须覆盖以下 5 类测试：
- normal（正常流程）：验证接口在合法输入下返回正确结果
- exception（异常流程）：验证缺失参数、非法参数、错误请求时接口的容错表现
- boundary（边界值）：验证参数取值边界（最小/最大/空值/超长等）
- security（安全测试）：验证鉴权缺失、越权访问、注入攻击等安全场景
- parameter（参数组合）：验证必填/选填参数组合、参数类型与格式的兼容性

必须严格按以下 JSON 结构输出，不要输出任何多余文字或 Markdown 代码块：
{
  "test_cases": [
    {
      "interface_id": "接口ID（对应输入中的 id，无则为 null）",
      "title": "用例标题",
      "category": "normal|exception|boundary|security|parameter",
      "method": "GET/POST/PUT/DELETE",
      "path": "接口路径（保留 {占位符}）",
      "test_data": "测试数据描述（具体参数值）",
      "request_payload": "请求参数/请求体（JSON 或 key=value，含具体测试值）",
      "expected_status": "预期状态码（如 200/400/401/500）",
      "expected_result": "预期结果描述",
      "priority": "高/中/低",
      "preconditions": "前置条件",
      "steps": ["步骤1", "步骤2", "步骤3"],
      "remark": "备注"
    }
  ]
}
要求：
1. 每个接口至少 5 类各 1 条用例（normal/exception/boundary/security/parameter 全覆盖）；
2. 路径中的 {占位符}（如 /users/{id}）必须在用例中给出实际取值；
3. 优先级建议：安全测试与核心流程为「高」，边界与异常为「中」，参数组合为「中」。"""


class InterfaceTestCaseAgent(BaseAgent):
    """接口测试用例生成 Agent：根据接口定义生成接口测试用例。"""

    def generate(
        self,
        interfaces: list[dict],
        system_prompt: str | None = None,
        project_context: str = "",
    ) -> dict:
        """生成接口测试用例，返回结构化 JSON 字典。"""
        user_prompt = self._build_user_prompt(interfaces, project_context)
        raw = self._provider.chat(system_prompt or SYSTEM_PROMPT, user_prompt)
        data = self._extract_json(raw)
        cases = data.get("test_cases")
        if not isinstance(cases, list) or not cases:
            raise ValueError("模型输出缺少 test_cases 字段")
        return data

    def _build_user_prompt(
        self, interfaces: list[dict], project_context: str = ""
    ) -> str:
        interfaces_json = json.dumps(interfaces, ensure_ascii=False)
        parts = []
        if project_context:
            parts.append(f"被测系统信息：\n{project_context}")
        parts.append(f"接口定义列表：\n```json\n{interfaces_json}\n```")
        return "\n\n".join(parts)
