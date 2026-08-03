"""测试用例生成业务逻辑：调用 TestCase Agent 并保存结果。"""
from sqlalchemy.orm import Session

from app.agents.llm import get_llm_provider
from app.agents.testcase_agent import TestCaseAgent
from app.models.module import Module
from app.models.requirement import Requirement
from app.models.test_case import TestCase
from app.models.test_point import TestPoint
from app.schemas.testcase import TestCaseOut

# 优先级归一化映射：兼容模型输出的中英文写法
PRIORITY_MAP = {
    "高": "高",
    "high": "高",
    "p0": "高",
    "p1": "高",
    "中": "中",
    "medium": "中",
    "p2": "中",
    "低": "低",
    "low": "低",
    "p3": "低",
}


def run_testcase_generation(
    db: Session, requirement: Requirement, user_id: int
) -> list[TestCase]:
    """调用 TestCase Agent 生成测试用例并保存（重新生成时替换旧用例）。"""
    test_points = (
        db.query(TestPoint)
        .filter(TestPoint.requirement_id == requirement.id)
        .order_by(TestPoint.id)
        .all()
    )
    if not test_points:
        raise ValueError("该需求还没有测试点，请先生成测试点")

    modules = (
        db.query(Module)
        .filter(Module.requirement_id == requirement.id)
        .order_by(Module.sort_order)
        .all()
    )
    module_name_map = {m.id: m.name for m in modules}
    module_id_map = {m.name: m.id for m in modules}
    points_data = [
        {
            "module": module_name_map.get(tp.module_id, "核心模块"),
            "category": tp.category,
            "name": tp.name,
        }
        for tp in test_points
    ]

    try:
        agent = TestCaseAgent(get_llm_provider())
        result = agent.generate(points_data)
        cases = result.get("test_cases", [])
    except Exception as exc:  # 模型调用/密钥配置/输出解析失败
        raise ValueError(f"测试用例生成失败：{exc}") from exc

    if not cases:
        raise ValueError("未生成任何测试用例")

    # 重新生成：先删除该需求下旧用例，再按项目现有最大编号续编
    db.query(TestCase).filter(TestCase.requirement_id == requirement.id).delete()
    next_no = _next_case_no(db, requirement.project_id)
    created: list[TestCase] = []
    for index, item in enumerate(cases):
        title = str(item.get("title", "")).strip()[:200]
        if not title:
            continue
        module_name = str(item.get("module", "")).strip()
        created.append(
            TestCase(
                project_id=requirement.project_id,
                requirement_id=requirement.id,
                module_id=module_id_map.get(module_name),
                case_no=f"TC{next_no + index:04d}",
                title=title,
                test_point=str(item.get("test_point", "")).strip()[:500] or None,
                test_data=str(item.get("test_data", "")).strip()[:500] or None,
                priority=_normalize_priority(item.get("priority")),
                preconditions=item.get("preconditions"),
                steps=_join_steps(item.get("steps")),
                expected_result=item.get("expected_result"),
                remark=item.get("remark"),
                status="draft",
                created_by=user_id,
            )
        )
    db.add_all(created)
    db.commit()
    for case in created:
        db.refresh(case)
    return created


def build_testcase_out(db: Session, cases: list[TestCase]) -> list[TestCaseOut]:
    """组装响应：补充所属模块名称。"""
    module_ids = {c.module_id for c in cases if c.module_id}
    module_names: dict[int, str] = {}
    if module_ids:
        rows = db.query(Module.id, Module.name).filter(Module.id.in_(module_ids)).all()
        module_names = {mid: name for mid, name in rows}
    return [
        TestCaseOut(
            id=c.id,
            project_id=c.project_id,
            requirement_id=c.requirement_id,
            module_id=c.module_id,
            module_name=module_names.get(c.module_id) if c.module_id else None,
            case_no=c.case_no,
            title=c.title,
            test_point=c.test_point,
            test_data=c.test_data,
            priority=c.priority,
            preconditions=c.preconditions,
            steps=c.steps,
            expected_result=c.expected_result,
            remark=c.remark,
            status=c.status,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in cases
    ]


def _next_case_no(db: Session, project_id: int) -> int:
    """计算项目内下一个用例编号数字部分（TC0001 起）。"""
    rows = db.query(TestCase.case_no).filter(TestCase.project_id == project_id).all()
    numbers = []
    for (case_no,) in rows:
        if case_no and case_no.startswith("TC") and case_no[2:].isdigit():
            numbers.append(int(case_no[2:]))
    return (max(numbers) + 1) if numbers else 1


def _join_steps(steps: object) -> str | None:
    """将步骤列表转换为每行一步的文本。"""
    if isinstance(steps, list):
        cleaned = [str(s).strip() for s in steps if str(s).strip()]
        return "\n".join(cleaned) if cleaned else None
    text = str(steps or "").strip()
    return text or None


def _normalize_priority(priority: object) -> str:
    """将模型输出的优先级写法归一化为 高/中/低。"""
    return PRIORITY_MAP.get(str(priority).strip().lower(), "中")
