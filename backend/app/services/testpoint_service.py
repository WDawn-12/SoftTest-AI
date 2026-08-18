"""测试点生成业务逻辑：调用 TestPoint Agent 并保存结果。"""
import json
import time

from sqlalchemy.orm import Session

from app.agents.llm import get_llm_provider
from app.agents.testpoint_agent import TestPointAgent
from app.models.module import Module
from app.models.project import Project
from app.models.requirement import Requirement
from app.models.test_point import TestPoint
from app.schemas.testpoint import TestPointOut
from app.services.ai_log_service import log_ai_call
from app.services.system_settings_service import get_setting
from app.services.sut_service import build_project_context

# 类别归一化映射：兼容模型输出的中英文写法
CATEGORY_MAP = {
    "normal": "normal",
    "正常": "normal",
    "正常流程": "normal",
    "正常流程测试": "normal",
    "exception": "exception",
    "异常": "exception",
    "异常流程": "exception",
    "异常流程测试": "exception",
    "boundary": "boundary",
    "边界": "boundary",
    "边界值": "boundary",
    "边界值测试": "boundary",
    "security": "security",
    "安全": "security",
    "安全测试": "security",
    "compatibility": "compatibility",
    "兼容": "compatibility",
    "兼容性": "compatibility",
    "兼容性测试": "compatibility",
    "performance": "performance",
    "性能": "performance",
    "性能测试": "performance",
}


def run_testpoint_generation(
    db: Session, requirement: Requirement, user_id: int
) -> list[TestPoint]:
    """调用 TestPoint Agent 生成六类测试点并保存（重新生成时先清旧数据）。"""
    modules = (
        db.query(Module)
        .filter(Module.requirement_id == requirement.id)
        .order_by(Module.sort_order)
        .all()
    )
    functions = _collect_functions(requirement, modules)

    content = requirement.content or ""
    project = db.get(Project, requirement.project_id)
    project_context = build_project_context(project) if project else ""
    prompt_length = len(json.dumps(functions, ensure_ascii=False)) + len(content)
    start = time.monotonic()
    try:
        agent = TestPointAgent(get_llm_provider(db))
        system_prompt = get_setting(db, "prompt_testpoint")
        result = agent.generate(
            functions, content, requirement.file_name, system_prompt, project_context
        )
        points = result.get("test_points", [])
        duration_ms = int((time.monotonic() - start) * 1000)
        log_ai_call(
            db,
            user_id=user_id,
            agent="TestPoint",
            provider=agent.provider_name,
            prompt_length=prompt_length,
            response_length=len(json.dumps(points, ensure_ascii=False)),
            duration_ms=duration_ms,
        )
    except Exception as exc:  # 模型调用/密钥配置/输出解析失败
        duration_ms = int((time.monotonic() - start) * 1000)
        log_ai_call(
            db,
            user_id=user_id,
            agent="TestPoint",
            provider=None,
            prompt_length=prompt_length,
            response_length=0,
            duration_ms=duration_ms,
            status="failed",
            error_message=str(exc)[:500],
        )
        raise ValueError(f"测试点生成失败：{exc}") from exc

    if not points:
        raise ValueError("未生成任何测试点")

    # 重新生成：先清空该需求下已有测试点
    db.query(TestPoint).filter(TestPoint.requirement_id == requirement.id).delete()
    module_map = {m.name: m.id for m in modules}
    created: list[TestPoint] = []
    for item in points:
        name = str(item.get("name", "")).strip()[:255]
        if not name:
            continue
        module_name = str(item.get("module", "")).strip()
        created.append(
            TestPoint(
                project_id=requirement.project_id,
                requirement_id=requirement.id,
                module_id=module_map.get(module_name),
                name=name,
                category=_normalize_category(item.get("category", "normal")),
            )
        )
    db.add_all(created)
    db.commit()
    for point in created:
        db.refresh(point)
    return created


def build_testpoint_out(db: Session, points: list[TestPoint]) -> list[TestPointOut]:
    """组装响应：补充所属模块名称。"""
    module_ids = {p.module_id for p in points if p.module_id}
    module_names: dict[int, str] = {}
    if module_ids:
        rows = db.query(Module.id, Module.name).filter(Module.id.in_(module_ids)).all()
        module_names = {mid: name for mid, name in rows}
    return [
        TestPointOut(
            id=p.id,
            project_id=p.project_id,
            requirement_id=p.requirement_id,
            module_id=p.module_id,
            module_name=module_names.get(p.module_id) if p.module_id else None,
            name=p.name,
            category=p.category,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in points
    ]


def _collect_functions(
    requirement: Requirement, modules: list[Module]
) -> list[dict]:
    """收集功能点：优先使用 AI 解析结果中的模块功能点。"""
    functions: list[dict] = []
    if requirement.parse_result:
        try:
            data = json.loads(requirement.parse_result)
            for module in data.get("modules", []):
                funcs = [f for f in module.get("functions", []) if f]
                if funcs:
                    functions.append(
                        {"module": module.get("name", "未命名模块"), "functions": funcs}
                    )
        except json.JSONDecodeError:
            pass
    if not functions and modules:
        functions = [{"module": m.name, "functions": [m.name]} for m in modules]
    if not functions:
        functions = [{"module": "核心功能", "functions": ["核心业务流程"]}]
    return functions


def _normalize_category(category: str) -> str:
    """将模型输出的类别写法归一化为标准值。"""
    return CATEGORY_MAP.get(str(category).strip(), "normal")
