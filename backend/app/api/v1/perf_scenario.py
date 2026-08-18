"""性能测试场景 API：场景 CRUD + 导出 JMeter 压测脚本。"""
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import DbDep, get_current_user, get_owned_project
from app.models.perf_scenario import PerfScenario
from app.models.user import User
from app.schemas.perf_scenario import (
    PerfScenarioIn,
    PerfScenarioListOut,
    PerfScenarioOut,
    PerfScenarioUpdate,
)
from app.services.interface_test_service import build_perf_jmeter_test_plan

router = APIRouter(prefix="/projects/{project_id}/perf-scenarios", tags=["性能测试场景"])

CurrentUser = Annotated[User, Depends(get_current_user)]


def _parse_interface_ids(value: str | None) -> list[int]:
    """解析接口ID JSON（空/非法返回空列表）。"""
    if not value:
        return []
    try:
        data = json.loads(value)
        return [int(x) for x in data] if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError, ValueError):
        return []


def _to_out(scenario: PerfScenario) -> PerfScenarioOut:
    """ORM → 响应模型（interface_ids 转列表）。"""
    return PerfScenarioOut(
        id=scenario.id,
        project_id=scenario.project_id,
        name=scenario.name,
        description=scenario.description,
        thread_count=scenario.thread_count,
        loop_count=scenario.loop_count,
        ramp_up=scenario.ramp_up,
        think_time_ms=scenario.think_time_ms,
        base_url=scenario.base_url,
        base_port=scenario.base_port,
        interface_ids=_parse_interface_ids(scenario.interface_ids),
        created_at=scenario.created_at,
        updated_at=scenario.updated_at,
    )


@router.post("", response_model=PerfScenarioOut, summary="新建性能测试场景")
def create_perf_scenario(
    project_id: int,
    payload: PerfScenarioIn,
    db: DbDep = None,
    current_user: CurrentUser = None,
):
    """创建性能测试场景（并发/循环/ramp-up/思考时间/目标地址/接口选择）。"""
    get_owned_project(db, project_id, current_user)
    scenario = PerfScenario(
        project_id=project_id,
        name=payload.name,
        description=payload.description,
        thread_count=payload.thread_count,
        loop_count=payload.loop_count,
        ramp_up=payload.ramp_up,
        think_time_ms=payload.think_time_ms,
        base_url=payload.base_url,
        base_port=payload.base_port,
        interface_ids=json.dumps(payload.interface_ids or [], ensure_ascii=False),
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return _to_out(scenario)


@router.get("", response_model=PerfScenarioListOut, summary="性能场景列表（分页 + 搜索）")
def list_perf_scenarios(
    project_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None, description="按名称模糊搜索"),
    db: DbDep = None,
    current_user: CurrentUser = None,
):
    get_owned_project(db, project_id, current_user)
    query = db.query(PerfScenario).filter(PerfScenario.project_id == project_id)
    if keyword:
        query = query.filter(PerfScenario.name.like(f"%{keyword}%"))
    total = query.count()
    items = (
        query.order_by(PerfScenario.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PerfScenarioListOut(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_out(s) for s in items],
    )


@router.get("/{scenario_id}", response_model=PerfScenarioOut, summary="性能场景详情")
def get_perf_scenario(
    project_id: int,
    scenario_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
):
    get_owned_project(db, project_id, current_user)
    scenario = db.get(PerfScenario, scenario_id)
    if not scenario or scenario.project_id != project_id:
        raise HTTPException(status_code=404, detail="性能场景不存在")
    return _to_out(scenario)


@router.patch("/{scenario_id}", response_model=PerfScenarioOut, summary="编辑性能场景")
def update_perf_scenario(
    project_id: int,
    scenario_id: int,
    payload: PerfScenarioUpdate,
    db: DbDep = None,
    current_user: CurrentUser = None,
):
    get_owned_project(db, project_id, current_user)
    scenario = db.get(PerfScenario, scenario_id)
    if not scenario or scenario.project_id != project_id:
        raise HTTPException(status_code=404, detail="性能场景不存在")
    data = payload.model_dump(exclude_unset=True)
    if "interface_ids" in data:
        data["interface_ids"] = json.dumps(
            data["interface_ids"] or [], ensure_ascii=False
        )
    for key, value in data.items():
        setattr(scenario, key, value)
    db.commit()
    db.refresh(scenario)
    return _to_out(scenario)


@router.delete("/{scenario_id}", status_code=204, summary="删除性能场景")
def delete_perf_scenario(
    project_id: int,
    scenario_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
):
    get_owned_project(db, project_id, current_user)
    scenario = db.get(PerfScenario, scenario_id)
    if not scenario or scenario.project_id != project_id:
        raise HTTPException(status_code=404, detail="性能场景不存在")
    db.delete(scenario)
    db.commit()


@router.get(
    "/{scenario_id}/export/jmeter",
    summary="导出性能场景为 JMeter 压测脚本（.jmx）",
)
def export_perf_scenario_jmeter(
    project_id: int,
    scenario_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> StreamingResponse:
    """按场景配置生成 JMeter 测试计划（并发/循环/ramp-up/思考时间可配）。"""
    get_owned_project(db, project_id, current_user)
    try:
        content = build_perf_jmeter_test_plan(db, scenario_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    scenario = db.get(PerfScenario, scenario_id)
    if scenario:
        from urllib.parse import quote

        ascii_name = "".join(
            c if (c.isascii() and (c.isalnum() or c in "._-")) else "_" for c in scenario.name
        )
        filename = f"perf_scenario_{scenario.id}_{ascii_name}.jmx"
        # 中文名走 RFC 5987（filename*，百分号编码），ASCII 兜底（filename）
        encoded_name = quote(f"{scenario.name}.jmx", safe="")
        content_disposition = (
            f"attachment; filename={filename}; filename*=UTF-8''{encoded_name}"
        )
    else:
        content_disposition = "attachment; filename=perf_scenario.jmx"
    return StreamingResponse(
        iter([content]),
        media_type="application/xml",
        headers={"Content-Disposition": content_disposition},
    )
