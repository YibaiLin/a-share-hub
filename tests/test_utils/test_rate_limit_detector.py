"""
智能限流探测器测试（简化版）
"""

import pytest
import time
import asyncio
import os
import json
from utils.rate_limit_detector import RateLimitDetector, RateLimitBoundary, is_rate_limit_error, print_all_boundaries


class TestIsRateLimitError:
    """测试限流错误识别"""

    def test_proxy_error(self):
        """测试ProxyError识别"""
        error = Exception("ProxyError: Connection failed")
        assert is_rate_limit_error(error) is True

    def test_remote_disconnected(self):
        """测试RemoteDisconnected识别"""
        error = Exception("RemoteDisconnected: Remote end closed connection")
        assert is_rate_limit_error(error) is True

    def test_connection_reset(self):
        """测试Connection reset识别"""
        error = Exception("ConnectionResetError: Connection reset by peer")
        assert is_rate_limit_error(error) is True

    def test_429_error(self):
        """测试429状态码识别"""
        error = Exception("HTTPError: 429 Too Many Requests")
        assert is_rate_limit_error(error) is True

    def test_rate_limit_message(self):
        """测试rate limit关键词识别"""
        error = Exception("Rate limit exceeded")
        assert is_rate_limit_error(error) is True

    def test_chinese_message(self):
        """测试中文限流消息识别"""
        error = Exception("请求过于频繁，请稍后再试")
        assert is_rate_limit_error(error) is True

    def test_normal_error(self):
        """测试普通错误不被识别为限流"""
        error = Exception("ValueError: Invalid data")
        assert is_rate_limit_error(error) is False

    def test_case_insensitive(self):
        """测试大小写不敏感"""
        error = Exception("PROXYERROR: Connection failed")
        assert is_rate_limit_error(error) is True


