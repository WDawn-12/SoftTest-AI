"""接口测试业务逻辑：接口管理、接口用例生成与保存。"""
import json
import time

from sqlalchemy.orm import Session

from app.agents.llm import get_llm_provider
from app.agents.interface_testcase_agent import InterfaceTestCaseAgent
from app.models.interface import Interface
from app.models.interface_test_case import InterfaceTestCase
from app.models.project import Project
from app.schemas.interface_test import InterfaceCaseOut, InterfaceOut
from app.services.ai_log_service import log_ai_call
from app.services.excel_export import build_testcase_excel
from app.services.system_settings_service import get_setting
from app.services.sut_service import build_project_context

# 单次生成的接口数量上限：避免输出过长被截断
INTERFACE_BATCH_SIZE = 5

# 优先级归一化映射
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


# ---------- 接口定义 ----------
def build_interface_out(db: Session, interfaces: list[Interface]) -> list[InterfaceOut]:
    """组装接口响应。"""
    return [InterfaceOut.model_validate(item) for item in interfaces]


# ---------- 接口用例生成 ----------
def run_interface_case_generation(
    db: Session, project_id: int, user_id: int, interface_ids: list[int] | None = None
) -> list[InterfaceTestCase]:
    """调用 InterfaceTestCase Agent 生成接口测试用例并保存。

    interface_ids 为 None 时生成项目下全部接口；否则只生成指定接口。
    重新生成时先删除对应接口的旧用例。
    """
    query = db.query(Interface).filter(Interface.project_id == project_id)
    if interface_ids:
        query = query.filter(Interface.id.in_(interface_ids))
    interfaces = query.order_by(Interface.id).all()
    if not interfaces:
        raise ValueError("该项目还没有接口定义，请先录入或导入接口")

    project = db.get(Project, project_id)
    project_context = build_project_context(project) if project else ""
    interfaces_data = [
        {
            "id": api.id,
            "name": api.name,
            "method": api.method,
            "path": api.path,
            "summary": api.summary or "",
            "headers": api.headers or "",
            "params": api.params or "",
            "body": api.body or "",
        }
        for api in interfaces
    ]

    prompt_length = len(json.dumps(interfaces_data, ensure_ascii=False))
    start = time.monotonic()
    provider_name = None
    total_response_length = 0
    try:
        provider = get_llm_provider(db)
        agent = InterfaceTestCaseAgent(provider)
        system_prompt = get_setting(db, "prompt_interface_testcase")
        provider_name = agent.provider_name
        # 分批生成：每批 INTERFACE_BATCH_SIZE 个接口
        batches = [
            interfaces_data[i : i + INTERFACE_BATCH_SIZE]
            for i in range(0, len(interfaces_data), INTERFACE_BATCH_SIZE)
        ]
        cases: list[dict] = []
        for batch in batches:
            batch_result = agent.generate(batch, system_prompt, project_context)
            batch_cases = batch_result.get("test_cases", [])
            cases.extend(batch_cases)
            total_response_length += len(json.dumps(batch_cases, ensure_ascii=False))
        duration_ms = int((time.monotonic() - start) * 1000)
        log_ai_call(
            db,
            user_id=user_id,
            agent="InterfaceTestCase",
            provider=provider_name,
            prompt_length=prompt_length,
            response_length=total_response_length,
            duration_ms=duration_ms,
        )
    except Exception as exc:  # 模型调用/密钥配置/输出解析失败
        duration_ms = int((time.monotonic() - start) * 1000)
        log_ai_call(
            db,
            user_id=user_id,
            agent="InterfaceTestCase",
            provider=provider_name,
            prompt_length=prompt_length,
            response_length=total_response_length,
            duration_ms=duration_ms,
            status="failed",
            error_message=str(exc)[:500],
        )
        raise ValueError(f"接口用例生成失败：{exc}") from exc

    if not cases:
        raise ValueError("未生成任何接口测试用例")

    # 重新生成：先删除该范围旧用例，再按项目现有最大编号续编
    if interface_ids:
        db.query(InterfaceTestCase).filter(
            InterfaceTestCase.interface_id.in_(interface_ids)
        ).delete()
    else:
        db.query(InterfaceTestCase).filter(
            InterfaceTestCase.project_id == project_id
        ).delete()
    next_no = _next_case_no(db, project_id)
    interface_id_map = {api.id: api for api in interfaces}
    created: list[InterfaceTestCase] = []
    for index, item in enumerate(cases):
        title = str(item.get("title", "")).strip()[:200]
        if not title:
            continue
        method = str(item.get("method", "GET")).strip().upper()[:10]
        path = str(item.get("path", "")).strip()[:500]
        if not path:
            continue
        interface_id = item.get("interface_id") or interfaces_data[0].get("id")
        created.append(
            InterfaceTestCase(
                project_id=project_id,
                interface_id=(
                    interface_id
                    if interface_id in interface_id_map
                    else (interfaces[0].id if interfaces else None)
                ),
                case_no=f"API{next_no + index:04d}",
                title=title,
                category=str(item.get("category", "normal")).strip()[:50] or "normal",
                method=method,
                path=path,
                test_data=str(item.get("test_data", "")).strip()[:2000] or None,
                request_payload=str(item.get("request_payload", "")).strip()[:2000]
                or None,
                expected_status=str(item.get("expected_status", "")).strip()[:50]
                or None,
                expected_result=str(item.get("expected_result", "")).strip()[:2000]
                or None,
                priority=_normalize_priority(item.get("priority")),
                preconditions=str(item.get("preconditions", "")).strip()[:2000] or None,
                steps=_join_steps(item.get("steps")),
                remark=str(item.get("remark", "")).strip()[:500] or None,
                status="draft",
                created_by=user_id,
            )
        )
    db.add_all(created)
    db.commit()
    for case in created:
        db.refresh(case)
    return created


