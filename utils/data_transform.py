"""
数据转换工具

提供数据类型转换、清洗、格式化等功能
"""

from typing import Any, Optional
import pandas as pd
from core.logger import logger


def price_to_int(price: Optional[float]) -> int:
    """
    价格转整型：浮点数 × 100

    用于存储时避免浮点数精度问题

    Args:
        price: 价格（元），可以为None

    Returns:
        整型价格（分），None转为-1

    Examples:
        >>> price_to_int(12.34)
        1234
        >>> price_to_int(0.0)
        0
        >>> price_to_int(None)
        -1
    """
    if price is None:
        return -1
    try:
        return int(price * 100)
    except (ValueError, TypeError) as e:
        logger.warning(f"价格转换失败: {price}, 错误: {e}")
        return -1


def int_to_price(value: int) -> Optional[float]:
    """
    整型还原为价格：整型 ÷ 100

    用于查询时将存储的整型还原为浮点数

    Args:
        value: 整型价格（分）

    Returns:
        浮点价格（元），-1转为None

    Examples:
        >>> int_to_price(1234)
        12.34
        >>> int_to_price(0)
        0.0
        >>> int_to_price(-1)
        None
    """
    if value == -1:
        return None
    try:
        return value / 100
    except (ValueError, TypeError) as e:
        logger.warning(f"价格还原失败: {value}, 错误: {e}")
        return None


def handle_null(value: Any, default: Any = -1) -> Any:
    """
    处理空值

    将None、NaN、空字符串等转换为指定默认值

    Args:
        value: 待处理的值
        default: 默认值，通常为-1

    Returns:
        处理后的值

    Examples:
        >>> handle_null(None)
        -1
        >>> handle_null(float('nan'))
        -1
        >>> handle_null('')
        -1
        >>> handle_null(0)
        0
    """
    if value is None:
        return default

    # 处理NaN
    if isinstance(value, float) and pd.isna(value):
        return default

    # 处理空字符串
    if isinstance(value, str) and value.strip() == '':
        return default

    return value


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    清洗DataFrame

    - 删除完全重复的行
    - 删除所有列都为空的行
    - 重置索引

    Args:
        df: 待清洗的DataFrame

    Returns:
        清洗后的DataFrame

    Examples:
        >>> df = pd.DataFrame({'a': [1, 1, None], 'b': [2, 2, None]})
        >>> clean_df = clean_dataframe(df)
        >>> len(clean_df)
        1
    """
    if df.empty:
        return df

    # 删除完全重复的行
    df = df.drop_duplicates()

    # 删除所有列都为空的行
    df = df.dropna(how='all')

    # 重置索引
    df = df.reset_index(drop=True)

    logger.debug(f"数据清洗完成，剩余 {len(df)} 行")
    return df


def convert_price_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    批量转换DataFrame中的价格列

    将指定列的浮点数价格转换为整型（×100）

    Args:
        df: 待转换的DataFrame
        columns: 需要转换的列名列表

    Returns:
        转换后的DataFrame（原地修改）

    Examples:
        >>> df = pd.DataFrame({'open': [12.34, 56.78], 'close': [13.45, 57.89]})
        >>> df = convert_price_columns(df, ['open', 'close'])
        >>> df['open'].tolist()
        [1234, 5678]
    """
    for col in columns:
        if col in df.columns:
            df[col] = df[col].apply(price_to_int)
        else:
            logger.warning(f"列 {col} 不存在，跳过转换")

    return df


def format_ts_code(code: str) -> str:
    """
    格式化股票代码

    统一为6位代码 + 后缀格式（如 000001.SZ）

    Args:
        code: 原始股票代码

    Returns:
        格式化后的股票代码

    Examples:
        >>> format_ts_code('000001')
        '000001.SZ'
        >>> format_ts_code('600000')
        '600000.SH'
        >>> format_ts_code('000001.SZ')
        '000001.SZ'
    """
    code = code.strip()

    # 如果已经有后缀，直接返回
    if '.' in code:
        return code

    # 根据代码范围判断市场
    if code.startswith('6'):
        return f"{code}.SH"  # 上海主板
    elif code.startswith('00') or code.startswith('30'):
        return f"{code}.SZ"  # 深圳主板/创业板
    elif code.startswith('688'):
        return f"{code}.SH"  # 科创板
    elif code.startswith('8'):
        return f"{code}.BJ"  # 北交所
    else:
        logger.warning(f"无法识别的股票代码: {code}")
        return code


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    安全转换为浮点数

    Args:
        value: 待转换的值
        default: 转换失败时的默认值

    Returns:
        浮点数

    Examples:
        >>> safe_float('12.34')
        12.34
        >>> safe_float(None)
        0.0
        >>> safe_float('abc', default=-1.0)
        -1.0
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default

    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"浮点数转换失败: {value}, 使用默认值: {default}")
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    安全转换为整数

    Args:
        value: 待转换的值
        default: 转换失败时的默认值

    Returns:
        整数

    Examples:
        >>> safe_int('123')
        123
        >>> safe_int(None)
        0
        >>> safe_int('abc', default=-1)
        -1
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default

    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"整数转换失败: {value}, 使用默认值: {default}")
        return default


__all__ = [
    "price_to_int",
    "int_to_price",
    "handle_null",
    "clean_dataframe",
    "convert_price_columns",
    "format_ts_code",
    "safe_float",
    "safe_int",
]
