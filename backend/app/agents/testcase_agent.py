"""TestCase Agent：测试用例生成 Agent（独立封装）。"""
import json

from app.agents.base import BaseAgent

# 测试用例生成系统提示词：约束模型输出完整用例结构
SYSTEM_PROMPT = """你是一名资深的软件测试用例设计专家。根据给定的测试点列表，为每条测试点设计一条完整的测试用例。
每条用例必须包含：功能名称、对应测试点、优先级（高/中/低）、前置条件、测试步骤（含具体测试数据）、预期结果、备注。

必须严格按以下 JSON 结构输出，不要输出任何多余文字或 Markdown 代码块：
{
  "test_cases": [
    {
      "module": "所属模块名",
      "title": "功能名称",
      "test_point": "对应测试点内容",
      "test_data": "测试数据（必须从「已生成测试数据」中选取并原样使用，格式：字段名：值，多行）",
      "priority": "高/中/低",
      "preconditions": "前置条件",
      "steps": ["步骤1（含测试数据）", "步骤2", "步骤3"],
      "expected_result": "预期结果",
      "remark": "备注"
    }
  ]
}
要求：
1. 每个测试点对应一条用例；
2. test_data 必须使用输入中「已生成测试数据」提供的候选值（按用例场景选取并原样填入），禁止自行编造或使用固定测试数据；
3. steps 至少 3 步且引用选用的测试数据。"""


class TestCaseAgent(BaseAgent):
    """测试用例生成 Agent：根据测试点生成完整测试用例。"""

    def generate(
        self,
        test_points: list[dict],
        system_prompt: str | None = None,
        project_context: str = "",
    ) -> dict:
        """生成测试用例，返回结构化 JSON 字典。"""
        user_prompt = self._build_user_prompt(test_points, project_context)
        raw = self._provider.chat(system_prompt or SYSTEM_PROMPT, user_prompt)
        data = self._extract_json(raw)
        cases = data.get("test_cases")
        if not isinstance(cases, list) or not cases:
            raise ValueError("模型输出缺少 test_cases 字段")
        return data

    def _build_user_prompt(
        self, test_points: list[dict], project_context: str = ""
    ) -> str:
        points_json = json.dumps(test_points, ensure_ascii=False)
        parts = []
        if project_context:
            parts.append(f"被测系统信息：\n{project_context}")
        parts.append(f"测试点列表：\n```json\n{points_json}\n```")
        return "\n\n".join(parts)
