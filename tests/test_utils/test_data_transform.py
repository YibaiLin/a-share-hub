"""
数据转换工具测试
"""

import pytest
import pandas as pd
from utils.data_transform import (
    price_to_int,
    int_to_price,
    handle_null,
    clean_dataframe,
    convert_price_columns,
    format_ts_code,
    safe_float,
    safe_int,
)


class TestPriceConversion:
    """价格转换测试"""

    def test_price_to_int_normal(self):
        """测试正常价格转换"""
        assert price_to_int(12.34) == 1234
        assert price_to_int(0.01) == 1
        assert price_to_int(100.0) == 10000

    def test_price_to_int_zero(self):
        """测试零值"""
        assert price_to_int(0.0) == 0

    def test_price_to_int_none(self):
        """测试None值"""
        assert price_to_int(None) == -1

    def test_price_to_int_negative(self):
        """测试负数（虽然价格通常不为负）"""
        assert price_to_int(-12.34) == -1234

    def test_int_to_price_normal(self):
        """测试正常整型转价格"""
        assert int_to_price(1234) == 12.34
        assert int_to_price(1) == 0.01
        assert int_to_price(10000) == 100.0

    def test_int_to_price_zero(self):
        """测试零值"""
        assert int_to_price(0) == 0.0

    def test_int_to_price_minus_one(self):
        """测试-1（表示None）"""
        assert int_to_price(-1) is None


class TestNullHandling:
    """空值处理测试"""

    def test_handle_null_none(self):
        """测试None值"""
        assert handle_null(None) == -1
        assert handle_null(None, default=0) == 0

    def test_handle_null_nan(self):
        """测试NaN值"""
        assert handle_null(float('nan')) == -1

    def test_handle_null_empty_string(self):
        """测试空字符串"""
        assert handle_null('') == -1
        assert handle_null('  ') == -1

    def test_handle_null_valid_value(self):
        """测试有效值"""
        assert handle_null(0) == 0
        assert handle_null(123) == 123
        assert handle_null('abc') == 'abc'


class TestDataFrameCleaning:
    """DataFrame清洗测试"""

    def test_clean_dataframe_duplicates(self):
        """测试删除重复行"""
        df = pd.DataFrame({'a': [1, 1, 2], 'b': [2, 2, 3]})
        cleaned = clean_dataframe(df)
        assert len(cleaned) == 2
        assert list(cleaned['a']) == [1, 2]

    def test_clean_dataframe_all_null(self):
        """测试删除全空行"""
        df = pd.DataFrame({'a': [1, None, 3], 'b': [2, None, 4]})
        cleaned = clean_dataframe(df)
        assert len(cleaned) == 2
        assert 1 in list(cleaned['a'])
        assert 3 in list(cleaned['a'])

    def test_clean_dataframe_empty(self):
        """测试空DataFrame"""
        df = pd.DataFrame()
        cleaned = clean_dataframe(df)
        assert len(cleaned) == 0


class TestConvertPriceColumns:
    """价格列批量转换测试"""

    def test_convert_price_columns_normal(self):
        """测试正常转换"""
        df = pd.DataFrame({
            'open': [12.34, 56.78],
            'close': [13.45, 57.89],
            'volume': [1000, 2000]
        })
        df = convert_price_columns(df, ['open', 'close'])
        assert df['open'].tolist() == [1234, 5678]
        assert df['close'].tolist() == [1345, 5789]
        assert df['volume'].tolist() == [1000, 2000]  # 未转换

    def test_convert_price_columns_missing(self):
        """测试不存在的列"""
        df = pd.DataFrame({'open': [12.34]})
        df = convert_price_columns(df, ['open', 'high'])
        assert df['open'].tolist() == [1234]
        assert 'high' not in df.columns


class TestFormatTsCode:
    """股票代码格式化测试"""

    def test_format_ts_code_shanghai(self):
        """测试上海市场"""
        assert format_ts_code('600000') == '600000.SH'
        assert format_ts_code('688001') == '688001.SH'

    def test_format_ts_code_shenzhen(self):
        """测试深圳市场"""
        assert format_ts_code('000001') == '000001.SZ'
        assert format_ts_code('300001') == '300001.SZ'

    def test_format_ts_code_beijing(self):
        """测试北交所"""
        assert format_ts_code('830001') == '830001.BJ'

    def test_format_ts_code_with_suffix(self):
        """测试已有后缀"""
        assert format_ts_code('000001.SZ') == '000001.SZ'
        assert format_ts_code('600000.SH') == '600000.SH'


class TestSafeConversion:
    """安全类型转换测试"""

    def test_safe_float_normal(self):
        """测试正常浮点数转换"""
        assert safe_float('12.34') == 12.34
        assert safe_float(56.78) == 56.78
        assert safe_float(100) == 100.0

    def test_safe_float_none(self):
        """测试None值"""
        assert safe_float(None) == 0.0
        assert safe_float(None, default=-1.0) == -1.0

    def test_safe_float_invalid(self):
        """测试无效值"""
        assert safe_float('abc') == 0.0
        assert safe_float('abc', default=-1.0) == -1.0

    def test_safe_int_normal(self):
        """测试正常整数转换"""
        assert safe_int('123') == 123
        assert safe_int(456) == 456
        assert safe_int(78.9) == 78

    def test_safe_int_none(self):
        """测试None值"""
        assert safe_int(None) == 0
        assert safe_int(None, default=-1) == -1

    def test_safe_int_invalid(self):
        """测试无效值"""
        assert safe_int('abc') == 0
        assert safe_int('abc', default=-1) == -1
