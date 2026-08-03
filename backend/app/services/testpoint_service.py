"""测试点生成业务逻辑：调用 TestPoint Agent 并保存结果。"""
import json

from sqlalchemy.orm import Session

from app.agents.llm import get_llm_provider
from app.agents.testpoint_agent import TestPointAgent
from app.models.module import Module
from app.models.requirement import Requirement
from app.models.test_point import TestPoint
from app.schemas.testpoint import TestPointOut

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
}


def run_testpoint_generation(
    db: Session, requirement: Requirement
) -> list[TestPoint]:
    """调用 TestPoint Agent 生成五类测试点并保存（重新生成时先清旧数据）。"""
    modules = (
        db.query(Module)
        .filter(Module.requirement_id == requirement.id)
        .order_by(Module.sort_order)
        .all()
    )
    functions = _collect_functions(requirement, modules)

    try:
        agent = TestPointAgent(get_llm_provider())
        result = agent.generate(
            functions, requirement.content or "", requirement.file_name
        )
        points = result.get("test_points", [])
    except Exception as exc:  # 模型调用/密钥配置/输出解析失败
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
