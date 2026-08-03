"""测试用例管理接口：列表、编辑、删除。"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DbDep, get_current_user, get_owned_project
from app.models.test_case import TestCase
from app.models.user import User
from app.schemas.testcase import TestCaseListOut, TestCaseOut, TestCaseUpdate
from app.services.testcase_service import build_testcase_out

router = APIRouter(prefix="/projects/{project_id}/test-cases", tags=["测试用例管理"])

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=TestCaseListOut, summary="测试用例列表")
def list_test_cases(
    project_id: int,
    requirement_id: int | None = Query(default=None, description="按需求筛选"),
    module_id: int | None = Query(default=None, description="按模块筛选"),
    priority: str | None = Query(default=None, description="按优先级筛选"),
    keyword: str | None = Query(default=None, max_length=100, description="关键字"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页条数"),
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> TestCaseListOut:
    """分页查询项目下的测试用例，支持多条件筛选。"""
    get_owned_project(db, project_id, current_user)
    query = db.query(TestCase).filter(TestCase.project_id == project_id)
    if requirement_id:
        query = query.filter(TestCase.requirement_id == requirement_id)
    if module_id:
        query = query.filter(TestCase.module_id == module_id)
    if priority:
        query = query.filter(TestCase.priority == priority)
    if keyword:
        query = query.filter(
            TestCase.case_no.like(f"%{keyword}%")
            | TestCase.title.like(f"%{keyword}%")
            | TestCase.test_point.like(f"%{keyword}%")
        )

    total = query.count()
    rows = (
        query.order_by(TestCase.case_no.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = build_testcase_out(db, rows)
    return TestCaseListOut(total=total, page=page, page_size=page_size, items=items)


@router.patch("/{test_case_id}", response_model=TestCaseOut, summary="编辑测试用例")
def update_test_case(
    project_id: int,
    test_case_id: int,
    payload: TestCaseUpdate,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> TestCaseOut:
    """人工编辑测试用例内容（功能、测试点、优先级、步骤等）。"""
    get_owned_project(db, project_id, current_user)
    case = db.get(TestCase, test_case_id)
    if case is None or case.project_id != project_id:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    db.commit()
    db.refresh(case)
    return build_testcase_out(db, [case])[0]


@router.delete(
    "/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除测试用例"
)
def delete_test_case(
    project_id: int,
    test_case_id: int,
    db: DbDep = None,
    current_user: CurrentUser = None,
) -> None:
    """删除单个测试用例。"""
    get_owned_project(db, project_id, current_user)
    case = db.get(TestCase, test_case_id)
    if case is None or case.project_id != project_id:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    db.delete(case)
    db.commit()
