"""测试点管理接口：列表、编辑、删除。"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DbDep, get_current_user, get_owned_project
from app.models.test_point import TestPoint
from app.models.user import User
from app.schemas.testpoint import TestPointListOut, TestPointOut, TestPointUpdate
from app.services.testpoint_service import build_testpoint_out

router = APIRouter(prefix="/projects/{project_id}/test-points", tags=["测试点管理"])

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=TestPointListOut, summary="测试点列表")
def list_test_points(
    project_id: int,
    requirement_id: int | None = Query(default=None, description="按需求筛选"),
    module_id: int | None = Query(default=None, description="按模块筛选"),
    category: str | None = Query(default=None, description="按类别筛选"),
    keyword: str | None = Query(default=None, max_length=100, description="关键字"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页条数"),
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> TestPointListOut:
    """分页查询项目下的测试点，支持多条件筛选。"""
    get_owned_project(db, project_id, current_user)
    query = db.query(TestPoint).filter(TestPoint.project_id == project_id)
    if requirement_id:
        query = query.filter(TestPoint.requirement_id == requirement_id)
    if module_id:
        query = query.filter(TestPoint.module_id == module_id)
    if category:
        query = query.filter(TestPoint.category == category)
    if keyword:
        query = query.filter(TestPoint.name.like(f"%{keyword}%"))

    total = query.count()
    rows = (
        query.order_by(TestPoint.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = build_testpoint_out(db, rows)
    return TestPointListOut(total=total, page=page, page_size=page_size, items=items)


@router.patch("/{test_point_id}", response_model=TestPointOut, summary="编辑测试点")
def update_test_point(
    project_id: int,
    test_point_id: int,
    payload: TestPointUpdate,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> TestPointOut:
    """人工编辑测试点内容或类别。"""
    get_owned_project(db, project_id, current_user)
    point = db.get(TestPoint, test_point_id)
    if point is None or point.project_id != project_id:
        raise HTTPException(status_code=404, detail="测试点不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(point, field, value)
    db.commit()
    db.refresh(point)
    return build_testpoint_out(db, [point])[0]


@router.delete(
    "/{test_point_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除测试点"
)
def delete_test_point(
    project_id: int,
    test_point_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> None:
    """删除单个测试点。"""
    get_owned_project(db, project_id, current_user)
    point = db.get(TestPoint, test_point_id)
    if point is None or point.project_id != project_id:
        raise HTTPException(status_code=404, detail="测试点不存在")
    db.delete(point)
    db.commit()
