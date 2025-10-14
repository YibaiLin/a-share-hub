"""
调度任务测试
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, date
from schedulers.tasks import (
    collect_daily_data_task,
    update_stock_list_task,
    trigger_daily_collect,
    trigger_stock_list_update,
)


class TestSchedulerTasks:
    """调度任务测试"""

    @pytest.mark.asyncio
    @patch('schedulers.tasks.is_trading_day')
    @patch('schedulers.tasks.get_previous_trading_day')
    @patch('schedulers.tasks.get_db_client')
    @patch('schedulers.tasks.DailyCollector')
    @patch('schedulers.tasks.ClickHouseHandler')
    async def test_collect_daily_data_task_success(
        self,
        mock_handler_class,
        mock_collector_class,
        mock_get_client,
        mock_get_prev_day,
        mock_is_trading_day
    ):
        """测试日线采集任务成功执行"""
        # Mock交易日判断
        mock_is_trading_day.return_value = True
        mock_get_prev_day.return_value = date(2024, 1, 15)

        # Mock采集器
        mock_collector = AsyncMock()
        mock_collector.collect.return_value = [
            {
                "trade_date": "20240115",
                "open": 1050,
                "close": 1060,
            }
        ]
        mock_collector_class.return_value = mock_collector

        # Mock数据库
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_handler = Mock()
        mock_handler.insert_daily.return_value = 1
        mock_handler_class.return_value = mock_handler

        # 执行任务
        await collect_daily_data_task()

        # 验证调用
        assert mock_collector.collect.call_count == 3  # 3只测试股票
        assert mock_handler.insert_daily.call_count == 3

    @pytest.mark.asyncio
    @patch('schedulers.tasks.is_trading_day')
    async def test_collect_daily_data_task_non_trading_day(
        self,
        mock_is_trading_day
    ):
        """测试非交易日跳过采集"""
        # Mock非交易日
        mock_is_trading_day.return_value = False

        # 执行任务（应该直接返回）
        await collect_daily_data_task()

        # 验证：非交易日应该直接返回，不执行采集
        mock_is_trading_day.assert_called_once()

    @pytest.mark.asyncio
    @patch('schedulers.tasks.is_trading_day')
    @patch('schedulers.tasks.get_previous_trading_day')
    @patch('schedulers.tasks.get_db_client')
    @patch('schedulers.tasks.DailyCollector')
    @patch('schedulers.tasks.ClickHouseHandler')
    async def test_collect_daily_data_task_partial_failure(
        self,
        mock_handler_class,
        mock_collector_class,
        mock_get_client,
        mock_get_prev_day,
        mock_is_trading_day
    ):
        """测试部分股票采集失败"""
        # Mock交易日
        mock_is_trading_day.return_value = True
        mock_get_prev_day.return_value = date(2024, 1, 15)

        # Mock采集器（第一只股票失败）
        mock_collector = AsyncMock()

        call_count = 0

        async def collect_side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Network error")
            return [{"trade_date": "20240115", "open": 1050}]

        mock_collector.collect.side_effect = collect_side_effect
        mock_collector_class.return_value = mock_collector

        # Mock数据库
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_handler = Mock()
        mock_handler.insert_daily.return_value = 1
        mock_handler_class.return_value = mock_handler

        # 执行任务（不应该抛出异常）
        await collect_daily_data_task()

        # 验证：应该调用3次collect（包括失败的那次）
        assert mock_collector.collect.call_count == 3
        # 只有2次成功insert
        assert mock_handler.insert_daily.call_count == 2

    @pytest.mark.asyncio
    async def test_update_stock_list_task(self):
        """测试股票列表更新任务"""
        # 当前版本只是打印TODO，不执行实际操作
        await update_stock_list_task()
        # 只验证不抛出异常

    @pytest.mark.asyncio
    @patch('schedulers.tasks.collect_daily_data_task')
    async def test_trigger_daily_collect(self, mock_collect_task):
        """测试手动触发日线采集"""
        mock_collect_task.return_value = None

        await trigger_daily_collect()

        mock_collect_task.assert_called_once()

    @pytest.mark.asyncio
    @patch('schedulers.tasks.update_stock_list_task')
    async def test_trigger_stock_list_update(self, mock_update_task):
        """测试手动触发股票列表更新"""
        mock_update_task.return_value = None

        await trigger_stock_list_update()

        mock_update_task.assert_called_once()
