"""
API响应模型

定义API接口的请求和响应数据结构
"""

from typing import Optional, Any, Generic, TypeVar
from datetime import date
from pydantic import BaseModel, Field, ConfigDict


T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    """通用API响应"""

    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="消息")
    data: Optional[T] = Field(default=None, description="数据")


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(..., description="状态：healthy/unhealthy")
    services: dict[str, bool] = Field(default_factory=dict, description="各服务状态")
    timestamp: str = Field(..., description="检查时间")


class DailyDataItem(BaseModel):
    """日线数据项（API返回）"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ts_code": "000001.SZ",
                "trade_date": "20240115",
                "open": 10.5,
                "high": 10.7,
                "low": 10.4,
                "close": 10.6,
                "pre_close": 10.45,
                "change": 0.15,
                "pct_change": 1.5,
                "volume": 1000000,
                "amount": 106000000.0,
            }
        }
    )

    ts_code: str = Field(..., description="股票代码")
    trade_date: str = Field(..., description="交易日期(YYYYMMDD)")
    open: Optional[float] = Field(None, description="开盘价(元)")
    high: Optional[float] = Field(None, description="最高价(元)")
    low: Optional[float] = Field(None, description="最低价(元)")
    close: Optional[float] = Field(None, description="收盘价(元)")
    pre_close: Optional[float] = Field(None, description="昨收价(元)")
    change: Optional[float] = Field(None, description="涨跌额(元)")
    pct_change: Optional[float] = Field(None, description="涨跌幅(%)")
    volume: Optional[int] = Field(None, description="成交量(手)")
    amount: Optional[float] = Field(None, description="成交额(元)")


class DailyDataResponse(BaseModel):
    """日线数据响应"""

    ts_code: str = Field(..., description="股票代码")
    count: int = Field(..., description="数据条数")
    data: list[DailyDataItem] = Field(default_factory=list, description="数据列表")


__all__ = [
    "Response",
    "HealthResponse",
    "DailyDataItem",
    "DailyDataResponse",
]
