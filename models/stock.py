"""
股票数据模型

定义股票基础信息、日线、分钟线等数据模型
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class StockBasic(BaseModel):
    """股票基础信息"""

    ts_code: str = Field(..., description="股票代码")
    symbol: str = Field(..., description="股票简称代码")
    name: str = Field(..., description="股票名称")
    area: Optional[str] = Field(None, description="地域")
    industry: Optional[str] = Field(None, description="行业")
    market: Optional[str] = Field(None, description="市场类型")
    list_date: Optional[date] = Field(None, description="上市日期")


class StockDaily(BaseModel):
    """股票日线数据"""

    ts_code: str = Field(..., description="股票代码")
    trade_date: str = Field(..., description="交易日期(YYYYMMDD)")
    open: int = Field(..., description="开盘价(×100)")
    high: int = Field(..., description="最高价(×100)")
    low: int = Field(..., description="最低价(×100)")
    close: int = Field(..., description="收盘价(×100)")
    pre_close: int = Field(default=-1, description="昨收价(×100)")
    change: int = Field(default=-1, description="涨跌额(×100)")
    pct_change: int = Field(..., description="涨跌幅(×10000)")
    volume: int = Field(..., description="成交量(手)")
    amount: int = Field(..., description="成交额(元×100)")

    @field_validator("open", "high", "low", "close")
    @classmethod
    def validate_price(cls, v: int) -> int:
        """验证价格有效性"""
        if v < -1:
            raise ValueError(f"价格不能小于-1: {v}")
        return v

    @field_validator("trade_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """验证日期格式"""
        if len(v) != 8 or not v.isdigit():
            raise ValueError(f"日期格式必须为YYYYMMDD: {v}")
        return v


class StockMinute(BaseModel):
    """股票分钟线数据"""

    ts_code: str = Field(..., description="股票代码")
    trade_time: datetime = Field(..., description="交易时间")
    open: int = Field(..., description="开盘价(×100)")
    high: int = Field(..., description="最高价(×100)")
    low: int = Field(..., description="最低价(×100)")
    close: int = Field(..., description="收盘价(×100)")
    volume: int = Field(..., description="成交量(手)")
    amount: int = Field(..., description="成交额(元×100)")

    @field_validator("open", "high", "low", "close")
    @classmethod
    def validate_price(cls, v: int) -> int:
        """验证价格有效性"""
        if v < -1:
            raise ValueError(f"价格不能小于-1: {v}")
        return v


__all__ = ["StockBasic", "StockDaily", "StockMinute"]
