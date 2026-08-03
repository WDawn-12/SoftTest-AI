"""AITestAgent 后端入口（FastAPI）。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings

# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    description="基于 AI Agent 的软件测试辅助平台后端 API",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
)

# CORS 配置：允许前端开发服务器跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由（统一前缀 /api/v1）
app.include_router(api_router, prefix="/api/v1")


@app.get("/", summary="服务信息", tags=["系统"])
def root() -> dict:
    """根路径：返回服务基本信息。"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
