"""
日期工具

提供交易日判断、日期格式化等功能
"""

from datetime import datetime, date, timedelta
from typing import Optional, Union
import pandas as pd
from core.logger import logger


def format_date(
    dt: Union[str, datetime, date, pd.Timestamp],
    fmt: str = "%Y%m%d"
) -> str:
    """
    格式化日期

    Args:
        dt: 日期（字符串、datetime、date或Timestamp）
        fmt: 输出格式，默认为YYYYMMDD

    Returns:
        格式化后的日期字符串

    Examples:
        >>> format_date(datetime(2024, 1, 15))
        '20240115'
        >>> format_date('2024-01-15')
        '20240115'
        >>> format_date(datetime(2024, 1, 15), '%Y-%m-%d')
        '2024-01-15'
    """
    if isinstance(dt, str):
        # 尝试解析字符串日期
        dt = parse_date(dt)

    if isinstance(dt, (datetime, date, pd.Timestamp)):
        return dt.strftime(fmt)

    raise ValueError(f"无法格式化日期: {dt}, 类型: {type(dt)}")


def parse_date(date_str: str) -> datetime:
    """
    解析日期字符串

    支持多种常见格式：
    - YYYYMMDD
    - YYYY-MM-DD
    - YYYY/MM/DD
    - YYYY.MM.DD

    Args:
        date_str: 日期字符串

    Returns:
        datetime对象

    Raises:
        ValueError: 无法解析日期字符串

    Examples:
        >>> parse_date('20240115')
        datetime.datetime(2024, 1, 15, 0, 0)
        >>> parse_date('2024-01-15')
        datetime.datetime(2024, 1, 15, 0, 0)
    """
    date_str = date_str.strip()

    # 尝试多种格式
    formats = [
        "%Y%m%d",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"无法解析日期字符串: {date_str}")


def is_trading_day(dt: Union[str, datetime, date]) -> bool:
    """
    判断是否为交易日

    简化版本：仅判断是否为工作日（周一至周五）
    不考虑节假日，实际使用需要对接交易日历API

    Args:
        dt: 日期

    Returns:
        True表示可能是交易日，False表示肯定不是

    Examples:
        >>> is_trading_day(datetime(2024, 1, 15))  # 周一
        True
        >>> is_trading_day(datetime(2024, 1, 20))  # 周六
        False
    """
    if isinstance(dt, str):
        dt = parse_date(dt)

    # 转换为datetime
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime.combine(dt, datetime.min.time())

    # 周一=0，周日=6
    weekday = dt.weekday()

    # 周一至周五
    return 0 <= weekday <= 4


def get_date_range(
    start_date: Union[str, datetime, date],
    end_date: Union[str, datetime, date],
    trading_days_only: bool = False
) -> list[str]:
    """
    获取日期范围

    Args:
        start_date: 开始日期
        end_date: 结束日期
        trading_days_only: 是否仅返回交易日

    Returns:
        日期字符串列表（YYYYMMDD格式）

    Examples:
        >>> dates = get_date_range('2024-01-15', '2024-01-17')
        >>> len(dates)
        3
        >>> dates = get_date_range('2024-01-15', '2024-01-21', trading_days_only=True)
        >>> len(dates)  # 不包含周末
        5
    """
    if isinstance(start_date, str):
        start_date = parse_date(start_date)
    if isinstance(end_date, str):
        end_date = parse_date(end_date)

    # 转换为date
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()

    dates = []
    current = start_date

    while current <= end_date:
        if not trading_days_only or is_trading_day(current):
            dates.append(format_date(current))
        current += timedelta(days=1)

    return dates


def get_today() -> str:
    """
    获取今天的日期

    Returns:
        今天的日期字符串（YYYYMMDD格式）

    Examples:
        >>> today = get_today()
        >>> len(today)
        8
    """
    return format_date(datetime.now())


def get_latest_trading_day(dt: Optional[Union[str, datetime, date]] = None) -> str:
    """
    获取最近的交易日

    简化版本：向前查找最近的工作日

    Args:
        dt: 参考日期，默认为今天

    Returns:
        最近交易日的日期字符串（YYYYMMDD格式）

    Examples:
        >>> # 如果今天是周六，返回周五
        >>> latest = get_latest_trading_day(datetime(2024, 1, 20))
        >>> latest
        '20240119'
    """
    if dt is None:
        dt = datetime.now()
    elif isinstance(dt, str):
        dt = parse_date(dt)

    # 转换为date
    if isinstance(dt, datetime):
        dt = dt.date()

    # 向前查找最多7天
    for i in range(7):
        check_date = dt - timedelta(days=i)
        if is_trading_day(check_date):
            return format_date(check_date)

    # 如果7天内没有找到，返回当前日期
    logger.warning(f"未找到最近交易日，返回当前日期: {dt}")
    return format_date(dt)


def is_trading_time() -> bool:
    """
    判断当前是否为交易时间

    A股交易时间：
    - 上午：09:30 - 11:30
    - 下午：13:00 - 15:00

    Returns:
        True表示当前是交易时间

    Examples:
        >>> # 假设当前是10:00
        >>> is_trading_time()
        True
    """
    now = datetime.now()

    # 首先判断是否为交易日
    if not is_trading_day(now):
        return False

    current_time = now.time()

    # 上午时段：09:30 - 11:30
    morning_start = datetime.strptime("09:30", "%H:%M").time()
    morning_end = datetime.strptime("11:30", "%H:%M").time()

    # 下午时段：13:00 - 15:00
    afternoon_start = datetime.strptime("13:00", "%H:%M").time()
    afternoon_end = datetime.strptime("15:00", "%H:%M").time()

    return (morning_start <= current_time <= morning_end or
            afternoon_start <= current_time <= afternoon_end)


def get_previous_trading_day(dt: Union[str, datetime, date], days: int = 1) -> str:
    """
    获取前N个交易日

    简化版本：向前推N个工作日

    Args:
        dt: 参考日期
        days: 向前推移的交易日数量

    Returns:
        前N个交易日的日期字符串

    Examples:
        >>> get_previous_trading_day('2024-01-19', 1)  # 周五
        '20240118'  # 周四
        >>> get_previous_trading_day('2024-01-22', 1)  # 周一
        '20240119'  # 周五
    """
    if isinstance(dt, str):
        dt = parse_date(dt)

    if isinstance(dt, datetime):
        dt = dt.date()

    found = 0
    current = dt

    # 向前查找，最多查30天
    for _ in range(30):
        current -= timedelta(days=1)
        if is_trading_day(current):
            found += 1
            if found == days:
                return format_date(current)

    logger.warning(f"未找到前{days}个交易日，返回当前日期")
    return format_date(dt)


__all__ = [
    "format_date",
    "parse_date",
    "is_trading_day",
    "get_date_range",
    "get_today",
    "get_latest_trading_day",
    "is_trading_time",
    "get_previous_trading_day",
]
