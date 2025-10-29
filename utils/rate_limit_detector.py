"""
智能限流探测器

用于自动探测API限流窗口和上限，并提供智能等待策略
"""

import time
import asyncio
from typing import Optional
from core.logger import logger


class RateLimitDetector:
    """
    智能限流探测器

    功能：
    - 记录所有请求时间戳
    - 检测限流失败并分析窗口大小
    - 每1分钟试探一次直到找到窗口
    - 提供智能等待建议
    - 统计和报告探测结果

    使用示例：
    ```python
    detector = RateLimitDetector()

    for stock in stocks:
        # 检查是否需要等待
        should_wait, wait_seconds = await detector.should_pause()
        if should_wait:
            await asyncio.sleep(wait_seconds)

        try:
            await collect(stock)
            detector.record_success()
        except RateLimitError:
            await detector.on_rate_limit_error()
    ```
    """

    # 候选窗口大小（秒）
    CANDIDATE_WINDOWS = [60, 180, 300, 600, 900]  # 1/3/5/10/15分钟

    # 探测阶段
    PHASE_NORMAL = "normal"       # 正常采集
    PHASE_DETECTING = "detecting"  # 探测中
    PHASE_CONFIRMED = "confirmed"  # 已确认

    def __init__(self, enable: bool = True):
        """
        初始化探测器

        Args:
            enable: 是否启用探测功能
        """
        self.enable = enable

        # 请求历史
        self.request_history: list[float] = []

        # 探测状态
        self.detection_phase = self.PHASE_NORMAL
        self.first_failure_time: Optional[float] = None
        self.detection_start_time: Optional[float] = None
        self.probe_count = 0  # 试探次数

        # 探测结果
        self.detected_window: Optional[int] = None  # 窗口大小（秒）
        self.detected_limit: Optional[int] = None   # 请求上限

        # 统计
        self.total_requests = 0
        self.total_rate_limit_errors = 0
        self.total_probes = 0
        self.total_wait_time = 0.0

        logger.info(f"限流探测器初始化: {'启用' if enable else '禁用'}")

    def record_success(self):
        """
        记录成功的请求
        """
        if not self.enable:
            return

        now = time.time()
        self.request_history.append(now)
        self.total_requests += 1

        # 只保留最近15分钟的记录（最大窗口）
        cutoff = now - 900
        self.request_history = [t for t in self.request_history if t >= cutoff]

    async def on_rate_limit_error(self):
        """
        处理限流错误

        触发探测流程：
        1. 记录第一次失败时间
        2. 分析候选窗口
        3. 开始探测
        """
        if not self.enable:
            return

        self.total_rate_limit_errors += 1
        now = time.time()

        # 如果已经在探测中，不重复处理
        if self.detection_phase == self.PHASE_DETECTING:
            logger.debug("探测进行中，跳过")
            return

        # 如果已确认窗口，说明再次触发限流（可能是误判或窗口变化）
        if self.detection_phase == self.PHASE_CONFIRMED:
            logger.warning("已确认窗口后再次触发限流，可能需要重新探测")
            # 暂不处理，继续使用已知窗口
            return

        # 第一次触发限流，开始探测
        logger.warning("🚨 检测到限流错误，启动智能探测...")
        self.first_failure_time = now
        self.detection_start_time = now
        self.detection_phase = self.PHASE_DETECTING
        self.probe_count = 0

        # 分析候选窗口
        self._analyze_candidate_windows()

    def _analyze_candidate_windows(self):
        """
        分析候选窗口

        统计每个候选窗口内的请求数，找到最可能的窗口
        """
        if not self.first_failure_time:
            return

        logger.info("📊 分析请求历史...")

        analysis = {}
        for window in self.CANDIDATE_WINDOWS:
            window_start = self.first_failure_time - window
            count = sum(1 for t in self.request_history if t >= window_start)
            analysis[window] = count
            logger.info(f"  - 过去 {window:>3}秒 ({window//60:>2}分钟): {count:>3}次请求")

        # 找到请求数最多的最小窗口（最可能的限流窗口）
        max_count = max(analysis.values())
        likely_windows = [w for w, c in analysis.items() if c == max_count]
        likely_window = min(likely_windows)

        logger.info(f"💡 推测窗口: {likely_window}秒 ({likely_window//60}分钟)")

    async def should_pause(self) -> tuple[bool, int]:
        """
        判断是否需要暂停

        Returns:
            (是否需要暂停, 等待秒数)
        """
        if not self.enable:
            return False, 0

        # 探测阶段：每分钟试探一次
        if self.detection_phase == self.PHASE_DETECTING:
            return await self._handle_detection_phase()

        # 已确认窗口：智能等待
        if self.detection_phase == self.PHASE_CONFIRMED:
            return self._handle_confirmed_phase()

        # 正常阶段：无需等待
        return False, 0

    async def _handle_detection_phase(self) -> tuple[bool, int]:
        """
        处理探测阶段

        每分钟试探一次，直到成功或超时（15分钟）

        Returns:
            (是否需要暂停, 等待秒数)
        """
        if not self.detection_start_time:
            return False, 0

        now = time.time()
        elapsed = now - self.detection_start_time

        # 超过15分钟还未探测成功，放弃探测
        if elapsed > 900:
            logger.error("❌ 探测超时（15分钟），放弃探测")
            self.detection_phase = self.PHASE_NORMAL
            return False, 0

        # 计算下一次试探时间
        next_probe_time = self.detection_start_time + (self.probe_count + 1) * 60
        wait_seconds = int(next_probe_time - now)

        if wait_seconds > 0:
            logger.info(f"⏸️  探测等待 {wait_seconds} 秒 ({self.probe_count + 1}/15)...")
            self.total_wait_time += wait_seconds
            return True, wait_seconds

        # 时间到了，执行试探
        self.probe_count += 1
        self.total_probes += 1
        logger.info(f"🔬 试探请求 (第 {self.probe_count} 次)...")

        # 不暂停，让调用方继续执行请求
        # 调用方应该：
        # 1. 尝试请求
        # 2. 如果成功，调用 confirm_window_detected()
        # 3. 如果失败，继续下一轮探测
        return False, 0

    def _handle_confirmed_phase(self) -> tuple[bool, int]:
        """
        处理已确认窗口阶段

        计算窗口内请求数，如果接近上限则等待

        Returns:
            (是否需要暂停, 等待秒数)
        """
        if not self.detected_window or not self.detected_limit:
            return False, 0

        now = time.time()
        window_start = now - self.detected_window

        # 统计窗口内请求数
        requests_in_window = [t for t in self.request_history if t >= window_start]
        count_in_window = len(requests_in_window)

        # 预留安全边界（10%）
        safety_limit = int(self.detected_limit * 0.9)

        if count_in_window < safety_limit:
            # 安全，无需等待
            return False, 0

        # 接近上限，计算需要等待的时间
        # 等到最早的请求滑出窗口
        if not requests_in_window:
            return False, 0

        oldest_request = requests_in_window[0]
        wait_until = oldest_request + self.detected_window
        wait_seconds = int(wait_until - now) + 5  # 加5秒缓冲

        if wait_seconds > 0:
            logger.info(
                f"⏸️  接近限流上限 ({count_in_window}/{self.detected_limit})，"
                f"精确等待 {wait_seconds} 秒..."
            )
            self.total_wait_time += wait_seconds
            return True, wait_seconds

        return False, 0

    def confirm_window_detected(self):
        """
        确认探测到窗口

        在试探请求成功后调用此方法
        """
        if self.detection_phase != self.PHASE_DETECTING:
            return

        if not self.first_failure_time:
            return

        # 计算窗口大小
        now = time.time()
        window_seconds = int(now - self.first_failure_time)

        # 找到最接近的候选窗口
        detected_window = min(
            self.CANDIDATE_WINDOWS,
            key=lambda w: abs(w - window_seconds)
        )

        # 计算该窗口的请求上限
        window_start = self.first_failure_time - detected_window
        detected_limit = sum(
            1 for t in self.request_history
            if window_start <= t < self.first_failure_time
        )

        self.detected_window = detected_window
        self.detected_limit = detected_limit
        self.detection_phase = self.PHASE_CONFIRMED

        logger.info("=" * 60)
        logger.info("🎯 探测完成！")
        logger.info(f"   - 窗口大小: {detected_window}秒 ({detected_window//60}分钟)")
        logger.info(f"   - 请求上限: 约{detected_limit}次")
        logger.info(f"   - 安全策略: 每{detected_window}秒最多{int(detected_limit * 0.9)}次")
        logger.info(f"   - 试探次数: {self.probe_count}次")
        logger.info(f"   - 总耗时: {self.probe_count}分钟")
        logger.info("=" * 60)

    def get_stats(self) -> dict:
        """
        获取探测统计信息

        Returns:
            统计信息字典
        """
        return {
            "enabled": self.enable,
            "phase": self.detection_phase,
            "detected_window": self.detected_window,
            "detected_limit": self.detected_limit,
            "total_requests": self.total_requests,
            "total_rate_limit_errors": self.total_rate_limit_errors,
            "total_probes": self.total_probes,
            "total_wait_time": self.total_wait_time,
            "requests_in_history": len(self.request_history),
        }

    def print_summary(self):
        """
        打印探测总结
        """
        stats = self.get_stats()

        logger.info("=" * 60)
        logger.info("限流探测器总结")
        logger.info("-" * 60)
        logger.info(f"探测状态: {stats['phase']}")

        if stats["detected_window"]:
            logger.info(f"窗口大小: {stats['detected_window']}秒 ({stats['detected_window']//60}分钟)")
            logger.info(f"请求上限: {stats['detected_limit']}次")

        logger.info(f"总请求数: {stats['total_requests']}")
        logger.info(f"限流次数: {stats['total_rate_limit_errors']}")
        logger.info(f"试探次数: {stats['total_probes']}")
        logger.info(f"总等待时长: {stats['total_wait_time']:.0f}秒 ({stats['total_wait_time']/60:.1f}分钟)")
        logger.info("=" * 60)


def is_rate_limit_error(error: Exception) -> bool:
    """
    判断是否为限流错误

    常见限流错误特征：
    - ProxyError
    - RemoteDisconnected
    - 429 Too Many Requests
    - Connection reset
    - 请求过于频繁

    Args:
        error: 异常对象

    Returns:
        True表示是限流错误
    """
    error_str = str(error).lower()

    rate_limit_keywords = [
        "proxyerror",
        "remotedisconnected",
        "connection reset",
        "429",
        "too many requests",
        "rate limit",
        "请求过于频繁",
        "访问过于频繁",
        "too many",
        "max retries",
    ]

    return any(keyword in error_str for keyword in rate_limit_keywords)


__all__ = ["RateLimitDetector", "is_rate_limit_error"]
