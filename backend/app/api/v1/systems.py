"""被测系统管理接口（System Under Test）。"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbDep, get_current_user, get_owned_project
from app.models.project import Project
from app.models.user import User
from app.schemas.sut import SutIn, SutOut, SutUpdate, TestConnectionOut
from app.services.crypto_service import decrypt_password, encrypt_password
from app.services.sut_service import test_connection

router = APIRouter(prefix="/projects/{project_id}/system", tags=["被测系统管理"])

CurrentUser = Annotated[User, Depends(get_current_user)]

SUT_FIELDS = (
    "system_name",
    "test_url",
    "system_type",
    "browser_type",
    "login_username",
    "login_password",
    "system_description",
)


def _has_sut(project: Project) -> bool:
    """项目是否已绑定被测系统。"""
    return any(getattr(project, field) for field in SUT_FIELDS)


def _to_out(project: Project) -> SutOut:
    """组装响应（密码返回解密值）。"""
    return SutOut(
        system_name=project.system_name,
        test_url=project.test_url,
        system_type=project.system_type,
        browser_type=project.browser_type,
        login_username=project.login_username,
        login_password=decrypt_password(project.login_password),
        system_description=project.system_description,
    )


def _apply_sut(project: Project, values: dict) -> None:
    """应用被测系统字段（密码加密存储；空值不覆盖已有密码）。"""
    for field, value in values.items():
        if field == "login_password":
            if value not in (None, ""):
                setattr(project, field, encrypt_password(value))
            continue
        setattr(project, field, value)


@router.get("", response_model=SutOut, summary="获取被测系统")
def get_sut(
    project_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> SutOut:
    """获取项目绑定的被测系统信息。"""
    project = get_owned_project(db, project_id, current_user)
    if not _has_sut(project):
        raise HTTPException(status_code=404, detail="该项目尚未配置被测系统")
    return _to_out(project)


@router.post(
    "",
    response_model=SutOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建被测系统",
)
def create_sut(
    project_id: int,
    payload: SutIn,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> SutOut:
    """为项目绑定被测系统（每项目仅一个，已存在时返回 409）。"""
    project = get_owned_project(db, project_id, current_user)
    if _has_sut(project):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该项目已绑定被测系统，请使用更新接口",
        )
    _apply_sut(project, payload.model_dump())
    db.commit()
    db.refresh(project)
    return _to_out(project)


@router.put("", response_model=SutOut, summary="更新被测系统")
def update_sut(
    project_id: int,
    payload: SutUpdate,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> SutOut:
    """更新被测系统信息（未传字段保持不变，密码留空保持原值）。"""
    project = get_owned_project(db, project_id, current_user)
    if not _has_sut(project):
        raise HTTPException(status_code=404, detail="该项目尚未配置被测系统")
    _apply_sut(project, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(project)
    return _to_out(project)


@router.delete(
    "", status_code=status.HTTP_204_NO_CONTENT, summary="删除被测系统"
)
def delete_sut(
    project_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> None:
    """解除项目与被测系统的绑定。"""
    project = get_owned_project(db, project_id, current_user)
    if not _has_sut(project):
        raise HTTPException(status_code=404, detail="该项目尚未配置被测系统")
    for field in SUT_FIELDS:
        setattr(project, field, None)
    db.commit()


@router.post(
    "/test-connection",
    response_model=TestConnectionOut,
    summary="测试连接（检测目标网址）",
)
async def test_sut_connection(
    project_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> TestConnectionOut:
    """请求目标 URL，检测 HTTP 状态码、网络连接与响应时间。"""
    project = get_owned_project(db, project_id, current_user)
    result = await test_connection(project.test_url)
    return TestConnectionOut(**result)