def build_interface_case_out(
    db: Session, cases: list[InterfaceTestCase]
) -> list[InterfaceCaseOut]:
    """组装接口用例响应：补充接口名称。"""
    interface_ids = {c.interface_id for c in cases if c.interface_id}
    interface_names: dict[int, str] = {}
    if interface_ids:
        rows = (
            db.query(Interface.id, Interface.name)
            .filter(Interface.id.in_(interface_ids))
            .all()
        )
        interface_names = {iid: name for iid, name in rows}
    return [
        InterfaceCaseOut(
            id=c.id,
            project_id=c.project_id,
            interface_id=c.interface_id,
            interface_name=interface_names.get(c.interface_id)
            if c.interface_id
            else None,
            case_no=c.case_no,
            title=c.title,
            category=c.category,
            method=c.method,
            path=c.path,
            test_data=c.test_data,
            request_payload=c.request_payload,
            expected_status=c.expected_status,
            expected_result=c.expected_result,
            priority=c.priority,
            preconditions=c.preconditions,
            steps=c.steps,
            remark=c.remark,
            status=c.status,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in cases
    ]


def export_interface_cases_excel(db: Session, project_id: int) -> bytes:
    """导出项目下全部接口测试用例为 Excel。"""
    cases = (
        db.query(InterfaceTestCase)
        .filter(InterfaceTestCase.project_id == project_id)
        .order_by(InterfaceTestCase.case_no)
        .all()
    )
    interface_ids = {c.interface_id for c in cases if c.interface_id}
    interface_names: dict[int, str] = {}
    if interface_ids:
        rows = (
            db.query(Interface.id, Interface.name)
            .filter(Interface.id.in_(interface_ids))
            .all()
        )
        interface_names = {iid: name for iid, name in rows}
    rows = [
        [
            c.case_no,
            c.priority,
            interface_names.get(c.interface_id, "") if c.interface_id else "",
            f"{c.method} {c.path}",
            c.title,
            c.preconditions or "",
            c.steps or "",
            c.request_payload or "",
            c.expected_result or "",
            c.remark or "",
        ]
        for c in cases
    ]
    return build_testcase_excel(rows)


# ---------- 工具函数 ----------
def _next_case_no(db: Session, project_id: int) -> int:
    """计算项目内下一个接口用例编号数字部分（API0001 起）。"""
    rows = (
        db.query(InterfaceTestCase.case_no)
        .filter(InterfaceTestCase.project_id == project_id)
        .all()
    )
    numbers = []
    for (case_no,) in rows:
        if case_no and case_no.startswith("API") and case_no[3:].isdigit():
            numbers.append(int(case_no[3:]))
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
