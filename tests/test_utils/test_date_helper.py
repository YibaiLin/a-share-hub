"""
日期工具测试
"""

import pytest
from datetime import datetime, date, timedelta
from utils.date_helper import (
    format_date,
    parse_date,
    is_trading_day,
    get_date_range,
    get_today,
    get_latest_trading_day,
    is_trading_time,
    get_previous_trading_day,
)


class TestFormatDate:
    """日期格式化测试"""

    def test_format_date_datetime(self):
        """测试datetime格式化"""
        dt = datetime(2024, 1, 15)
        assert format_date(dt) == '20240115'
        assert format_date(dt, '%Y-%m-%d') == '2024-01-15'

    def test_format_date_date(self):
        """测试date格式化"""
        dt = date(2024, 1, 15)
        assert format_date(dt) == '20240115'

    def test_format_date_string(self):
        """测试字符串格式化"""
        assert format_date('2024-01-15') == '20240115'
        assert format_date('20240115') == '20240115'


class TestParseDate:
    """日期解析测试"""

    def test_parse_date_yyyymmdd(self):
        """测试YYYYMMDD格式"""
        dt = parse_date('20240115')
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15

    def test_parse_date_dash(self):
        """测试YYYY-MM-DD格式"""
        dt = parse_date('2024-01-15')
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15

    def test_parse_date_slash(self):
        """测试YYYY/MM/DD格式"""
        dt = parse_date('2024/01/15')
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15

    def test_parse_date_invalid(self):
        """测试无效日期"""
        with pytest.raises(ValueError):
            parse_date('invalid-date')


class TestIsTradingDay:
    """交易日判断测试"""

    def test_is_trading_day_weekday(self):
        """测试工作日（周一）"""
        dt = datetime(2024, 1, 15)  # 2024-01-15是周一
        assert is_trading_day(dt) is True

    def test_is_trading_day_friday(self):
        """测试周五"""
        dt = datetime(2024, 1, 19)  # 2024-01-19是周五
        assert is_trading_day(dt) is True

    def test_is_trading_day_saturday(self):
        """测试周六"""
        dt = datetime(2024, 1, 20)  # 2024-01-20是周六
        assert is_trading_day(dt) is False

    def test_is_trading_day_sunday(self):
        """测试周日"""
        dt = datetime(2024, 1, 21)  # 2024-01-21是周日
        assert is_trading_day(dt) is False

    def test_is_trading_day_string(self):
        """测试字符串输入"""
        assert is_trading_day('2024-01-15') is True  # 周一
        assert is_trading_day('2024-01-20') is False  # 周六


class TestGetDateRange:
    """日期范围获取测试"""

    def test_get_date_range_simple(self):
        """测试简单日期范围"""
        dates = get_date_range('2024-01-15', '2024-01-17')
        assert len(dates) == 3
        assert dates[0] == '20240115'
        assert dates[-1] == '20240117'

    def test_get_date_range_trading_days_only(self):
        """测试仅交易日"""
        # 2024-01-15是周一，2024-01-21是周日
        dates = get_date_range('2024-01-15', '2024-01-21', trading_days_only=True)
        assert len(dates) == 5  # 周一到周五
        assert '20240120' not in dates  # 周六
        assert '20240121' not in dates  # 周日

    def test_get_date_range_same_day(self):
        """测试同一天"""
        dates = get_date_range('2024-01-15', '2024-01-15')
        assert len(dates) == 1
        assert dates[0] == '20240115'


class TestGetToday:
    """获取今天日期测试"""

    def test_get_today(self):
        """测试获取今天"""
        today = get_today()
        assert len(today) == 8
        assert today.isdigit()

        # 验证格式正确
        now = datetime.now()
        expected = format_date(now)
        assert today == expected


class TestGetLatestTradingDay:
    """获取最近交易日测试"""

    def test_get_latest_trading_day_weekday(self):
        """测试工作日返回当天"""
        dt = datetime(2024, 1, 15)  # 周一
        latest = get_latest_trading_day(dt)
        assert latest == '20240115'

    def test_get_latest_trading_day_saturday(self):
        """测试周六返回周五"""
        dt = datetime(2024, 1, 20)  # 周六
        latest = get_latest_trading_day(dt)
        assert latest == '20240119'  # 周五

    def test_get_latest_trading_day_sunday(self):
        """测试周日返回周五"""
        dt = datetime(2024, 1, 21)  # 周日
        latest = get_latest_trading_day(dt)
        assert latest == '20240119'  # 周五


class TestIsTradingTime:
    """交易时间判断测试"""

    def test_is_trading_time(self):
        """测试交易时间判断

        注意：此测试依赖当前时间，仅验证函数可执行
        """
        result = is_trading_time()
        assert isinstance(result, bool)


class TestGetPreviousTradingDay:
    """获取前N个交易日测试"""

    def test_get_previous_trading_day_one(self):
        """测试获取前1个交易日"""
        dt = datetime(2024, 1, 19)  # 周五
        prev = get_previous_trading_day(dt, 1)
        assert prev == '20240118'  # 周四

    def test_get_previous_trading_day_from_monday(self):
        """测试从周一获取前1个交易日"""
        dt = datetime(2024, 1, 22)  # 周一
        prev = get_previous_trading_day(dt, 1)
        assert prev == '20240119'  # 周五

    def test_get_previous_trading_day_multiple(self):
        """测试获取前3个交易日"""
        dt = datetime(2024, 1, 19)  # 周五
        prev = get_previous_trading_day(dt, 3)
        assert prev == '20240116'  # 周二
