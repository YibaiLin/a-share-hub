"""
ClickHouse存储处理器

提供日线数据的增删改查操作
"""

from typing import Optional, Any
from datetime import datetime
import pandas as pd
from core.database import ClickHouseClient, get_db_client
from core.logger import logger
from utils.date_helper import format_date
from config.settings import settings


class ClickHouseHandler:
    """ClickHouse数据操作处理器"""

    def __init__(self, client: Optional[ClickHouseClient] = None):
        """
        初始化Handler

        Args:
            client: ClickHouse客户端，如果为None则使用全局客户端
        """
        self.client = client or get_db_client()
        self.batch_size = settings.collector_batch_size

    def insert_daily(
        self,
        ts_code: str,
        data: list[dict],
        deduplicate: bool = True
    ) -> int:
        """
        插入日线数据

        Args:
            ts_code: 股票代码
            data: 数据列表
            deduplicate: 是否去重

        Returns:
            实际插入的行数

        Raises:
            Exception: 插入失败
        """
        if not data:
            logger.warning(f"数据为空，跳过插入: {ts_code}")
            return 0

        try:
            # 去重处理
            if deduplicate:
                data = self._deduplicate_daily(ts_code, data)
                if not data:
                    logger.info(f"去重后无新数据: {ts_code}")
                    return 0

            # 准备插入数据
            insert_data = []
            for record in data:
                row = [
                    ts_code,
                    record["trade_date"],
                    record["open"],
                    record["high"],
                    record["low"],
                    record["close"],
                    record.get("pre_close", -1),
                    record.get("change", -1),
                    record["pct_change"],
                    record["volume"],
                    record["amount"],
                ]
                insert_data.append(row)

            # 分批插入
            total_inserted = 0
            for i in range(0, len(insert_data), self.batch_size):
                batch = insert_data[i:i + self.batch_size]

                self.client.insert(
                    table="stock_daily",
                    data=batch,
                    column_names=[
                        "ts_code",
                        "trade_date",
                        "open",
                        "high",
                        "low",
                        "close",
                        "pre_close",
                        "change",
                        "pct_change",
                        "volume",
                        "amount",
                    ],
                )

                total_inserted += len(batch)
                logger.debug(f"插入批次: {len(batch)} 条")

            logger.info(f"插入日线数据成功: {ts_code}, 共 {total_inserted} 条")
            return total_inserted

        except Exception as e:
            logger.error(f"插入日线数据失败: {e}, ts_code={ts_code}")
            raise

    def query_daily(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> list[dict]:
        """
        查询日线数据

        Args:
            ts_code: 股票代码
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）
            limit: 限制返回行数

        Returns:
            数据列表

        Raises:
            Exception: 查询失败
        """
        try:
            # 构建查询SQL
            where_clauses = [f"ts_code = '{ts_code}'"]

            if start_date:
                where_clauses.append(f"trade_date >= '{start_date}'")

            if end_date:
                where_clauses.append(f"trade_date <= '{end_date}'")

            where_sql = " AND ".join(where_clauses)

            # 查询语句
            sql = f"""
                SELECT
                    ts_code,
                    trade_date,
                    open,
                    high,
                    low,
                    close,
                    pre_close,
                    change,
                    pct_change,
                    volume,
                    amount
                FROM stock_daily
                WHERE {where_sql}
                ORDER BY trade_date DESC
            """

            if limit:
                sql += f" LIMIT {limit}"

            logger.debug(f"查询日线数据: {ts_code}")
            result = self.client.execute(sql)

            # 转换结果
            data = []
            for row in result.result_rows:
                record = {
                    "ts_code": row[0],
                    "trade_date": row[1],
                    "open": row[2],
                    "high": row[3],
                    "low": row[4],
                    "close": row[5],
                    "pre_close": row[6],
                    "change": row[7],
                    "pct_change": row[8],
                    "volume": row[9],
                    "amount": row[10],
                }
                data.append(record)

            logger.info(f"查询到 {len(data)} 条日线数据: {ts_code}")
            return data

        except Exception as e:
            logger.error(f"查询日线数据失败: {e}, ts_code={ts_code}")
            raise

    def query_daily_df(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        查询日线数据（返回DataFrame）

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame

        Raises:
            Exception: 查询失败
        """
        try:
            where_clauses = [f"ts_code = '{ts_code}'"]

            if start_date:
                where_clauses.append(f"trade_date >= '{start_date}'")

            if end_date:
                where_clauses.append(f"trade_date <= '{end_date}'")

            where_sql = " AND ".join(where_clauses)

            sql = f"""
                SELECT * FROM stock_daily
                WHERE {where_sql}
                ORDER BY trade_date
            """

            df = self.client.query_df(sql)
            logger.info(f"查询到 {len(df)} 条日线数据(DataFrame): {ts_code}")
            return df

        except Exception as e:
            logger.error(f"查询日线数据失败(DataFrame): {e}")
            raise

    def delete_daily(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> None:
        """
        删除日线数据

        注意：ClickHouse的DELETE是异步的，不会立即生效

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Raises:
            Exception: 删除失败
        """
        try:
            where_clauses = [f"ts_code = '{ts_code}'"]

            if start_date:
                where_clauses.append(f"trade_date >= '{start_date}'")

            if end_date:
                where_clauses.append(f"trade_date <= '{end_date}'")

            where_sql = " AND ".join(where_clauses)

            sql = f"ALTER TABLE stock_daily DELETE WHERE {where_sql}"

            self.client.execute(sql)
            logger.info(f"删除日线数据: {ts_code}, {start_date} ~ {end_date}")

        except Exception as e:
            logger.error(f"删除日线数据失败: {e}")
            raise

    def get_latest_date(self, ts_code: str) -> Optional[str]:
        """
        获取某股票最新的数据日期

        Args:
            ts_code: 股票代码

        Returns:
            最新日期（YYYYMMDD），如果没有数据返回None
        """
        try:
            sql = f"""
                SELECT max(trade_date) as max_date
                FROM stock_daily
                WHERE ts_code = '{ts_code}'
            """

            result = self.client.execute(sql)

            if result.result_rows and result.result_rows[0][0]:
                date_obj = result.result_rows[0][0]
                return format_date(date_obj)

            return None

        except Exception as e:
            logger.error(f"获取最新日期失败: {e}, ts_code={ts_code}")
            return None

    def _deduplicate_daily(self, ts_code: str, data: list[dict]) -> list[dict]:
        """
        去重：过滤已存在的数据

        Args:
            ts_code: 股票代码
            data: 待插入的数据

        Returns:
            去重后的数据
        """
        if not data:
            return []

        try:
            # 获取待插入数据的日期范围
            dates = [record["trade_date"] for record in data]
            min_date = min(dates)
            max_date = max(dates)

            # 查询已存在的日期
            sql = f"""
                SELECT DISTINCT trade_date
                FROM stock_daily
                WHERE ts_code = '{ts_code}'
                  AND trade_date >= '{min_date}'
                  AND trade_date <= '{max_date}'
            """

            result = self.client.execute(sql)
            existing_dates = {format_date(row[0]) for row in result.result_rows}

            # 过滤已存在的数据
            new_data = [
                record for record in data
                if record["trade_date"] not in existing_dates
            ]

            if len(new_data) < len(data):
                logger.info(
                    f"去重: 原 {len(data)} 条, "
                    f"已存在 {len(data) - len(new_data)} 条, "
                    f"新增 {len(new_data)} 条"
                )

            return new_data

        except Exception as e:
            logger.warning(f"去重失败，将插入全部数据: {e}")
            return data


__all__ = ["ClickHouseHandler"]
