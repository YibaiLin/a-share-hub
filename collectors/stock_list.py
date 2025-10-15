"""
股票列表采集器

获取全部A股股票列表
"""

import akshare as ak
import pandas as pd
from typing import Optional
from collectors.base import BaseCollector
from core.logger import logger


class StockListCollector(BaseCollector):
    """
    股票列表采集器

    功能:
    - 获取全部A股股票代码
    - 返回标准化的股票代码列表（ts_code格式）
    """

    async def fetch_data(self, **kwargs) -> pd.DataFrame:
        """
        从AKShare获取股票列表

        Returns:
            原始股票列表DataFrame

        Raises:
            Exception: 获取失败
        """
        try:
            logger.info("开始获取股票列表")

            # 调用AKShare接口获取股票列表
            # 返回字段: 代码, 名称
            df = ak.stock_info_a_code_name()

            if df is None or df.empty:
                logger.warning("未获取到股票列表数据")
                return pd.DataFrame()

            logger.info(f"获取到 {len(df)} 只股票")
            return df

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            raise

    def transform_data(self, raw_data: pd.DataFrame) -> list[dict]:
        """
        转换股票列表数据

        转换逻辑:
        - AKShare返回的代码需要添加后缀（.SZ / .SH）
        - 60/68/688开头 → 上海交易所 (.SH)
        - 00/30开头 → 深圳交易所 (.SZ)
        - 其他 → 北交所 (.BJ)

        Args:
            raw_data: AKShare返回的DataFrame

        Returns:
            转换后的股票列表
            [{"ts_code": "000001.SZ", "name": "平安银行"}, ...]
        """
        if raw_data.empty:
            return []

        try:
            stock_list = []

            for _, row in raw_data.iterrows():
                code = str(row.get("code", "")).strip()
                name = str(row.get("name", "")).strip()

                if not code:
                    continue

                # 添加市场后缀
                ts_code = self._format_ts_code(code)

                stock_list.append({
                    "ts_code": ts_code,
                    "name": name,
                    "code": code
                })

            logger.debug(f"股票列表转换完成: {len(stock_list)} 只")
            return stock_list

        except Exception as e:
            logger.error(f"股票列表转换失败: {e}")
            raise

    def validate_data(self, data: list[dict]) -> bool:
        """
        验证股票列表数据

        检查:
        - 数据不为空
        - 每条记录包含 ts_code 字段
        - ts_code 格式正确（6位数字.市场代码）

        Args:
            data: 待验证的股票列表

        Returns:
            True表示有效，False表示无效
        """
        if not data:
            logger.warning("股票列表为空")
            return True  # 空列表也认为有效

        try:
            for stock in data:
                # 检查必需字段
                if "ts_code" not in stock:
                    logger.error("股票记录缺少ts_code字段")
                    return False

                ts_code = stock["ts_code"]

                # 检查格式：6位数字.市场代码
                if not isinstance(ts_code, str):
                    logger.error(f"ts_code格式错误: {ts_code}")
                    return False

                parts = ts_code.split(".")
                if len(parts) != 2:
                    logger.error(f"ts_code格式错误: {ts_code}")
                    return False

                code, market = parts

                # 检查代码部分是否为6位数字
                if not (len(code) == 6 and code.isdigit()):
                    logger.error(f"股票代码格式错误: {code}")
                    return False

                # 检查市场代码
                if market not in ["SZ", "SH", "BJ"]:
                    logger.error(f"市场代码错误: {market}")
                    return False

            return True

        except Exception as e:
            logger.error(f"股票列表验证失败: {e}")
            return False

    def _format_ts_code(self, code: str) -> str:
        """
        格式化股票代码为ts_code格式

        规则:
        - 60/68/688开头 → 上海交易所 (.SH)
        - 00/30开头 → 深圳交易所 (.SZ)
        - 43/83/87/88开头 → 北交所 (.BJ)
        - 其他 → 默认深圳交易所 (.SZ)

        Args:
            code: 6位股票代码

        Returns:
            带市场后缀的ts_code (如 "000001.SZ")
        """
        code = code.strip()

        # 上海交易所
        if code.startswith(("60", "68", "688")):
            return f"{code}.SH"

        # 北交所
        elif code.startswith(("43", "83", "87", "88")):
            return f"{code}.BJ"

        # 深圳交易所（包括00、30和其他）
        else:
            return f"{code}.SZ"

    async def get_all_stocks(self) -> list[str]:
        """
        获取所有股票代码列表（便捷方法）

        Returns:
            股票代码列表 ["000001.SZ", "600000.SH", ...]

        Examples:
            >>> collector = StockListCollector()
            >>> stocks = await collector.get_all_stocks()
            >>> print(len(stocks))  # 约5000
        """
        data = await self.collect()
        return [stock["ts_code"] for stock in data]


__all__ = ["StockListCollector"]
