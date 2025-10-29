"""
智能限流探测器测试
"""

import pytest
import time
import asyncio
from utils.rate_limit_detector import RateLimitDetector, is_rate_limit_error


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

    def test_init(self):
        """测试初始化"""
        detector = RateLimitDetector(enable=True)

        assert detector.enable is True
        assert detector.detection_phase == "normal"
        assert detector.detected_window is None
        assert detector.detected_limit is None
        assert len(detector.request_history) == 0

    def test_init_disabled(self):
        """测试禁用状态"""
        detector = RateLimitDetector(enable=False)
        assert detector.enable is False

    def test_record_success(self):
        """测试记录成功请求"""
        detector = RateLimitDetector()

        detector.record_success()
        assert len(detector.request_history) == 1
        assert detector.total_requests == 1

        detector.record_success()
        assert len(detector.request_history) == 2
        assert detector.total_requests == 2

    def test_record_success_disabled(self):
        """测试禁用时不记录"""
        detector = RateLimitDetector(enable=False)

        detector.record_success()
        assert len(detector.request_history) == 0
        assert detector.total_requests == 0

    def test_record_success_cleanup(self):
        """测试清理旧记录（超过15分钟）"""
        detector = RateLimitDetector()

        # 模拟添加16分钟前的请求
        old_time = time.time() - 960  # 16分钟前
        detector.request_history.append(old_time)

        # 添加新请求
        detector.record_success()

        # 旧记录应该被清理
        assert len(detector.request_history) == 1
        assert detector.request_history[0] > old_time

    @pytest.mark.asyncio
    async def test_on_rate_limit_error(self):
        """测试触发限流错误"""
        detector = RateLimitDetector()

        # 先记录一些成功请求
        for _ in range(10):
            detector.record_success()

        # 触发限流
        await detector.on_rate_limit_error()

        assert detector.detection_phase == "detecting"
        assert detector.first_failure_time is not None
        assert detector.total_rate_limit_errors == 1

    @pytest.mark.asyncio
    async def test_should_pause_normal_phase(self):
        """测试正常阶段不暂停"""
        detector = RateLimitDetector()

        should_wait, wait_seconds = await detector.should_pause()

        assert should_wait is False
        assert wait_seconds == 0

    @pytest.mark.asyncio
    async def test_should_pause_detecting_phase(self):
        """测试探测阶段需要暂停"""
        detector = RateLimitDetector()

        # 记录一些请求
        for _ in range(50):
            detector.record_success()
            time.sleep(0.01)  # 模拟时间间隔

        # 触发限流，进入探测阶段
        await detector.on_rate_limit_error()

        # 立即检查，应该需要等待约60秒
        should_wait, wait_seconds = await detector.should_pause()

        assert should_wait is True
        assert 55 <= wait_seconds <= 65  # 允许一些误差

    @pytest.mark.asyncio
    async def test_should_pause_disabled(self):
        """测试禁用时不暂停"""
        detector = RateLimitDetector(enable=False)

        await detector.on_rate_limit_error()
        should_wait, wait_seconds = await detector.should_pause()

        assert should_wait is False
        assert wait_seconds == 0

    def test_confirm_window_detected(self):
        """测试确认窗口探测成功"""
        detector = RateLimitDetector()

        # 模拟场景：5分钟内请求了78次，然后失败
        base_time = time.time() - 10  # 从10秒前开始
        for i in range(78):
            detector.request_history.append(base_time - 300 + i * 3.8)  # 分布在5分钟内

        # 设置失败时间为base_time（78次请求后）
        detector.first_failure_time = base_time
        detector.detection_phase = "detecting"
        detector.probe_count = 5

        # 现在试探成功，确认窗口
        detector.confirm_window_detected()

        assert detector.detection_phase == "confirmed"
        assert detector.detected_window is not None
        assert detector.detected_limit is not None
        assert detector.detected_limit > 0

    def test_confirm_window_not_in_detecting_phase(self):
        """测试非探测阶段不确认"""
        detector = RateLimitDetector()

        detector.confirm_window_detected()

        # 状态不应该改变
        assert detector.detection_phase == "normal"
        assert detector.detected_window is None

    @pytest.mark.asyncio
    async def test_should_pause_confirmed_phase_safe(self):
        """测试已确认阶段，请求数安全时不暂停"""
        detector = RateLimitDetector()

        # 模拟已确认窗口：300秒内最多100次
        detector.detection_phase = "confirmed"
        detector.detected_window = 300
        detector.detected_limit = 100

        # 只记录50次请求（低于安全限制90次）
        now = time.time()
        for i in range(50):
            detector.request_history.append(now - 100 + i * 2)

        should_wait, wait_seconds = await detector.should_pause()

        assert should_wait is False
        assert wait_seconds == 0

    @pytest.mark.asyncio
    async def test_should_pause_confirmed_phase_near_limit(self):
        """测试已确认阶段，接近上限时需要暂停"""
        detector = RateLimitDetector()

        # 模拟已确认窗口：300秒内最多100次
        detector.detection_phase = "confirmed"
        detector.detected_window = 300
        detector.detected_limit = 100

        # 记录95次请求（超过安全限制90次）
        now = time.time()
        for i in range(95):
            detector.request_history.append(now - 290 + i * 3)

        should_wait, wait_seconds = await detector.should_pause()

        assert should_wait is True
        assert wait_seconds > 0

    def test_get_stats(self):
        """测试获取统计信息"""
        detector = RateLimitDetector()

        # 记录一些数据
        for _ in range(10):
            detector.record_success()

        stats = detector.get_stats()

        assert stats["enabled"] is True
        assert stats["phase"] == "normal"
        assert stats["total_requests"] == 10
        assert stats["requests_in_history"] == 10

    def test_get_stats_after_detection(self):
        """测试探测后的统计信息"""
        detector = RateLimitDetector()

        # 模拟探测完成
        detector.detection_phase = "confirmed"
        detector.detected_window = 300
        detector.detected_limit = 80
        detector.total_requests = 100
        detector.total_rate_limit_errors = 1
        detector.total_probes = 5
        detector.total_wait_time = 300.0

        stats = detector.get_stats()

        assert stats["phase"] == "confirmed"
        assert stats["detected_window"] == 300
        assert stats["detected_limit"] == 80
        assert stats["total_requests"] == 100
        assert stats["total_rate_limit_errors"] == 1
        assert stats["total_probes"] == 5
        assert stats["total_wait_time"] == 300.0

    def test_print_summary(self):
        """测试打印总结（不抛异常即可）"""
        detector = RateLimitDetector()

        detector.total_requests = 100
        detector.detected_window = 300
        detector.detected_limit = 80

        # 应该能正常打印，不抛异常
        detector.print_summary()

    @pytest.mark.asyncio
    async def test_detection_timeout(self):
        """测试探测超时（15分钟）"""
        detector = RateLimitDetector()

        # 模拟15分钟前开始探测
        detector.detection_phase = "detecting"
        detector.detection_start_time = time.time() - 910  # 15分10秒前

        should_wait, wait_seconds = await detector.should_pause()

        # 应该放弃探测，返回正常状态
        assert detector.detection_phase == "normal"
        assert should_wait is False

    @pytest.mark.asyncio
    async def test_multiple_rate_limit_errors(self):
        """测试多次限流错误"""
        detector = RateLimitDetector()

        # 第一次限流
        await detector.on_rate_limit_error()
        assert detector.total_rate_limit_errors == 1
        assert detector.detection_phase == "detecting"

        # 探测过程中再次限流（应该被忽略）
        await detector.on_rate_limit_error()
        assert detector.total_rate_limit_errors == 2
        assert detector.detection_phase == "detecting"  # 状态不变

    @pytest.mark.asyncio
    async def test_confirmed_then_rate_limit_again(self):
        """测试确认后再次触发限流"""
        detector = RateLimitDetector()

        # 模拟已确认状态
        detector.detection_phase = "confirmed"
        detector.detected_window = 300
        detector.detected_limit = 80

        # 再次触发限流
        await detector.on_rate_limit_error()

        # 应该保持确认状态（不重新探测）
        assert detector.detection_phase == "confirmed"
        assert detector.total_rate_limit_errors == 1


@pytest.mark.asyncio
async def test_integration_scenario():
    """集成测试：完整的探测流程"""
    detector = RateLimitDetector()

    # 阶段1：正常采集
    for i in range(80):
        detector.record_success()
        time.sleep(0.001)  # 模拟时间

    # 阶段2：触发限流
    await detector.on_rate_limit_error()
    assert detector.detection_phase == "detecting"

    # 阶段3：第一次试探（应该需要等待）
    should_wait, wait_seconds = await detector.should_pause()
    assert should_wait is True

    # 阶段4：模拟等待后试探成功
    detector.confirm_window_detected()
    assert detector.detection_phase == "confirmed"
    assert detector.detected_window is not None
    assert detector.detected_limit is not None

    # 阶段5：确认后的智能等待
    stats = detector.get_stats()
    assert stats["total_requests"] == 80
    assert stats["total_rate_limit_errors"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
