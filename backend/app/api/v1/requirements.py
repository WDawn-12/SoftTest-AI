"""需求文档接口：上传（Word/PDF/TXT/Markdown）与查询管理。"""
import json
import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse

from app.api.deps import DbDep, get_current_user, get_owned_project
from app.core.config import settings
from app.models.requirement import Requirement
from app.models.user import User
from app.schemas.requirement import (
    ParseResultOut,
    RequirementDetailOut,
    RequirementListOut,
    RequirementOut,
)
from app.schemas.testpoint import TestPointOut
from app.schemas.testcase import TestCaseOut
from app.services.requirement_service import run_requirement_parse
from app.services.testcase_service import build_testcase_out, run_testcase_generation
from app.services.testpoint_service import build_testpoint_out, run_testpoint_generation
from app.services.document_parser import extract_text
from app.services.sse import sse_event

router = APIRouter(prefix="/projects/{project_id}/requirements", tags=["需求文档"])

# 允许的文件类型：扩展名 -> 存储类型
ALLOWED_EXTENSIONS = {
    "docx": "docx",
    "pdf": "pdf",
    "txt": "txt",
    "md": "md",
    "markdown": "md",
}

CurrentUser = Annotated[User, Depends(get_current_user)]


def _progress_stream(stage_messages: dict[str, str], runner, *args) -> Iterator[str]:
    """把一次阻塞的 AI 生成任务包装为 SSE 阶段进度事件流。

    事件顺序：status(llm) -> status(save) -> result / error
    runner 返回 JSON 可序列化的结果。
    """
    try:
        yield sse_event("status", {"stage": "llm", "message": stage_messages.get("llm", "正在调用 AI 生成...")})
        time.sleep(0.2)  # 让阶段进度可见（真实 LLM 调用耗时较长，可忽略）
        result = runner(*args)
        yield sse_event("status", {"stage": "save", "message": stage_messages.get("save", "结果已保存")})
        yield sse_event("result", result)
    except Exception as exc:
        yield sse_event("error", {"message": str(exc)})


def _get_requirement(
    db: DbDep, project_id: int, requirement_id: int, current_user: User
) -> Requirement:
    """获取需求文档并校验项目权限。"""
    get_owned_project(db, project_id, current_user)
    requirement = db.get(Requirement, requirement_id)
    if requirement is None or requirement.project_id != project_id:
        raise HTTPException(status_code=404, detail="需求文档不存在")
    return requirement


def _load_result(requirement: Requirement) -> dict | None:
    """将 parse_result 字段解析为字典。"""
    if not requirement.parse_result:
        return None
    try:
        return json.loads(requirement.parse_result)
    except json.JSONDecodeError:
        return None


