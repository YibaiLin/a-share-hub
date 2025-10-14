"""
健康检查接口
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from core.database import get_db_client
from models.schemas import Response, HealthResponse
from core.logger import logger


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=Response[HealthResponse])
async def health_check():
    """
    健康检查

    Returns:
        健康状态
    """
    return Response(
        code=200,
        message="healthy",
        data=HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
        ),
    )


@router.get("/db", response_model=Response[dict])
async def health_check_db():
    """
    数据库健康检查

    Returns:
        数据库连接状态
    """
    try:
        client = get_db_client()
        is_healthy = client.ping()

        if is_healthy:
            return Response(
                code=200,
                message="database healthy",
                data={
                    "status": "healthy",
                    "database": "clickhouse",
                    "timestamp": datetime.now().isoformat(),
                },
            )
        else:
            return Response(
                code=500,
                message="database unhealthy",
                data={
                    "status": "unhealthy",
                    "database": "clickhouse",
                    "timestamp": datetime.now().isoformat(),
                },
            )

    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return Response(
            code=500,
            message=f"database error: {str(e)}",
            data={
                "status": "error",
                "database": "clickhouse",
                "timestamp": datetime.now().isoformat(),
            },
        )


__all__ = ["router"]
