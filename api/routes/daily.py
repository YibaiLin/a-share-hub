"""
日线数据查询接口
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from storage.clickhouse_handler import ClickHouseHandler
from api.dependencies import get_db_handler
from models.schemas import Response, DailyDataResponse, DailyDataItem
from utils.data_transform import int_to_price
from core.logger import logger


router = APIRouter(prefix="/api/daily", tags=["Daily Data"])


@router.get("/{ts_code}", response_model=Response[DailyDataResponse])
async def get_daily_data(
    ts_code: str,
    start_date: Optional[str] = Query(
        None,
        description="开始日期(YYYYMMDD)",
        pattern="^\\d{8}$"
    ),
    end_date: Optional[str] = Query(
        None,
        description="结束日期(YYYYMMDD)",
        pattern="^\\d{8}$"
    ),
    limit: Optional[int] = Query(
        100,
        description="限制返回数量",
        ge=1,
        le=1000
    ),
    handler: ClickHouseHandler = Depends(get_db_handler),
):
    """
    查询日线数据

    Args:
        ts_code: 股票代码（如000001.SZ）
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        limit: 限制返回数量（默认100，最大1000）
        handler: 数据库Handler（依赖注入）

    Returns:
        日线数据列表

    Examples:
        - GET /api/daily/000001.SZ
        - GET /api/daily/000001.SZ?start_date=20240101&end_date=20240131
        - GET /api/daily/000001.SZ?limit=10
    """
    try:
        # 查询数据
        raw_data = handler.query_daily(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        # 转换数据（价格还原为浮点数）
        data_items = []
        for record in raw_data:
            item = DailyDataItem(
                ts_code=record["ts_code"],
                trade_date=record["trade_date"],
                open=int_to_price(record["open"]),
                high=int_to_price(record["high"]),
                low=int_to_price(record["low"]),
                close=int_to_price(record["close"]),
                pre_close=int_to_price(record["pre_close"]),
                change=int_to_price(record["change"]),
                pct_change=(
                    record["pct_change"] / 100
                    if record["pct_change"] != -1
                    else None
                ),
                volume=record["volume"] if record["volume"] != -1 else None,
                amount=int_to_price(record["amount"]),
            )
            data_items.append(item)

        response_data = DailyDataResponse(
            ts_code=ts_code,
            count=len(data_items),
            data=data_items,
        )

        return Response(
            code=200,
            message="success",
            data=response_data,
        )

    except Exception as e:
        logger.error(f"查询日线数据失败: {e}, ts_code={ts_code}")
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


@router.get("/{ts_code}/latest", response_model=Response[Optional[DailyDataItem]])
async def get_latest_daily(
    ts_code: str,
    handler: ClickHouseHandler = Depends(get_db_handler),
):
    """
    获取最新一条日线数据

    Args:
        ts_code: 股票代码
        handler: 数据库Handler

    Returns:
        最新的日线数据
    """
    try:
        raw_data = handler.query_daily(
            ts_code=ts_code,
            limit=1,
        )

        if not raw_data:
            return Response(
                code=404,
                message="no data found",
                data=None,
            )

        record = raw_data[0]
        item = DailyDataItem(
            ts_code=record["ts_code"],
            trade_date=record["trade_date"],
            open=int_to_price(record["open"]),
            high=int_to_price(record["high"]),
            low=int_to_price(record["low"]),
            close=int_to_price(record["close"]),
            pre_close=int_to_price(record["pre_close"]),
            change=int_to_price(record["change"]),
            pct_change=(
                record["pct_change"] / 100
                if record["pct_change"] != -1
                else None
            ),
            volume=record["volume"] if record["volume"] != -1 else None,
            amount=int_to_price(record["amount"]),
        )

        return Response(
            code=200,
            message="success",
            data=item,
        )

    except Exception as e:
        logger.error(f"查询最新日线失败: {e}, ts_code={ts_code}")
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


__all__ = ["router"]
