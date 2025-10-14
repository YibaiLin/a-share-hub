"""
FastAPI主应用

提供A股数据查询API服务
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.logger import setup_logger, logger
from core.database import get_db_client, close_db_client
from api.routes import health, daily
from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时：初始化日志、连接数据库
    关闭时：关闭数据库连接
    """
    # 启动
    setup_logger()
    logger.info("=" * 60)
    logger.info(f"{settings.app_name} API服务启动中...")
    logger.info("=" * 60)

    # 测试数据库连接
    try:
        client = get_db_client()
        if client.ping():
            logger.info("✅ ClickHouse连接正常")
        else:
            logger.warning("⚠️  ClickHouse连接异常")
    except Exception as e:
        logger.error(f"❌ ClickHouse连接失败: {e}")

    logger.info(f"API服务启动成功: http://{settings.api_host}:{settings.api_port}")
    logger.info(f"Swagger文档: http://{settings.api_host}:{settings.api_port}/docs")

    yield

    # 关闭
    logger.info("API服务关闭中...")
    close_db_client()
    logger.info("API服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="中国A股数据采集和管理系统 API",
    version="0.7.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router)
app.include_router(daily.router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": "0.7.0",
        "docs": "/docs",
        "health": "/health",
    }


__all__ = ["app"]
