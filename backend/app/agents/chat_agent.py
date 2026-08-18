"""ChatAgent：AI 聊天助手（独立封装，支持 Markdown 回复与工具调用）。"""
from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.tools import TOOL_SCHEMAS, run_tool

# 聊天系统提示词：要求基于项目知识库回答并使用 Markdown
SYSTEM_PROMPT = """你是一名软件测试助手，帮助测试人员分析需求、设计测试并解答测试相关问题。
规则：
1. 优先依据「项目知识库」中的需求文档与测试用例回答；
2. 若知识库中没有相关内容，请明确说明「项目知识库中没有找到相关内容」，再给出通用建议；
3. 结合「最近对话」保持上下文连贯；
4. 回复使用 Markdown 格式（标题、列表、加粗、代码块等），内容简洁清晰。
5. 当用户询问某字段的测试数据时，调用 generate_test_data 工具获取 12 类场景数据后展示；
   当用户询问项目知识库内容时，调用 get_project_knowledge 工具获取。"""


class ChatAgent(BaseAgent):
    """聊天 Agent：基于项目知识库与对话历史生成 Markdown 回复，支持工具调用。"""

    def respond(
        self,
        question: str,
        history: list,
        knowledge: str,
        system_prompt: str | None = None,
    ) -> str:
        """生成回复文本。"""
        user_prompt = self._build_user_prompt(question, history, knowledge)
        raw = self._provider.chat(system_prompt or SYSTEM_PROMPT, user_prompt)
        return raw.strip()

    def stream_respond(
        self,
        question: str,
        history: list,
        knowledge: str,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        """流式生成回复文本，逐块产出（配合 SSE 实现打字机效果）。"""
        user_prompt = self._build_user_prompt(question, history, knowledge)
        return self._provider.stream_chat(system_prompt or SYSTEM_PROMPT, user_prompt)

    def run_tools(
        self,
        question: str,
        history: list,
        knowledge: str,
        system_prompt: str | None = None,
        db: Session | None = None,
        project_id: int | None = None,
    ) -> tuple[list[dict], str | None]:
        """执行工具调用阶段（真实大模型自主决策 / 演示模式关键词模拟）。

        返回 (工具调用记录列表, 最终回复文本)。
        未命中任何工具时返回 ([], None)，调用方应继续走普通对话流程。
        """
        user_prompt = self._build_user_prompt(question, history, knowledge)

        def handler(name: str, args: dict) -> dict:
            return run_tool(name, args, db=db, project_id=project_id)

        return self._provider.run_tools(
            system_prompt or SYSTEM_PROMPT, user_prompt, TOOL_SCHEMAS, handler
        )

    def _build_user_prompt(
        self, question: str, history: list, knowledge: str
    ) -> str:
        parts = [f"项目知识库：\n{knowledge or '（暂无内容）'}"]
        if history:
            lines = []
            for message in history:
                sender = "用户" if message.role == "user" else "助手"
                lines.append(f"{sender}: {message.content[:500]}")
            parts.append("最近对话：\n" + "\n".join(lines))
        parts.append(f"对话内容：\n{question}")
        return "\n\n".join(parts)
