"""
智能限流探测器（简化版）

用于自动探测API限流边界，并提供智能等待策略。
支持多数据源/接口的边界管理和持久化。
"""

import os
import json
import time
import asyncio
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from core.logger import logger


@dataclass
class RateLimitBoundary:
    """限流边界信息"""
    max_requests: int          # 触发限流前的最大请求数
    wait_time_seconds: int     # 恢复所需的等待时间（秒）
    window_seconds: int        # 推测的时间窗口（秒）
    detected_at: float         # 探测时间戳
    confidence: str            # 置信度: 'low' / 'medium' / 'high'


class RateLimitDetector:
    """
    智能限流探测器（简化版）

    核心逻辑：
    1. 触发限流时：立即暂停，记录已成功请求数
    2. 探测策略：固定每5分钟重试一次（5min、10min、15min...）
    3. 成功后：保存"边界信息"（成功请求数 + 等待时长）
    4. 后续采集：根据边界动态调整批次大小和暂停时间
    5. 再次触发：重新评估并更新边界

    状态机：
    - NORMAL: 正常采集
    - PAUSED: 已触发限流，暂停中
    - PROBING: 正在探测（每5分钟试一次）
    - CONFIRMED: 已确认边界，智能采集

    使用示例：
    ```python
    # 初始化（指定数据源和接口）
    detector = RateLimitDetector(
        enable=True,
        source="akshare",
        interface="stock_zh_a_hist",
        data_type="daily",
        description="A股日线数据"
    )

    # 采集循环
    for stock in stocks:
        # 检查是否需要暂停
        should_wait, wait_seconds = await detector.should_pause()
        if should_wait:
            await asyncio.sleep(wait_seconds)

        try:
            data = await collect(stock)
            detector.record_success()

            # 如果正在探测，成功意味着探测成功
            if detector.state == "PROBING":
                await detector.on_probe_success()
        except Exception as e:
            if is_rate_limit_error(e):
                if detector.state == "NORMAL":
                    await detector.on_rate_limit_triggered()
                elif detector.state == "PROBING":
                    await detector.on_probe_failed()
                elif detector.state == "CONFIRMED":
                    await detector.on_rate_limit_re_triggered()
    ```
    """

    # 探测间隔（固定5分钟）
    PROBE_INTERVAL = 300  # 秒

    # 状态
    STATE_NORMAL = "NORMAL"
    STATE_PAUSED = "PAUSED"
    STATE_PROBING = "PROBING"
    STATE_CONFIRMED = "CONFIRMED"

    def __init__(
        self,
        enable: bool = True,
        source: str = "akshare",
        interface: str = "stock_zh_a_hist",
        data_type: str = "daily",
        description: str = "",
        boundary_file: str = ".rate_limit_boundaries.json"
    ):
        """
        初始化限流探测器

        Args:
            enable: 是否启用探测
            source: 数据源名称（如：akshare, baostock, tushare）
            interface: 接口名称（如：stock_zh_a_hist, query_history_k_data）
            data_type: 数据类型（如：daily, minute, tick）
            description: 接口描述（如：A股日线数据）
            boundary_file: 边界文件路径
        """
        self.enable = enable
        self.source = source
        self.interface = interface
        self.data_type = data_type
        self.description = description or f"{source}的{data_type}数据"
        self.boundary_file = boundary_file

        # 生成边界key
        self.boundary_key = f"{source}.{interface}.{data_type}"

        # 状态
        self.state = self.STATE_NORMAL
        self.boundary: Optional[RateLimitBoundary] = None

        # 请求历史（时间戳列表）
        self.request_history: list[float] = []
        self.success_count = 0  # 总成功请求数

        # 触发信息
        self.trigger_count = 0  # 触发时的成功次数
        self.trigger_time: Optional[float] = None

        # 探测信息
        self.probe_interval = self.PROBE_INTERVAL
        self.probe_count = 0
        self.next_probe_time: Optional[float] = None

        # 安全策略
        self.safe_batch_size = 50  # 默认批次
        self.safe_pause_time = 0   # 默认不暂停

        # 统计
        self.total_rate_limit_errors = 0
        self.total_probes = 0
        self.total_wait_time = 0.0

        logger.info(f"[{self.boundary_key}] 限流探测器初始化: {'启用' if enable else '禁用'}")

        # 启动时加载已有边界
        if self.enable:
            self._load_boundary()

    def _load_boundary(self) -> None:
        """从文件加载边界信息"""
        if not os.path.exists(self.boundary_file):
            logger.info(f"[{self.boundary_key}] 未找到边界记录文件，将首次探测")
            return

        try:
            with open(self.boundary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 查找对应接口的边界
            boundary_data = data.get('boundaries', {}).get(self.boundary_key)
            if not boundary_data:
                logger.info(f"[{self.boundary_key}] 未找到该接口的边界记录，将首次探测")
                return

            current = boundary_data.get('current_boundary')
            if current:
                self.boundary = RateLimitBoundary(
                    max_requests=current['max_requests'],
                    wait_time_seconds=current['wait_time_seconds'],
                    window_seconds=current['window_seconds'],
                    detected_at=current['detected_at_timestamp'],
                    confidence=current['confidence']
                )
                self.safe_batch_size = current['safe_batch_size']
                self.safe_pause_time = current['safe_pause_time']
                self.state = self.STATE_CONFIRMED

                logger.info(f"[{self.boundary_key}] ✅ 加载已有边界: {self.boundary.max_requests}次/{self.boundary.window_seconds}秒 ({self.boundary.window_seconds//60}分钟)")
                logger.info(f"[{self.boundary_key}]    安全策略: 批次{self.safe_batch_size}次，暂停{self.safe_pause_time}秒 ({self.safe_pause_time//60}分钟)")
                logger.info(f"[{self.boundary_key}]    历史探测: {len(boundary_data.get('history', []))}次")

        except Exception as e:
            logger.warning(f"[{self.boundary_key}] 加载边界文件失败: {e}，将重新探测")

    def _save_boundary(self, notes: str = "") -> None:
        """保存边界信息到文件"""
        if not self.boundary:
            return

        try:
            # 读取现有数据
            if os.path.exists(self.boundary_file):
                with open(self.boundary_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    "version": "1.0",
                    "boundaries": {},
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "last_update": None,
                        "total_sources": 0
                    }
                }

            # 确保该接口的数据结构存在
            if self.boundary_key not in data['boundaries']:
                data['boundaries'][self.boundary_key] = {
                    "source": self.source,
                    "interface": self.interface,
                    "data_type": self.data_type,
                    "description": self.description,
                    "current_boundary": None,
                    "history": [],
                    "statistics": {
                        "total_detections": 0,
                        "total_rate_limits": 0,
                        "total_probes": 0,
                        "first_detection": None,
                        "last_update": None
                    }
                }

            boundary_info = data['boundaries'][self.boundary_key]

            # 添加新的边界记录
            now = datetime.now()
            boundary_record = {
                "max_requests": self.boundary.max_requests,
                "wait_time_seconds": self.boundary.wait_time_seconds,
                "window_seconds": self.boundary.window_seconds,
                "detected_at": now.isoformat(),
                "detected_at_timestamp": self.boundary.detected_at,
                "confidence": self.boundary.confidence,
                "trigger_count": self.trigger_count,
                "probe_count": self.probe_count,
                "notes": notes
            }
            boundary_info['history'].append(boundary_record)

            # 更新当前边界
            boundary_info['current_boundary'] = {
                **boundary_record,
                "safe_batch_size": self.safe_batch_size,
                "safe_pause_time": self.safe_pause_time
            }

            # 更新统计信息
            stats = boundary_info['statistics']
            stats['total_detections'] += 1
            stats['total_rate_limits'] = self.total_rate_limit_errors
            stats['total_probes'] = self.total_probes
            if not stats.get('first_detection'):
                stats['first_detection'] = now.isoformat()
            stats['last_update'] = now.isoformat()

            # 更新全局元数据
            data['metadata']['last_update'] = now.isoformat()
            data['metadata']['total_sources'] = len(data['boundaries'])

            # 保存到文件
            with open(self.boundary_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"[{self.boundary_key}] 💾 边界信息已保存到 {self.boundary_file}")

        except Exception as e:
            logger.error(f"[{self.boundary_key}] 保存边界文件失败: {e}")

    def record_success(self) -> None:
        """记录成功的请求"""
        if not self.enable:
            return

        now = time.time()
        self.request_history.append(now)
        self.success_count += 1

        # 只保留最近20分钟的记录（超出最大可能窗口）
        cutoff = now - 1200
        self.request_history = [t for t in self.request_history if t >= cutoff]

    async def on_rate_limit_triggered(self) -> None:
        """限流触发"""
        if not self.enable:
            return

        self.total_rate_limit_errors += 1

        # 记录当前状态
        self.trigger_count = self.success_count
        self.trigger_time = time.time()

        # 切换到暂停状态
        self.state = self.STATE_PAUSED
        self.probe_count = 0
        self.next_probe_time = self.trigger_time + self.probe_interval

        logger.warning(f"[{self.boundary_key}] 🚨 触发限流！已成功{self.trigger_count}次，暂停{self.probe_interval}秒后开始探测")

    async def on_probe_success(self) -> None:
        """探测成功"""
        if not self.enable:
            return

        elapsed = time.time() - self.trigger_time
        elapsed_minutes = int(elapsed / 60)

        # 保存边界信息
        self.boundary = RateLimitBoundary(
            max_requests=self.trigger_count,
            wait_time_seconds=int(elapsed),
            window_seconds=int(elapsed),  # 简化：等待时长即窗口大小
            detected_at=time.time(),
            confidence=self._calculate_confidence()
        )

        self.state = self.STATE_CONFIRMED

        # 计算安全策略
        self.safe_batch_size = max(1, int(self.boundary.max_requests * 0.8))  # 80%安全阈值
        self.safe_pause_time = int(self.boundary.window_seconds * 1.2)  # 120%安全窗口

        logger.info("=" * 70)
        logger.info(f"[{self.boundary_key}] ✅ 探测成功！")
        logger.info(f"   边界: {self.boundary.max_requests}次 / {self.boundary.window_seconds}秒 ({elapsed_minutes}分钟)")
        logger.info(f"   置信度: {self.boundary.confidence}")
        logger.info(f"   安全策略: 批次{self.safe_batch_size}次，暂停{self.safe_pause_time}秒 ({self.safe_pause_time//60}分钟)")
        logger.info(f"   探测次数: {self.probe_count}次")
        logger.info("=" * 70)

        # 保存到文件
        notes = f"探测{self.probe_count}次后成功" if self.probe_count > 1 else "首次探测成功"
        self._save_boundary(notes)

    async def on_probe_failed(self) -> None:
        """探测失败"""
        if not self.enable:
            return

        self.next_probe_time = time.time() + self.probe_interval
        logger.warning(f"[{self.boundary_key}] ❌ 第{self.probe_count}次探测失败，{self.probe_interval}秒后再试")

    async def on_rate_limit_re_triggered(self) -> None:
        """已确认边界后再次触发限流"""
        if not self.enable:
            return

        if self.state == self.STATE_CONFIRMED:
            logger.warning(f"[{self.boundary_key}] ⚠️ 边界评估不准确，重新探测")

            old_boundary = self.boundary

            # 重置状态，重新探测
            self.trigger_count = self.success_count
            self.trigger_time = time.time()
            self.state = self.STATE_PAUSED
            self.probe_count = 0
            self.next_probe_time = time.time() + self.probe_interval

            logger.info(f"[{self.boundary_key}] 旧边界: {old_boundary.max_requests}次/{old_boundary.window_seconds}秒")
            logger.info(f"[{self.boundary_key}] 本次触发: {self.trigger_count}次，开始重新探测")

            self.total_rate_limit_errors += 1

    async def should_pause(self) -> tuple[bool, int]:
        """
        判断是否需要暂停

        Returns:
            (是否需要暂停, 等待秒数)
        """
        if not self.enable:
            return False, 0

        if self.state == self.STATE_NORMAL:
            return False, 0

        if self.state == self.STATE_CONFIRMED:
            # 已确认边界，检查是否需要主动暂停
            return self._check_boundary_limit()

        if self.state in [self.STATE_PAUSED, self.STATE_PROBING]:
            now = time.time()
            if now < self.next_probe_time:
                # 还需要等待
                wait_seconds = int(self.next_probe_time - now)
                elapsed = int(now - self.trigger_time)
                logger.info(f"[{self.boundary_key}] ⏸️  探测等待 {wait_seconds} 秒 (已等待{elapsed}秒, 第{self.probe_count + 1}次探测)...")
                return True, wait_seconds
            else:
                # 可以尝试探测了
                self.state = self.STATE_PROBING
                self.probe_count += 1
                self.total_probes += 1
                elapsed = int(time.time() - self.trigger_time)
                logger.info(f"[{self.boundary_key}] 🔬 开始第{self.probe_count}次探测（已等待{elapsed}秒）")
                return False, 0

        return False, 0

    def _check_boundary_limit(self) -> tuple[bool, int]:
        """检查是否达到边界限制"""
        if not self.boundary:
            return False, 0

        # 计算当前窗口内的请求数
        now = time.time()
        window_start = now - self.boundary.window_seconds
        requests_in_window = sum(1 for t in self.request_history if t > window_start)

        # 如果达到安全阈值，主动暂停
        if requests_in_window >= self.safe_batch_size:
            wait_time = self.safe_pause_time
            logger.info(f"[{self.boundary_key}] 📊 达到安全批次大小{self.safe_batch_size}（窗口内已{requests_in_window}次），主动暂停{wait_time}秒 ({wait_time//60}分钟)")
            return True, wait_time

        return False, 0

    def _calculate_confidence(self) -> str:
        """计算置信度"""
        if self.probe_count == 1:
            return "high"
        elif self.probe_count <= 3:
            return "medium"
        else:
            return "low"

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "enabled": self.enable,
            "boundary_key": self.boundary_key,
            "state": self.state,
            "boundary": {
                "max_requests": self.boundary.max_requests if self.boundary else None,
                "window_seconds": self.boundary.window_seconds if self.boundary else None,
                "confidence": self.boundary.confidence if self.boundary else None,
            } if self.boundary else None,
            "safe_batch_size": self.safe_batch_size,
            "safe_pause_time": self.safe_pause_time,
            "total_success": self.success_count,
            "total_rate_limit_errors": self.total_rate_limit_errors,
            "total_probes": self.total_probes,
            "total_wait_time": self.total_wait_time,
        }

    def print_boundary_history(self) -> None:
        """打印该接口的边界历史"""
        if not os.path.exists(self.boundary_file):
            print(f"📝 [{self.boundary_key}] 暂无边界记录")
            return

        try:
            with open(self.boundary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            boundary_data = data.get('boundaries', {}).get(self.boundary_key)
            if not boundary_data:
                print(f"📝 [{self.boundary_key}] 暂无边界记录")
                return

            history = boundary_data.get('history', [])
            stats = boundary_data.get('statistics', {})

            print(f"\n📝 边界探测历史 - {self.description}")
            print(f"   数据源: {self.source} | 接口: {self.interface} | 类型: {self.data_type}")
            print("=" * 80)
            print(f"总探测次数: {stats.get('total_detections', 0)}")
            print(f"总限流次数: {stats.get('total_rate_limits', 0)}")
            print(f"总试探次数: {stats.get('total_probes', 0)}")
            print(f"首次探测: {stats.get('first_detection', 'N/A')}")
            print(f"最后更新: {stats.get('last_update', 'N/A')}")
            print("=" * 80)

            if history:
                for i, record in enumerate(history, 1):
                    print(f"\n#{i} - {record['detected_at']}")
                    print(f"   边界: {record['max_requests']}次 / {record['window_seconds']}秒 ({record['window_seconds']//60}分钟)")
                    print(f"   置信度: {record['confidence']}")
                    print(f"   探测次数: {record['probe_count']}")
                    print(f"   备注: {record['notes']}")

            print("=" * 80)

        except Exception as e:
            logger.error(f"读取边界历史失败: {e}")


def print_all_boundaries(boundary_file: str = ".rate_limit_boundaries.json") -> None:
    """打印所有接口的边界信息"""
    if not os.path.exists(boundary_file):
        print("📝 暂无边界记录")
        return

    try:
        with open(boundary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        boundaries = data.get('boundaries', {})
        metadata = data.get('metadata', {})

        print(f"\n📊 限流边界总览")
        print("=" * 80)
        print(f"文件版本: {data.get('version', 'N/A')}")
        print(f"创建时间: {metadata.get('created_at', 'N/A')}")
        print(f"最后更新: {metadata.get('last_update', 'N/A')}")
        print(f"数据源数量: {metadata.get('total_sources', 0)}")
        print("=" * 80)

        for key, boundary_data in boundaries.items():
            current = boundary_data.get('current_boundary')
            stats = boundary_data.get('statistics', {})

            print(f"\n🔹 {key}")
            print(f"   描述: {boundary_data.get('description', 'N/A')}")

            if current:
                print(f"   当前边界: {current['max_requests']}次 / {current['window_seconds']}秒 ({current['window_seconds']//60}分钟)")
                print(f"   安全策略: 批次{current['safe_batch_size']}次, 暂停{current['safe_pause_time']}秒 ({current['safe_pause_time']//60}分钟)")
                print(f"   置信度: {current['confidence']}")
                print(f"   探测时间: {current['detected_at']}")
            else:
                print(f"   当前边界: 未探测")

            print(f"   探测历史: {stats.get('total_detections', 0)}次")
            print(f"   限流次数: {stats.get('total_rate_limits', 0)}次")

        print("=" * 80)

    except Exception as e:
        print(f"读取边界文件失败: {e}")


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


__all__ = ["RateLimitDetector", "RateLimitBoundary", "is_rate_limit_error", "print_all_boundaries"]
