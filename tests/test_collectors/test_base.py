"""
基础采集器测试
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from collectors.base import BaseCollector, RateLimiter


class TestRateLimiter:
    """限流器测试"""

    @pytest.mark.asyncio
    async def test_rate_limiter_delay(self):
        """测试限流延迟"""
        limiter = RateLimiter(delay=0.2)

        # 第一次调用不需要等待
        start1 = time.time()
        await limiter.wait()
        elapsed1 = time.time() - start1
        assert elapsed1 < 0.1  # 几乎不等待

        # 第二次调用需要等待
        start2 = time.time()
        await limiter.wait()
        elapsed2 = time.time() - start2
        assert elapsed2 >= 0.2  # 至少等待0.2秒
        assert elapsed2 < 0.3  # 不超过0.3秒

    @pytest.mark.asyncio
    async def test_rate_limiter_multiple_calls(self):
        """测试多次调用限流"""
        limiter = RateLimiter(delay=0.1)

        start = time.time()
        for _ in range(3):
            await limiter.wait()
        elapsed = time.time() - start

        # 3次调用，2次需要等待，总共至少0.2秒
        assert elapsed >= 0.2
        assert elapsed < 0.4


class MockCollector(BaseCollector):
    """测试用的Mock采集器"""

    def __init__(self):
        super().__init__()
        self.fetch_called = False
        self.transform_called = False
        self.validate_called = False

    async def fetch_data(self, **kwargs):
        """模拟数据获取"""
        self.fetch_called = True
        await asyncio.sleep(0.01)  # 模拟网络延迟
        return [{"code": "000001", "price": 10.5}]

    def transform_data(self, raw_data):
        """模拟数据转换"""
        self.transform_called = True
        return [{"ts_code": "000001.SZ", "close": 1050}]

    def validate_data(self, data):
        """模拟数据验证"""
        self.validate_called = True
        return len(data) > 0


class FailingCollector(BaseCollector):
    """总是失败的采集器（用于测试重试）"""

    def __init__(self):
        super().__init__()
        self.attempt_count = 0

    async def fetch_data(self, **kwargs):
        """总是失败"""
        self.attempt_count += 1
        raise Exception("Network error")

    def transform_data(self, raw_data):
        """不会被调用"""
        return []

    def validate_data(self, data):
        """不会被调用"""
        return True


class TestBaseCollector:
    """基础采集器测试"""

    @pytest.mark.asyncio
    async def test_collect_success(self):
        """测试成功采集"""
        collector = MockCollector()
        data = await collector.collect(ts_code="000001")

        # 验证所有方法都被调用
        assert collector.fetch_called is True
        assert collector.transform_called is True
        assert collector.validate_called is True

        # 验证数据正确
        assert len(data) == 1
        assert data[0]["ts_code"] == "000001.SZ"

    @pytest.mark.asyncio
    async def test_collect_empty_data(self):
        """测试空数据"""
        class EmptyCollector(BaseCollector):
            async def fetch_data(self, **kwargs):
                return []

            def transform_data(self, raw_data):
                return []

            def validate_data(self, data):
                return True

        collector = EmptyCollector()
        data = await collector.collect()
        assert data == []

    @pytest.mark.asyncio
    async def test_collect_validation_failure(self):
        """测试验证失败"""
        class InvalidCollector(BaseCollector):
            async def fetch_data(self, **kwargs):
                return [{"data": "test"}]

            def transform_data(self, raw_data):
                return [{"result": "transformed"}]

            def validate_data(self, data):
                return False  # 验证失败

        collector = InvalidCollector()
        with pytest.raises(ValueError, match="Data validation failed"):
            await collector.collect()

    @pytest.mark.asyncio
    async def test_collect_with_retry(self):
        """测试重试机制"""
        collector = FailingCollector()

        with pytest.raises(Exception, match="Network error"):
            await collector.collect()

        # 验证重试了3次
        assert collector.attempt_count == 3

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """测试限流机制"""
        collector = MockCollector()

        start = time.time()

        # 连续采集2次
        await collector.collect()
        await collector.collect()

        elapsed = time.time() - start

        # 应该至少等待collector_delay秒（默认0.5秒）
        # 由于有两次调用，至少等待0.5秒
        assert elapsed >= 0.5

    @pytest.mark.asyncio
    async def test_batch_collect_success(self):
        """测试批量采集成功"""
        collector = MockCollector()

        params_list = [
            {"ts_code": "000001"},
            {"ts_code": "000002"},
        ]

        data = await collector.batch_collect(params_list)

        # 应该有2条数据
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_batch_collect_partial_failure(self):
        """测试批量采集部分失败"""
        class PartialFailCollector(BaseCollector):
            def __init__(self):
                super().__init__()
                self.call_count = 0

            async def fetch_data(self, **kwargs):
                self.call_count += 1
                # 前3次都失败（会触发重试）
                if self.call_count <= 3:
                    raise Exception("First param fails")
                return [{"data": f"success_{self.call_count}"}]

            def transform_data(self, raw_data):
                return [{"result": raw_data[0]["data"]}]

            def validate_data(self, data):
                return True

        collector = PartialFailCollector()

        params_list = [
            {"ts_code": "000001"},  # 会失败（重试3次全部失败）
            {"ts_code": "000002"},  # 会成功
        ]

        data = await collector.batch_collect(params_list)

        # 只有第2个成功
        assert len(data) == 1
        assert data[0]["result"] == "success_4"

    @pytest.mark.asyncio
    async def test_collector_initialization(self):
        """测试采集器初始化"""
        collector = MockCollector()

        # 验证限流器已创建
        assert collector.rate_limiter is not None
        assert isinstance(collector.rate_limiter, RateLimiter)

        # 验证配置加载
        assert collector.retry_times > 0
