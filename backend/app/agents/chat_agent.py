"""ChatAgent：AI 聊天助手（独立封装，支持 Markdown 回复）。"""
from app.agents.base import BaseAgent

# 聊天系统提示词：要求基于项目知识库回答并使用 Markdown
SYSTEM_PROMPT = """你是一名软件测试助手，帮助测试人员分析需求、设计测试并解答测试相关问题。
规则：
1. 优先依据「项目知识库」中的需求文档与测试用例回答；
2. 若知识库中没有相关内容，请明确说明「项目知识库中没有找到相关内容」，再给出通用建议；
3. 结合「最近对话」保持上下文连贯；
4. 回复使用 Markdown 格式（标题、列表、加粗、代码块等），内容简洁清晰。"""


class ChatAgent(BaseAgent):
    """聊天 Agent：基于项目知识库与对话历史生成 Markdown 回复。"""

    def respond(self, question: str, history: list, knowledge: str) -> str:
        """生成回复文本。"""
        user_prompt = self._build_user_prompt(question, history, knowledge)
        raw = self._provider.chat(SYSTEM_PROMPT, user_prompt)
        return raw.strip()

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
