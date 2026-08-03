"""仪表盘接口。"""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.api.deps import DbDep, get_current_user
from app.models.chat_history import ChatHistory
from app.models.project import Project
from app.models.requirement import Requirement
from app.models.test_case import TestCase
from app.models.test_point import TestPoint
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])

CurrentUser = Annotated[User, Depends(get_current_user)]


class RecentProject(BaseModel):
    """最近项目摘要。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str
    created_at: datetime


class DashboardStatsOut(BaseModel):
    """仪表盘统计数据。"""

    project_count: int
    requirement_count: int
    test_point_count: int
    test_case_count: int
    chat_count: int
    recent_projects: list[RecentProject]


@router.get("/stats", response_model=DashboardStatsOut, summary="仪表盘统计")
def dashboard_stats(
    db: DbDep, current_user: CurrentUser = None
) -> DashboardStatsOut:
    """统计当前用户项目下的需求、测试点、测试用例与聊天记录数。"""
    projects = (
        db.query(Project)
        .filter(Project.owner_id == current_user.id)
        .order_by(Project.id.desc())
        .all()
    )
    project_ids = [p.id for p in projects]
    if not project_ids:
        return DashboardStatsOut(
            project_count=0,
            requirement_count=0,
            test_point_count=0,
            test_case_count=0,
            chat_count=0,
            recent_projects=[],
        )
    requirement_count = (
        db.query(Requirement).filter(Requirement.project_id.in_(project_ids)).count()
    )
    test_point_count = (
        db.query(TestPoint).filter(TestPoint.project_id.in_(project_ids)).count()
    )
    test_case_count = (
        db.query(TestCase).filter(TestCase.project_id.in_(project_ids)).count()
    )
    chat_count = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.project_id.in_(project_ids),
            ChatHistory.user_id == current_user.id,
        )
        .count()
    )
    recent = projects[:5]
    return DashboardStatsOut(
        project_count=len(projects),
        requirement_count=requirement_count,
        test_point_count=test_point_count,
        test_case_count=test_case_count,
        chat_count=chat_count,
        recent_projects=[RecentProject.model_validate(p) for p in recent],
    )
