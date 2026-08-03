"""AITestAgent 后端入口（FastAPI）。"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.api.v1 import api_router
from app.api.middleware import OperationLogMiddleware
from app.core.config import settings

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("aitest")

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

# 操作日志中间件
app.add_middleware(OperationLogMiddleware)

# 注册 API 路由（统一前缀 /api/v1）
app.include_router(api_router, prefix="/api/v1")


# 全局异常处理：未捕获异常统一返回 500 JSON，避免泄露内部错误
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("未处理异常: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500, content={"detail": "服务器内部错误，请稍后重试"}
    )


@app.get("/", summary="服务信息", tags=["系统"])
def root() -> dict:
    """根路径：返回服务基本信息。"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
