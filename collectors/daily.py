"""
日线数据采集器

对接AKShare的stock_zh_a_hist接口，采集A股日线数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, date
from typing import Any, Optional
from collectors.base import BaseCollector
from utils.data_transform import (
    price_to_int,
    format_ts_code,
    safe_int,
    clean_dataframe,
)
from utils.date_helper import format_date, parse_date
from core.logger import logger


class DailyCollector(BaseCollector):
    """
    日线数据采集器

    采集A股日线数据，包括：
    - 开盘价、最高价、最低价、收盘价
    - 成交量、成交额
    - 涨跌额、涨跌幅
    """

    async def fetch_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        从AKShare获取日线数据

        Args:
            symbol: 股票代码（如'000001'或'000001.SZ'）
            start_date: 开始日期（YYYYMMDD或YYYY-MM-DD）
            end_date: 结束日期（YYYYMMDD或YYYY-MM-DD）

        Returns:
            原始数据DataFrame

        Raises:
            Exception: 数据获取失败
        """
        # 格式化股票代码（去掉后缀）
        if '.' in symbol:
            symbol = symbol.split('.')[0]

        # 格式化日期
        if start_date:
            start_date = format_date(parse_date(start_date), '%Y%m%d')
        if end_date:
            end_date = format_date(parse_date(end_date), '%Y%m%d')

        try:
            logger.info(f"采集日线数据: {symbol}, {start_date} ~ {end_date}")

            # 调用AKShare接口
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date or "19900101",
                end_date=end_date or format_date(datetime.now(), '%Y%m%d'),
                adjust="",  # 不复权
            )

            if df is None or df.empty:
                logger.warning(f"未获取到数据: {symbol}")
                return pd.DataFrame()

            logger.info(f"获取到 {len(df)} 条日线数据: {symbol}")
            return df

        except Exception as e:
            logger.error(f"AKShare接口调用失败: {e}, symbol={symbol}")
            raise

    def transform_data(self, raw_data: pd.DataFrame) -> list[dict]:
        """
        转换数据格式

        AKShare返回的列名（中文）：
        - 日期
        - 开盘, 收盘, 最高, 最低
        - 成交量, 成交额
        - 振幅, 涨跌幅, 涨跌额
        - 换手率

        转换为数据库格式：
        - 价格 × 100 转为整型
        - 涨跌幅 × 100 转为整型（百分比）
        - 日期格式化

        Args:
            raw_data: AKShare返回的DataFrame

        Returns:
            转换后的数据列表

        Raises:
            Exception: 转换失败
        """
        if raw_data.empty:
            return []

        try:
            # 清洗数据
            df = clean_dataframe(raw_data.copy())

            # 转换数据
            data_list = []

            for _, row in df.iterrows():
                record = {
                    "trade_date": self._parse_date(row.get("日期")),
                    "open": price_to_int(row.get("开盘")),
                    "high": price_to_int(row.get("最高")),
                    "low": price_to_int(row.get("最低")),
                    "close": price_to_int(row.get("收盘")),
                    "volume": safe_int(row.get("成交量"), default=-1),
                    "amount": price_to_int(row.get("成交额")),  # 成交额也×100
                    "pct_change": self._convert_pct_change(row.get("涨跌幅")),
                }

                data_list.append(record)

            logger.debug(f"数据转换完成，共 {len(data_list)} 条")
            return data_list

        except Exception as e:
            logger.error(f"数据转换失败: {e}")
            raise

    def validate_data(self, data: list[dict]) -> bool:
        """
        验证数据有效性

        检查：
        - 数据不为空
        - 必需字段存在
        - 价格数据合理（非负或-1）

        Args:
            data: 待验证的数据

        Returns:
            True表示有效，False表示无效
        """
        if not data:
            return True  # 空数据也认为有效

        try:
            required_fields = [
                "trade_date",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "amount",
                "pct_change",
            ]

            for record in data:
                # 检查必需字段
                for field in required_fields:
                    if field not in record:
                        logger.error(f"缺少必需字段: {field}")
                        return False

                # 检查价格合理性（应该>=0或=-1）
                price_fields = ["open", "high", "low", "close"]
                for field in price_fields:
                    value = record[field]
                    if value < -1:
                        logger.error(f"价格不合理: {field}={value}")
                        return False

                # 检查最高价>=最低价（如果都有效）
                high = record["high"]
                low = record["low"]
                if high != -1 and low != -1 and high < low:
                    logger.error(f"最高价({high})<最低价({low})")
                    return False

            return True

        except Exception as e:
            logger.error(f"数据验证失败: {e}")
            return False

    def _parse_date(self, date_str: Any) -> str:
        """
        解析日期字符串

        Args:
            date_str: 日期字符串或其他类型

        Returns:
            标准格式日期字符串（YYYYMMDD）
        """
        if pd.isna(date_str):
            return ""

        if isinstance(date_str, str):
            try:
                dt = parse_date(date_str)
                return format_date(dt)
            except Exception as e:
                logger.warning(f"日期解析失败: {date_str}, {e}")
                return ""

        # 如果是datetime/date/Timestamp类型
        if isinstance(date_str, (datetime, date, pd.Timestamp)):
            return format_date(date_str)

        return ""

    def _convert_pct_change(self, value: Any) -> int:
        """
        转换涨跌幅

        涨跌幅通常是百分比（如3.45%），需要×10000存储
        例如：3.45% → 345

        Args:
            value: 涨跌幅值

        Returns:
            整型涨跌幅（×10000）
        """
        if value is None or pd.isna(value):
            return -1

        try:
            # 转为浮点数后×10000
            pct = float(value)
            return int(pct * 100)
        except (ValueError, TypeError):
            logger.warning(f"涨跌幅转换失败: {value}")
            return -1


__all__ = ["DailyCollector"]
