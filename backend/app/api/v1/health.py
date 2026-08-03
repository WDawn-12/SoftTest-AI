"""健康检查接口。"""
from fastapi import APIRouter

router = APIRouter(tags=["系统"])


@router.get("/health", summary="健康检查")
def health_check() -> dict:
    """供部署探活与前端连通性检查使用。"""
    return {"status": "ok", "message": "AITestAgent 后端服务运行正常"}
