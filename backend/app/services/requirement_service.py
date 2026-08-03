"""需求解析业务逻辑：调用 Requirement Agent 并保存解析结果。"""
import json
import time

from sqlalchemy.orm import Session

from app.agents.llm import get_llm_provider
from app.agents.requirement_agent import RequirementAgent
from app.core.config import settings
from app.models.module import Module
from app.models.project import Project
from app.models.requirement import Requirement
from app.services.ai_log_service import log_ai_call
from app.services.system_settings_service import get_setting
from app.services.sut_service import build_project_context


def run_requirement_parse(
    db: Session, requirement: Requirement, user_id: int
) -> Requirement:
    """调用 Requirement Agent 解析需求，保存结构化结果并同步功能模块。"""
    if not requirement.content:
        requirement.parse_status = "failed"
        requirement.error_message = "需求文档未提取到文本内容，无法解析"
        db.commit()
        db.refresh(requirement)
        return requirement

    content = requirement.content[: settings.AI_MAX_CONTENT_LENGTH]
    project = db.get(Project, requirement.project_id)
    project_context = build_project_context(project) if project else ""
    start = time.monotonic()
    try:
        provider = get_llm_provider(db)
        agent = RequirementAgent(provider)
        system_prompt = get_setting(db, "prompt_requirement")
        result = agent.parse(
            content, requirement.file_name, system_prompt, project_context
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        log_ai_call(
            db,
            user_id=user_id,
            agent="Requirement",
            provider=agent.provider_name,
            prompt_length=len(content),
            response_length=len(json.dumps(result, ensure_ascii=False)),
            duration_ms=duration_ms,
        )
    except Exception as exc:  # 模型调用/密钥配置/输出解析失败
        duration_ms = int((time.monotonic() - start) * 1000)
        log_ai_call(
            db,
            user_id=user_id,
            agent="Requirement",
            provider=None,
            prompt_length=len(content),
            response_length=0,
            duration_ms=duration_ms,
            status="failed",
            error_message=str(exc)[:500],
        )
        requirement.parse_status = "failed"
        requirement.error_message = f"解析失败：{exc}"
        db.commit()
        db.refresh(requirement)
        return requirement

    # 保存结构化解析结果
    requirement.parse_status = "completed"
    requirement.parse_result = json.dumps(result, ensure_ascii=False)
    requirement.error_message = None

    # 同步功能模块到 modules 表（先清旧后写新，支持重复解析）
    db.query(Module).filter(Module.requirement_id == requirement.id).delete()
    for index, module_data in enumerate(result.get("modules", [])):
        db.add(
            Module(
                project_id=requirement.project_id,
                requirement_id=requirement.id,
                name=str(module_data.get("name", ""))[:100],
                description=module_data.get("description"),
                sort_order=index,
            )
        )
    db.commit()
    db.refresh(requirement)
    return requirement
