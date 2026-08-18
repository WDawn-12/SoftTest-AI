"""接口测试接口：接口管理、OpenAPI 导入、接口用例生成与管理。"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.api.deps import DbDep, get_current_user, get_owned_project
from app.models.interface import Interface
from app.models.interface_test_case import InterfaceTestCase
from app.models.user import User
from app.schemas.interface_test import (
    InterfaceCaseListOut,
    InterfaceCaseOut,
    InterfaceCaseUpdate,
    InterfaceIn,
    InterfaceListOut,
    InterfaceOut,
    InterfaceUpdate,
    OpenApiImportIn,
)
from app.services.interface_test_service import (
    build_interface_case_out,
    build_interface_out,
    build_postman_collection,
    export_interface_cases_excel,
    run_interface_case_generation,
)

router = APIRouter(prefix="/projects/{project_id}", tags=["接口测试"])

CurrentUser = Annotated[User, Depends(get_current_user)]


# ---------- 接口定义 CRUD ----------
@router.get(
    "/interfaces", response_model=InterfaceListOut, summary="接口列表"
)
def list_interfaces(
    project_id: int,
    keyword: str | None = Query(default=None, max_length=100, description="关键字"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> InterfaceListOut:
    """分页查询项目下的接口定义。"""
    get_owned_project(db, project_id, current_user)
    query = db.query(Interface).filter(Interface.project_id == project_id)
    if keyword:
        query = query.filter(
            Interface.name.like(f"%{keyword}%")
            | Interface.path.like(f"%{keyword}%")
        )
    total = query.count()
    rows = (
        query.order_by(Interface.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return InterfaceListOut(
        total=total, page=page, page_size=page_size, items=build_interface_out(db, rows)
    )


@router.post("/interfaces", response_model=InterfaceOut, summary="新增接口")
def create_interface(
    project_id: int,
    payload: InterfaceIn,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> InterfaceOut:
    """手动录入接口定义。"""
    get_owned_project(db, project_id, current_user)
    interface = Interface(
        project_id=project_id,
        name=payload.name,
        method=payload.method,
        path=payload.path,
        summary=payload.summary,
        headers=payload.headers,
        params=payload.params,
        body=payload.body,
    )
    db.add(interface)
    db.commit()
    db.refresh(interface)
    return build_interface_out(db, [interface])[0]


@router.post(
    "/interfaces/import-openapi",
    response_model=InterfaceListOut,
    summary="从 OpenAPI（Swagger）JSON 导入接口",
)
def import_openapi(
    project_id: int,
    payload: OpenApiImportIn,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> InterfaceListOut:
    """解析 OpenAPI 3.x / Swagger 2.0 文档，批量导入接口定义。"""
    get_owned_project(db, project_id, current_user)
    spec = payload.spec

    # 兼容 OpenAPI 3.x（paths 下带 method）与 Swagger 2.0（paths 带 operationId）
    paths = spec.get("paths") or {}
    if not isinstance(paths, dict) or not paths:
        raise HTTPException(status_code=400, detail="OpenAPI 文档中未找到 paths")

    imported: list[Interface] = []
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method in ("get", "post", "put", "delete", "patch"):
            operation = item.get(method)
            if not isinstance(operation, dict):
                continue
            name = operation.get("summary") or operation.get("operationId") or path
            interface = Interface(
                project_id=project_id,
                name=str(name)[:200],
                method=method.upper(),
                path=path,
                summary=str(operation.get("description") or "")[:500] or None,
                params=(
                    _params_to_json(operation.get("parameters"))
                    if operation.get("parameters")
                    else None
                ),
                body=_request_body_to_json(operation.get("requestBody")),
            )
            db.add(interface)
            imported.append(interface)
    db.commit()
    for interface in imported:
        db.refresh(interface)
    return InterfaceListOut(
        total=len(imported), page=1, page_size=len(imported), items=build_interface_out(db, imported)
    )


@router.patch("/interfaces/{interface_id}", response_model=InterfaceOut, summary="编辑接口")
def update_interface(
    project_id: int,
    interface_id: int,
    payload: InterfaceUpdate,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> InterfaceOut:
    """编辑接口定义。"""
    get_owned_project(db, project_id, current_user)
    interface = db.get(Interface, interface_id)
    if interface is None or interface.project_id != project_id:
        raise HTTPException(status_code=404, detail="接口不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(interface, field, value)
    db.commit()
    db.refresh(interface)
    return build_interface_out(db, [interface])[0]


@router.delete(
    "/interfaces/{interface_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除接口",
)
def delete_interface(
    project_id: int,
    interface_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> None:
    """删除接口定义（关联用例保留但 interface_id 置空）。"""
    get_owned_project(db, project_id, current_user)
    interface = db.get(Interface, interface_id)
    if interface is None or interface.project_id != project_id:
        raise HTTPException(status_code=404, detail="接口不存在")
    db.delete(interface)
    db.commit()


# ---------- 接口用例 ----------
@router.post(
    "/interfaces/generate-cases",
    response_model=InterfaceCaseListOut,
    summary="生成接口测试用例（AI）",
)
def generate_interface_cases(
    project_id: int,
    payload: dict | None = None,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> InterfaceCaseListOut:
    """调用 InterfaceTestCase Agent 生成接口测试用例。

    请求体可选：{"interface_ids": [1,2]} 指定生成部分接口；缺省生成全部。
    """
    get_owned_project(db, project_id, current_user)
    interface_ids = (payload or {}).get("interface_ids")
    try:
        created = run_interface_case_generation(
            db, project_id, current_user.id, interface_ids
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return InterfaceCaseListOut(
        total=len(created), page=1, page_size=len(created), items=build_interface_case_out(db, created)
    )


@router.get(
    "/interface-cases",
    response_model=InterfaceCaseListOut,
    summary="接口测试用例列表",
)
def list_interface_cases(
    project_id: int,
    interface_id: int | None = Query(default=None, description="按接口筛选"),
    category: str | None = Query(default=None, description="按类别筛选"),
    keyword: str | None = Query(default=None, max_length=100, description="关键字"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页条数"),
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> InterfaceCaseListOut:
    """分页查询项目下的接口测试用例。"""
    get_owned_project(db, project_id, current_user)
    query = db.query(InterfaceTestCase).filter(
        InterfaceTestCase.project_id == project_id
    )
    if interface_id:
        query = query.filter(InterfaceTestCase.interface_id == interface_id)
    if category:
        query = query.filter(InterfaceTestCase.category == category)
    if keyword:
        query = query.filter(
            InterfaceTestCase.title.like(f"%{keyword}%")
            | InterfaceTestCase.path.like(f"%{keyword}%")
            | InterfaceTestCase.case_no.like(f"%{keyword}%")
        )
    total = query.count()
    rows = (
        query.order_by(InterfaceTestCase.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = build_interface_case_out(db, rows)
    return InterfaceCaseListOut(total=total, page=page, page_size=page_size, items=items)


@router.patch(
    "/interface-cases/{case_id}",
    response_model=InterfaceCaseOut,
    summary="编辑接口测试用例",
)
def update_interface_case(
    project_id: int,
    case_id: int,
    payload: InterfaceCaseUpdate,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> InterfaceCaseOut:
    """人工编辑接口测试用例。"""
    get_owned_project(db, project_id, current_user)
    case = db.get(InterfaceTestCase, case_id)
    if case is None or case.project_id != project_id:
        raise HTTPException(status_code=404, detail="接口用例不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    db.commit()
    db.refresh(case)
    return build_interface_case_out(db, [case])[0]


@router.delete(
    "/interface-cases/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除接口测试用例",
)
def delete_interface_case(
    project_id: int,
    case_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> None:
    """删除单个接口测试用例。"""
    get_owned_project(db, project_id, current_user)
    case = db.get(InterfaceTestCase, case_id)
    if case is None or case.project_id != project_id:
        raise HTTPException(status_code=404, detail="接口用例不存在")
    db.delete(case)
    db.commit()


@router.get("/interface-cases/export", summary="导出接口测试用例 Excel")
def export_interface_cases(
    project_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> StreamingResponse:
    """导出项目下全部接口测试用例为 Excel（与用例导出格式一致）。"""
    get_owned_project(db, project_id, current_user)
    content = export_interface_cases_excel(db, project_id)
    import io

    return StreamingResponse(
        io.BytesIO(content),
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                "attachment; filename=interface_test_cases.xlsx"
            )
        },
    )


@router.get(
    "/interface-cases/export/postman",
    summary="导出接口测试用例为 Postman/Apifox Collection JSON",
)
def export_interface_cases_postman(
    project_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> StreamingResponse:
    """导出项目下全部接口测试用例为 Postman Collection v2.1 JSON（Apifox 兼容）。

    导入后配置环境变量 base_url 即可直接发送请求。
    """
    get_owned_project(db, project_id, current_user)
    collection = build_postman_collection(db, project_id)
    import json

    content = json.dumps(collection, ensure_ascii=False, indent=2).encode("utf-8")
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={
            "Content-Disposition": (
                "attachment; filename=interface_test_cases.postman_collection.json"
            )
        },
    )


# ---------- 工具函数 ----------
def _params_to_json(parameters: list) -> str | None:
    """将 OpenAPI parameters 简化为查询参数 JSON 文本。"""
    rows = []
    for param in parameters:
        if not isinstance(param, dict):
            continue
        rows.append(
            {
                "name": param.get("name"),
                "in": param.get("in"),
                "required": bool(param.get("required")),
                "type": (param.get("schema") or {}).get("type")
                if isinstance(param.get("schema"), dict)
                else None,
                "description": param.get("description") or "",
            }
        )
    import json

    return json.dumps(rows, ensure_ascii=False) if rows else None


def _request_body_to_json(request_body: object) -> str | None:
    """将 OpenAPI requestBody 简化为 JSON 文本。"""
    if not isinstance(request_body, dict):
        return None
    import json

    return json.dumps(request_body, ensure_ascii=False)
