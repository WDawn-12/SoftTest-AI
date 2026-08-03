"""API v1 路由聚合。"""
from fastapi import APIRouter

from app.api.v1 import (
    auth,
    chat,
    dashboard,
    health,
    projects,
    requirements,
    systems,
    system,
    test_cases,
    test_points,
    users,
)

# 聚合 v1 版本全部子路由，后续业务模块在此挂载
api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(requirements.router)
api_router.include_router(test_points.router)
api_router.include_router(test_cases.router)
api_router.include_router(chat.router)
api_router.include_router(systems.router)
api_router.include_router(system.router)
api_router.include_router(dashboard.router)
