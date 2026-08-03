"""项目管理接口：CRUD + 分页 + 搜索。"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_

from app.api.deps import DbDep, get_current_user
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectListOut, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["项目管理"])

CurrentUser = Annotated[User, Depends(get_current_user)]


def get_owned_project(db: DbDep, project_id: int, current_user: User) -> Project:
    """获取项目并校验归属：仅项目创建人或管理员可操作。"""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    # 非管理员查看他人项目时返回 404，避免泄露项目存在性
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.post(
    "",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建项目",
)
def create_project(
    payload: ProjectCreate, db: DbDep, current_user: CurrentUser
) -> Project:
    """创建项目（默认状态 active，创建人为当前用户）。"""
    project = Project(
        name=payload.name,
        description=payload.description,
        status="active",
        owner_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=ProjectListOut, summary="项目列表（分页 + 搜索）")
def list_projects(
    db: DbDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页条数"),
    keyword: str | None = Query(default=None, max_length=100, description="搜索关键字"),
) -> ProjectListOut:
    """分页查询项目；管理员可查看全部，普通用户仅查看自己的项目。"""
    query = db.query(Project)
    if current_user.role != "admin":
        query = query.filter(Project.owner_id == current_user.id)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(Project.name.like(like), Project.description.like(like))
        )

    total = query.count()
    items = (
        query.order_by(Project.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ProjectListOut(total=total, page=page, page_size=page_size, items=items)


@router.get("/{project_id}", response_model=ProjectOut, summary="项目详情")
def get_project(
    project_id: int, db: DbDep, current_user: CurrentUser
) -> Project:
    """获取单个项目详情。"""
    return get_owned_project(db, project_id, current_user)


@router.patch("/{project_id}", response_model=ProjectOut, summary="更新项目")
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: DbDep,
    current_user: CurrentUser,
) -> Project:
    """部分更新项目（名称、描述、状态），仅创建人或管理员可操作。"""
    project = get_owned_project(db, project_id, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除项目")
def delete_project(
    project_id: int, db: DbDep, current_user: CurrentUser
) -> None:
    """删除项目（关联的需求、模块、测试用例由数据库级联删除）。"""
    project = get_owned_project(db, project_id, current_user)
    db.delete(project)
    db.commit()