@router.post(
    "/upload",
    response_model=RequirementOut,
    status_code=status.HTTP_201_CREATED,
    summary="上传需求文档",
)
async def upload_requirement(
    project_id: int,
    file: UploadFile = File(..., description="Word/PDF/TXT/Markdown 文件"),
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> Requirement:
    """上传需求文档并提取纯文本内容（AI 解析将在下一阶段进行）。"""
    get_owned_project(db, project_id, current_user)

    # 校验扩展名
    original_name = file.filename or ""
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 Word(docx)、PDF、TXT、Markdown(md/markdown) 文件",
        )

    # 读取并校验大小
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小超过限制（最大 20MB）",
        )

    # 保存文件（随机文件名，避免重名与路径穿越）
    upload_dir = Path(settings.UPLOAD_DIR).resolve() / str(project_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{Path(original_name).suffix.lower()}"
    file_path = upload_dir / stored_name
    file_path.write_bytes(content)

    # 提取文本内容；失败时记录原因，解析状态置为 failed
    requirement = Requirement(
        project_id=project_id,
        file_name=original_name,
        file_path=str(file_path),
        file_type=ALLOWED_EXTENSIONS[ext],
        file_size=len(content),
        parse_status="pending",
    )
    try:
        requirement.content = extract_text(str(file_path), requirement.file_type)
    except ValueError as exc:
        requirement.parse_status = "failed"
        requirement.error_message = str(exc)

    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return requirement


@router.get("", response_model=RequirementListOut, summary="需求文档列表")
def list_requirements(
    project_id: int,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页条数"),
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> RequirementListOut:
    """分页查询项目下的需求文档。"""
    get_owned_project(db, project_id, current_user)
    query = db.query(Requirement).filter(Requirement.project_id == project_id)
    total = query.count()
    items = (
        query.order_by(Requirement.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return RequirementListOut(total=total, page=page, page_size=page_size, items=items)


@router.get("/{requirement_id}", response_model=RequirementDetailOut, summary="需求文档详情")
def get_requirement(
    project_id: int,
    requirement_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> Requirement:
    """获取需求文档详情（含提取的文本内容）。"""
    return _get_requirement(db, project_id, requirement_id, current_user)


@router.delete(
    "/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除需求文档",
)
def delete_requirement(
    project_id: int,
    requirement_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> None:
    """删除需求文档（同时删除已保存的文件）。"""
    requirement = _get_requirement(db, project_id, requirement_id, current_user)
    file_path = Path(requirement.file_path)
    if file_path.exists():
        file_path.unlink()
    db.delete(requirement)
    db.commit()


@router.post(
    "/{requirement_id}/parse",
    response_model=ParseResultOut,
    summary="AI 解析需求文档",
)
def parse_requirement(
    project_id: int,
    requirement_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> ParseResultOut:
    """调用 Requirement Agent 解析需求，保存结构化结果与功能模块。"""
    requirement = _get_requirement(db, project_id, requirement_id, current_user)
    run_requirement_parse(db, requirement, current_user.id)
    return ParseResultOut(
        requirement_id=requirement.id,
        parse_status=requirement.parse_status,
        error_message=requirement.error_message,
        result=_load_result(requirement),
    )


@router.get(
    "/{requirement_id}/parse-result",
    response_model=ParseResultOut,
    summary="获取 AI 解析结果",
)
def get_parse_result(
    project_id: int,
    requirement_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> ParseResultOut:
    """查询已保存的解析结果（供前端可视化展示）。"""
    requirement = _get_requirement(db, project_id, requirement_id, current_user)
    return ParseResultOut(
        requirement_id=requirement.id,
        parse_status=requirement.parse_status,
        error_message=requirement.error_message,
        result=_load_result(requirement),
    )


@router.post(
    "/{requirement_id}/test-points/generate",
    response_model=list[TestPointOut],
    summary="生成测试点（TestPoint Agent）",
)
def generate_test_points(
    project_id: int,
    requirement_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> list[TestPointOut]:
    """调用 TestPoint Agent 按功能点生成五类测试点并保存（可重新生成）。"""
    requirement = _get_requirement(db, project_id, requirement_id, current_user)
    try:
        created = run_testpoint_generation(db, requirement, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return build_testpoint_out(db, created)


@router.post(
    "/{requirement_id}/test-cases/generate",
    response_model=list[TestCaseOut],
    summary="生成测试用例（TestCase Agent）",
)
def generate_test_cases(
    project_id: int,
    requirement_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> list[TestCaseOut]:
    """调用 TestCase Agent 根据测试点生成测试用例（含编号，可重新生成）。"""
    requirement = _get_requirement(db, project_id, requirement_id, current_user)
    try:
        created = run_testcase_generation(db, requirement, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return build_testcase_out(db, created)


@router.post(
    "/{requirement_id}/parse/stream",
    summary="AI 解析需求文档（SSE 流式返回）",
    responses={
        200: {
            "description": "SSE 事件流：status（阶段进度）/ result（解析结果）/ error",
            "content": {"text/event-stream": {}},
        }
    },
)
async def parse_requirement_stream(
    project_id: int,
    requirement_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> StreamingResponse:
    """流式解析需求：先推送调用进度，完成后推送完整结构化结果。"""
    requirement = _get_requirement(db, project_id, requirement_id, current_user)

    def run_parse():
        run_requirement_parse(db, requirement, current_user.id)
        return {
            "requirement_id": requirement.id,
            "parse_status": requirement.parse_status,
            "error_message": requirement.error_message,
            "result": _load_result(requirement),
        }

    return StreamingResponse(
        _progress_stream(
            {"llm": "正在调用 Requirement Agent 解析需求文档...", "save": "解析完成，结构化结果已保存"},
            run_parse,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/{requirement_id}/test-points/generate/stream",
    summary="生成测试点（SSE 流式返回）",
    responses={
        200: {
            "description": "SSE 事件流：status（阶段进度）/ result（测试点列表）/ error",
            "content": {"text/event-stream": {}},
        }
    },
)
async def generate_test_points_stream(
    project_id: int,
    requirement_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> StreamingResponse:
    """流式生成测试点：先推送调用进度，完成后推送测试点列表。"""
    requirement = _get_requirement(db, project_id, requirement_id, current_user)

    def run_generate():
        created = run_testpoint_generation(db, requirement, current_user.id)
        return jsonable_encoder(build_testpoint_out(db, created))

    return StreamingResponse(
        _progress_stream(
            {"llm": "正在调用 TestPoint Agent 按五类维度生成测试点...", "save": "测试点已保存"},
            run_generate,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/{requirement_id}/test-cases/generate/stream",
    summary="生成测试用例（SSE 流式返回）",
    responses={
        200: {
            "description": "SSE 事件流：status（阶段进度）/ result（测试用例列表）/ error",
            "content": {"text/event-stream": {}},
        }
    },
)
async def generate_test_cases_stream(
    project_id: int,
    requirement_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> StreamingResponse:
    """流式生成测试用例：先推送调用进度，完成后推送测试用例列表。"""
    requirement = _get_requirement(db, project_id, requirement_id, current_user)

    def run_generate():
        created = run_testcase_generation(db, requirement, current_user.id)
        return jsonable_encoder(build_testcase_out(db, created))

    return StreamingResponse(
        _progress_stream(
            {"llm": "正在调用 TestCase Agent 生成测试用例（含测试数据）...", "save": "测试用例已保存"},
            run_generate,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
