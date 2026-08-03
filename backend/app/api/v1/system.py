"""系统管理接口：设置与日志（仅管理员）。"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbDep, get_current_admin
from app.models.ai_call_log import AiCallLog
from app.models.operation_log import OperationLog
from app.models.user import User
from app.schemas.system import (
    AiCallLogListOut,
    AiCallLogOut,
    OperationLogListOut,
    OperationLogOut,
    SettingsOut,
    SettingsUpdate,
)
from app.services.system_settings_service import get_all_settings, update_settings

router = APIRouter(prefix="/system", tags=["系统管理"])

CurrentAdmin = Annotated[User, Depends(get_current_admin)]


@router.get("/settings", response_model=SettingsOut, summary="获取系统设置")
def read_settings(
    db: DbDep, _: CurrentAdmin = None
) -> SettingsOut:
    """读取模型配置、API Key 与 Prompt 模板。"""
    return SettingsOut(settings=get_all_settings(db))


@router.put("/settings", response_model=SettingsOut, summary="更新系统设置")
def write_settings(
    payload: SettingsUpdate,
    db: DbDep = None,
    _: CurrentAdmin = None,
) -> SettingsOut:
    """批量更新系统设置（仅白名单键生效）。"""
    return SettingsOut(settings=update_settings(db, payload.values))


@router.get("/logs/operations", response_model=OperationLogListOut, summary="操作日志")
def list_operation_logs(
    keyword: str | None = Query(default=None, max_length=100, description="关键字"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: DbDep = None,
    _: CurrentAdmin = None,
) -> OperationLogListOut:
    """分页查询操作日志。"""
    query = db.query(OperationLog)
    if keyword:
        query = query.filter(
            OperationLog.action.like(f"%{keyword}%")
            | OperationLog.module.like(f"%{keyword}%")
            | OperationLog.detail.like(f"%{keyword}%")
        )
    total = query.count()
    rows = (
        query.order_by(OperationLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    user_ids = {row.user_id for row in rows if row.user_id}
    usernames: dict[int, str] = {}
    if user_ids:
        from app.models.user import User

        users = db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        usernames = {uid: name for uid, name in users}
    items = [
        OperationLogOut(
            id=row.id,
            user_id=row.user_id,
            username=usernames.get(row.user_id) if row.user_id else None,
            action=row.action,
            module=row.module,
            detail=row.detail,
            ip=row.ip,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return OperationLogListOut(
        total=total, page=page, page_size=page_size, items=items
    )


@router.get("/logs/ai", response_model=AiCallLogListOut, summary="AI 调用日志")
def list_ai_call_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: DbDep = None,
    _: CurrentAdmin = None,
) -> AiCallLogListOut:
    """分页查询 AI 调用日志。"""
    query = db.query(AiCallLog)
    total = query.count()
    rows = (
        query.order_by(AiCallLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    user_ids = {row.user_id for row in rows if row.user_id}
    usernames: dict[int, str] = {}
    if user_ids:
        from app.models.user import User

        users = db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        usernames = {uid: name for uid, name in users}
    items = [
        AiCallLogOut(
            id=row.id,
            user_id=row.user_id,
            username=usernames.get(row.user_id) if row.user_id else None,
            agent=row.agent,
            provider=row.provider,
            prompt_length=row.prompt_length,
            response_length=row.response_length,
            duration_ms=row.duration_ms,
            status=row.status,
            error_message=row.error_message,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return AiCallLogListOut(total=total, page=page, page_size=page_size, items=items)