class TestRateLimitDetector:
    """测试限流探测器"""

    @pytest.fixture
    def test_boundary_file(self, tmp_path):
        """创建临时边界文件路径"""
        return str(tmp_path / "test_boundaries.json")

    @pytest.fixture
    def detector(self, test_boundary_file):
        """创建测试用探测器"""
        return RateLimitDetector(
            enable=True,
            source="test",
            interface="test_api",
            data_type="test",
            description="测试接口",
            boundary_file=test_boundary_file
        )

    def test_init(self, detector):
        """测试初始化"""
        assert detector.enable is True
        assert detector.source == "test"
        assert detector.interface == "test_api"
        assert detector.data_type == "test"
        assert detector.boundary_key == "test.test_api.test"
        assert detector.state == "NORMAL"
        assert detector.boundary is None
        assert len(detector.request_history) == 0

    def test_init_disabled(self, test_boundary_file):
        """测试禁用状态"""
        detector = RateLimitDetector(
            enable=False,
            boundary_file=test_boundary_file
        )
        assert detector.enable is False

    def test_record_success(self, detector):
        """测试记录成功请求"""
        detector.record_success()
        assert len(detector.request_history) == 1
        assert detector.success_count == 1

        detector.record_success()
        assert len(detector.request_history) == 2
        assert detector.success_count == 2

    def test_record_success_disabled(self, test_boundary_file):
        """测试禁用时不记录"""
        detector = RateLimitDetector(enable=False, boundary_file=test_boundary_file)
        detector.record_success()
        assert len(detector.request_history) == 0
        assert detector.success_count == 0

    @pytest.mark.asyncio
    async def test_on_rate_limit_triggered(self, detector):
        """测试触发限流"""
        # 先记录一些成功请求
        for _ in range(50):
            detector.record_success()

        # 触发限流
        await detector.on_rate_limit_triggered()

        assert detector.state == "PAUSED"
        assert detector.trigger_count == 50
        assert detector.trigger_time is not None
        assert detector.next_probe_time is not None
        assert detector.total_rate_limit_errors == 1

    @pytest.mark.asyncio
    async def test_should_pause_normal_state(self, detector):
        """测试正常状态不暂停"""
        should_wait, wait_seconds = await detector.should_pause()
        assert should_wait is False
        assert wait_seconds == 0

    @pytest.mark.asyncio
    async def test_should_pause_paused_state(self, detector):
        """测试暂停状态需要等待"""
        # 模拟触发限流
        detector.state = "PAUSED"
        detector.trigger_time = time.time()
        detector.next_probe_time = time.time() + 10  # 10秒后试探

        should_wait, wait_seconds = await detector.should_pause()
        assert should_wait is True
        assert 5 <= wait_seconds <= 15  # 允许一些误差

    @pytest.mark.asyncio
    async def test_should_pause_probe_ready(self, detector):
        """测试探测时间到了"""
        # 模拟触发限流，且探测时间已到
        detector.state = "PAUSED"
        detector.trigger_time = time.time() - 301  # 5分钟前触发
        detector.next_probe_time = time.time() - 1  # 探测时间已过

        should_wait, wait_seconds = await detector.should_pause()
        assert should_wait is False
        assert wait_seconds == 0
        assert detector.state == "PROBING"
        assert detector.probe_count == 1

    @pytest.mark.asyncio
    async def test_on_probe_success(self, detector):
        """测试探测成功"""
        # 模拟场景：50次请求后触发限流，5分钟后探测成功
        detector.trigger_count = 50
        detector.trigger_time = time.time() - 300  # 5分钟前
        detector.probe_count = 1
        detector.state = "PROBING"

        await detector.on_probe_success()

        assert detector.state == "CONFIRMED"
        assert detector.boundary is not None
        assert detector.boundary.max_requests == 50
        assert 290 <= detector.boundary.window_seconds <= 310  # 允许误差
        assert detector.safe_batch_size == 40  # 80% of 50
        assert 350 <= detector.safe_pause_time <= 370  # 120% of 300

    @pytest.mark.asyncio
    async def test_on_probe_failed(self, detector):
        """测试探测失败"""
        detector.state = "PROBING"
        detector.probe_count = 1

        await detector.on_probe_failed()

        # 下次探测时间应该在5分钟后
        assert detector.next_probe_time is not None
        assert detector.next_probe_time > time.time()

    @pytest.mark.asyncio
    async def test_on_rate_limit_re_triggered(self, detector):
        """测试已确认后再次触发限流"""
        # 模拟已确认状态
        detector.state = "CONFIRMED"
        detector.boundary = RateLimitBoundary(
            max_requests=50,
            wait_time_seconds=300,
            window_seconds=300,
            detected_at=time.time(),
            confidence="high"
        )
        detector.success_count = 30

        await detector.on_rate_limit_re_triggered()

        # 应该重置到暂停状态
        assert detector.state == "PAUSED"
        assert detector.trigger_count == 30
        assert detector.probe_count == 0
        assert detector.total_rate_limit_errors == 1

    @pytest.mark.asyncio
    async def test_should_pause_confirmed_safe(self, detector):
        """测试已确认状态，请求数安全时不暂停"""
        # 模拟已确认窗口：300秒内最多50次
        detector.state = "CONFIRMED"
        detector.boundary = RateLimitBoundary(
            max_requests=50,
            wait_time_seconds=300,
            window_seconds=300,
            detected_at=time.time(),
            confidence="high"
        )
        detector.safe_batch_size = 40

        # 只记录30次请求（低于安全限制40次）
        now = time.time()
        for i in range(30):
            detector.request_history.append(now - 100 + i * 3)

        should_wait, wait_seconds = await detector.should_pause()
        assert should_wait is False
        assert wait_seconds == 0

    @pytest.mark.asyncio
    async def test_should_pause_confirmed_near_limit(self, detector):
        """测试已确认状态，接近上限时需要暂停"""
        # 模拟已确认窗口：300秒内最多50次
        detector.state = "CONFIRMED"
        detector.boundary = RateLimitBoundary(
            max_requests=50,
            wait_time_seconds=300,
            window_seconds=300,
            detected_at=time.time(),
            confidence="high"
        )
        detector.safe_batch_size = 40
        detector.safe_pause_time = 360

        # 记录40次请求（达到安全限制）
        now = time.time()
        for i in range(40):
            detector.request_history.append(now - 290 + i * 7)

        should_wait, wait_seconds = await detector.should_pause()
        assert should_wait is True
        assert wait_seconds == 360

    def test_save_and_load_boundary(self, test_boundary_file):
        """测试边界保存和加载"""
        # 创建探测器并保存边界
        detector1 = RateLimitDetector(
            enable=True,
            source="test",
            interface="test_api",
            data_type="test",
            boundary_file=test_boundary_file
        )

        detector1.trigger_count = 50
        detector1.trigger_time = time.time() - 300
        detector1.probe_count = 1
        detector1.state = "PROBING"
        detector1.total_probes = 1

        # 模拟探测成功并保存
        asyncio.run(detector1.on_probe_success())

        # 创建新探测器，应该能加载边界
        detector2 = RateLimitDetector(
            enable=True,
            source="test",
            interface="test_api",
            data_type="test",
            boundary_file=test_boundary_file
        )

        assert detector2.state == "CONFIRMED"
        assert detector2.boundary is not None
        assert detector2.boundary.max_requests == 50
        assert detector2.safe_batch_size == 40

    def test_multiple_sources(self, test_boundary_file):
        """测试多数据源支持"""
        # 创建第一个数据源的探测器
        detector1 = RateLimitDetector(
            enable=True,
            source="source1",
            interface="api1",
            data_type="daily",
            boundary_file=test_boundary_file
        )
        detector1.trigger_count = 50
        detector1.trigger_time = time.time() - 300
        detector1.probe_count = 1
        detector1.state = "PROBING"
        asyncio.run(detector1.on_probe_success())

        # 创建第二个数据源的探测器
        detector2 = RateLimitDetector(
            enable=True,
            source="source2",
            interface="api2",
            data_type="minute",
            boundary_file=test_boundary_file
        )
        detector2.trigger_count = 100
        detector2.trigger_time = time.time() - 600
        detector2.probe_count = 2
        detector2.state = "PROBING"
        asyncio.run(detector2.on_probe_success())

        # 验证文件包含两个数据源
        with open(test_boundary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert len(data['boundaries']) == 2
        assert 'source1.api1.daily' in data['boundaries']
        assert 'source2.api2.minute' in data['boundaries']

        # 创建新探测器验证能分别加载
        detector3 = RateLimitDetector(
            enable=True,
            source="source1",
            interface="api1",
            data_type="daily",
            boundary_file=test_boundary_file
        )
        assert detector3.boundary.max_requests == 50

        detector4 = RateLimitDetector(
            enable=True,
            source="source2",
            interface="api2",
            data_type="minute",
            boundary_file=test_boundary_file
        )
        assert detector4.boundary.max_requests == 100

    def test_get_stats(self, detector):
        """测试获取统计信息"""
        # 记录一些数据
        for _ in range(10):
            detector.record_success()

        stats = detector.get_stats()

        assert stats["enabled"] is True
        assert stats["boundary_key"] == "test.test_api.test"
        assert stats["state"] == "NORMAL"
        assert stats["total_success"] == 10
        assert stats["boundary"] is None

    def test_confidence_calculation(self, detector):
        """测试置信度计算"""
        # probe_count=1 -> high
        detector.probe_count = 1
        assert detector._calculate_confidence() == "high"

        # probe_count=2 -> medium
        detector.probe_count = 2
        assert detector._calculate_confidence() == "medium"

        # probe_count=4 -> low
        detector.probe_count = 4
        assert detector._calculate_confidence() == "low"


@pytest.mark.asyncio
async def test_integration_scenario(tmp_path):
    """集成测试：完整的探测流程"""
    boundary_file = str(tmp_path / "integration_test.json")

    detector = RateLimitDetector(
        enable=True,
        source="integration_test",
        interface="test_api",
        data_type="test",
        boundary_file=boundary_file
    )

    # 阶段1：正常采集
    for i in range(50):
        detector.record_success()

    assert detector.state == "NORMAL"
    assert detector.success_count == 50

    # 阶段2：触发限流
    await detector.on_rate_limit_triggered()
    assert detector.state == "PAUSED"
    assert detector.trigger_count == 50

    # 阶段3：等待探测
    should_wait, wait_seconds = await detector.should_pause()
    assert should_wait is True

    # 阶段4：模拟时间流逝，探测时间到
    detector.next_probe_time = time.time() - 1
    should_wait, wait_seconds = await detector.should_pause()
    assert should_wait is False
    assert detector.state == "PROBING"

    # 阶段5：探测成功
    await detector.on_probe_success()
    assert detector.state == "CONFIRMED"
    assert detector.boundary is not None

    # 阶段6：验证边界已保存
    assert os.path.exists(boundary_file)

    # 阶段7：新实例能加载边界
    detector2 = RateLimitDetector(
        enable=True,
        source="integration_test",
        interface="test_api",
        data_type="test",
        boundary_file=boundary_file
    )
    assert detector2.state == "CONFIRMED"
    assert detector2.boundary is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
