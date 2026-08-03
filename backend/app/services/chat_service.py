"""AI 聊天业务逻辑：上下文记忆、项目知识库与回复生成。"""
import json
import time

from sqlalchemy.orm import Session

from app.agents.chat_agent import ChatAgent
from app.agents.llm import get_llm_provider
from app.models.chat_history import ChatHistory
from app.models.requirement import Requirement
from app.models.test_case import TestCase
from app.services.ai_log_service import log_ai_call
from app.services.system_settings_service import get_setting

HISTORY_LIMIT = 10  # 注入对话上下文的最近消息条数
KNOWLEDGE_LIMIT = 8000  # 项目知识库文本上限


def build_project_knowledge(db: Session, project_id: int) -> str:
    """汇总项目需求解析结果与测试用例，作为问答知识库。"""
    parts: list[str] = []

    requirements = (
        db.query(Requirement)
        .filter(
            Requirement.project_id == project_id,
            Requirement.parse_status == "completed",
        )
        .order_by(Requirement.id.desc())
        .limit(5)
        .all()
    )
    for req in requirements:
        try:
            result = json.loads(req.parse_result) if req.parse_result else {}
        except json.JSONDecodeError:
            result = {}
        modules = [
            m.get("name", "") for m in result.get("modules", []) if m.get("name")
        ]
        summary = result.get("summary", "")
        parts.append(
            f"需求《{req.file_name}》：{summary}；功能模块：{'、'.join(modules) or '无'}"
        )

    cases = (
        db.query(TestCase)
        .filter(TestCase.project_id == project_id)
        .order_by(TestCase.case_no.asc())
        .limit(100)
        .all()
    )
    for case in cases:
        parts.append(
            f"用例 {case.case_no}：{case.title}；优先级：{case.priority}；"
            f"测试点：{case.test_point or ''}；预期结果：{case.expected_result or ''}"
        )

    return "\n".join(parts)[:KNOWLEDGE_LIMIT]


def get_recent_history(
    db: Session, user_id: int, project_id: int, limit: int = HISTORY_LIMIT
) -> list[ChatHistory]:
    """获取最近的对话记录（按时间正序）。"""
    rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user_id, ChatHistory.project_id == project_id)
        .order_by(ChatHistory.id.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(rows))


def build_reply(
    db: Session, user_id: int, project_id: int, question: str
) -> ChatHistory:
    """调用 ChatAgent 生成回复并保存到聊天记录。"""
    history = get_recent_history(db, user_id, project_id)
    knowledge = build_project_knowledge(db, project_id)
    prompt_length = (
        len(question)
        + len(knowledge)
        + sum(len(message.content) for message in history)
    )
    start = time.monotonic()
    try:
        agent = ChatAgent(get_llm_provider(db))
        system_prompt = get_setting(db, "prompt_chat")
        reply_content = agent.respond(question, history, knowledge, system_prompt)
        duration_ms = int((time.monotonic() - start) * 1000)
        log_ai_call(
            db,
            user_id=user_id,
            agent="Chat",
            provider=agent.provider_name,
            prompt_length=prompt_length,
            response_length=len(reply_content),
            duration_ms=duration_ms,
        )
    except Exception as exc:  # 模型调用/密钥配置失败
        duration_ms = int((time.monotonic() - start) * 1000)
        log_ai_call(
            db,
            user_id=user_id,
            agent="Chat",
            provider=None,
            prompt_length=prompt_length,
            response_length=0,
            duration_ms=duration_ms,
            status="failed",
            error_message=str(exc)[:500],
        )
        reply_content = f"（AI 服务调用失败：{exc}，请检查 API 配置）"
    assistant = ChatHistory(
        user_id=user_id,
        project_id=project_id,
        role="assistant",
        content=reply_content,
    )
    db.add(assistant)
    db.commit()
    db.refresh(assistant)
    return assistant
