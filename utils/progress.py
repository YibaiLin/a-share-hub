"""
进度管理器

用于历史数据回填的进度跟踪和断点续传
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from core.logger import logger


class ProgressTracker:
    """
    进度跟踪器

    功能:
    - 保存回填进度到JSON文件
    - 加载已有进度
    - 断点续传支持
    - 统计信息汇总
    """

    def __init__(self, progress_file: str = ".backfill_progress.json"):
        """
        初始化进度跟踪器

        Args:
            progress_file: 进度文件路径
        """
        self.progress_file = Path(progress_file)
        self.progress_data = self._load_progress()

    def _load_progress(self) -> dict:
        """
        从文件加载进度

        Returns:
            进度数据字典
        """
        if not self.progress_file.exists():
            logger.info("进度文件不存在，创建新进度")
            return self._create_empty_progress()

        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"加载进度: {len(data.get('completed_stocks', []))} 只已完成")
                return data
        except Exception as e:
            logger.error(f"加载进度文件失败: {e}")
            return self._create_empty_progress()

    def _create_empty_progress(self) -> dict:
        """
        创建空进度数据

        Returns:
            空进度字典
        """
        return {
            "start_date": "",
            "end_date": "",
            "total_stocks": 0,
            "completed_stocks": [],
            "failed_stocks": [],
            "start_time": "",
            "last_update": "",
            "statistics": {
                "success": 0,
                "failed": 0,
                "total_records": 0
            }
        }

    def save_progress(self):
        """
        保存进度到文件

        Raises:
            Exception: 保存失败
        """
        try:
            self.progress_data["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(self.progress_data, f, ensure_ascii=False, indent=2)

            logger.debug("进度已保存")
        except Exception as e:
            logger.error(f"保存进度失败: {e}")
            raise

    def init_progress(
        self,
        start_date: str,
        end_date: str,
        total_stocks: int
    ):
        """
        初始化进度（开始新的回填任务）

        Args:
            start_date: 开始日期
            end_date: 结束日期
            total_stocks: 股票总数
        """
        self.progress_data = {
            "start_date": start_date,
            "end_date": end_date,
            "total_stocks": total_stocks,
            "completed_stocks": [],
            "failed_stocks": [],
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_update": "",
            "statistics": {
                "success": 0,
                "failed": 0,
                "total_records": 0
            }
        }
        self.save_progress()
        logger.info(f"初始化进度: {start_date} ~ {end_date}, {total_stocks} 只股票")

    def is_completed(self, ts_code: str) -> bool:
        """
        检查股票是否已完成

        Args:
            ts_code: 股票代码

        Returns:
            True表示已完成
        """
        return ts_code in self.progress_data.get("completed_stocks", [])

    def mark_success(self, ts_code: str, records_count: int):
        """
        标记股票采集成功

        Args:
            ts_code: 股票代码
            records_count: 插入的记录数
        """
        if ts_code not in self.progress_data["completed_stocks"]:
            self.progress_data["completed_stocks"].append(ts_code)

        # 从失败列表中移除（如果存在）
        if ts_code in self.progress_data["failed_stocks"]:
            self.progress_data["failed_stocks"].remove(ts_code)

        # 更新统计
        self.progress_data["statistics"]["success"] += 1
        self.progress_data["statistics"]["total_records"] += records_count

        self.save_progress()

    def mark_failed(self, ts_code: str):
        """
        标记股票采集失败

        Args:
            ts_code: 股票代码
        """
        if ts_code not in self.progress_data["failed_stocks"]:
            self.progress_data["failed_stocks"].append(ts_code)

        # 从完成列表中移除（如果存在）
        if ts_code in self.progress_data["completed_stocks"]:
            self.progress_data["completed_stocks"].remove(ts_code)

        # 更新统计
        self.progress_data["statistics"]["failed"] += 1

        self.save_progress()

    def get_remaining_stocks(self, all_stocks: list[str]) -> list[str]:
        """
        获取待采集的股票列表（排除已完成）

        Args:
            all_stocks: 全部股票列表

        Returns:
            待采集的股票列表
        """
        completed = set(self.progress_data.get("completed_stocks", []))
        remaining = [stock for stock in all_stocks if stock not in completed]

        logger.info(f"待采集: {len(remaining)} 只 (总计: {len(all_stocks)})")
        return remaining

    def get_statistics(self) -> dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        stats = self.progress_data.get("statistics", {})
        total = self.progress_data.get("total_stocks", 0)
        completed = len(self.progress_data.get("completed_stocks", []))

        return {
            "total_stocks": total,
            "completed": completed,
            "remaining": total - completed,
            "success": stats.get("success", 0),
            "failed": stats.get("failed", 0),
            "total_records": stats.get("total_records", 0),
            "progress_percent": (completed / total * 100) if total > 0 else 0
        }

    def get_failed_stocks(self) -> list[str]:
        """
        获取失败的股票列表

        Returns:
            失败股票代码列表
        """
        return self.progress_data.get("failed_stocks", [])

    def clear_progress(self):
        """
        清除进度文件

        用于重新开始回填
        """
        if self.progress_file.exists():
            self.progress_file.unlink()
            logger.info("进度文件已删除")

        self.progress_data = self._create_empty_progress()

    def has_progress(self) -> bool:
        """
        检查是否有已保存的进度

        Returns:
            True表示有进度可恢复
        """
        return (
            self.progress_file.exists() and
            len(self.progress_data.get("completed_stocks", [])) > 0
        )

    def print_summary(self):
        """
        打印进度摘要
        """
        stats = self.get_statistics()

        logger.info("=" * 60)
        logger.info("回填进度摘要")
        logger.info("-" * 60)
        logger.info(f"总股票数: {stats['total_stocks']}")
        logger.info(f"已完成: {stats['completed']} ({stats['progress_percent']:.1f}%)")
        logger.info(f"待采集: {stats['remaining']}")
        logger.info(f"成功: {stats['success']}")
        logger.info(f"失败: {stats['failed']}")
        logger.info(f"总记录数: {stats['total_records']}")
        logger.info("=" * 60)

        if self.progress_data.get("failed_stocks"):
            failed = self.progress_data["failed_stocks"]
            logger.warning(f"失败股票 ({len(failed)}): {', '.join(failed[:10])}")
            if len(failed) > 10:
                logger.warning(f"... 还有 {len(failed) - 10} 只")


__all__ = ["ProgressTracker"]
