"""
数据库初始化脚本

功能：
- 创建ClickHouse数据库和表结构
- 支持幂等操作（重复执行安全）
- 支持重置模式（--reset删除已有表）

使用方法：
    python scripts/init_db.py           # 初始化数据库
    python scripts/init_db.py --reset   # 重置数据库（删除并重建）
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logger import setup_logger, logger
from core.database import ClickHouseClient
from config.settings import settings


# 表结构定义
TABLES = {
    "stock_basic": """
        CREATE TABLE IF NOT EXISTS stock_basic (
            ts_code String COMMENT '股票代码',
            symbol String COMMENT '股票简称代码',
            name String COMMENT '股票名称',
            area String COMMENT '地域',
            industry String COMMENT '行业',
            market String COMMENT '市场类型（主板/创业板等）',
            list_date Date COMMENT '上市日期',
            update_time DateTime DEFAULT now() COMMENT '更新时间'
        ) ENGINE = ReplacingMergeTree(update_time)
        ORDER BY ts_code
        COMMENT '股票基础信息表'
    """,

    "stock_daily": """
        CREATE TABLE IF NOT EXISTS stock_daily (
            ts_code String COMMENT '股票代码',
            trade_date Date COMMENT '交易日期',
            open Int32 COMMENT '开盘价（×100）',
            high Int32 COMMENT '最高价（×100）',
            low Int32 COMMENT '最低价（×100）',
            close Int32 COMMENT '收盘价（×100）',
            pre_close Int32 COMMENT '昨收价（×100）',
            change Int32 COMMENT '涨跌额（×100）',
            pct_change Int32 COMMENT '涨跌幅（×10000，即百分比×100）',
            volume Int64 COMMENT '成交量（手）',
            amount Int64 COMMENT '成交额（元×100）',
            update_time DateTime DEFAULT now() COMMENT '更新时间'
        ) ENGINE = ReplacingMergeTree(update_time)
        PARTITION BY toYYYYMM(trade_date)
        ORDER BY (ts_code, trade_date)
        COMMENT '股票日线数据表'
    """,

    "stock_minute": """
        CREATE TABLE IF NOT EXISTS stock_minute (
            ts_code String COMMENT '股票代码',
            trade_time DateTime COMMENT '交易时间',
            open Int32 COMMENT '开盘价（×100）',
            high Int32 COMMENT '最高价（×100）',
            low Int32 COMMENT '最低价（×100）',
            close Int32 COMMENT '收盘价（×100）',
            volume Int64 COMMENT '成交量（手）',
            amount Int64 COMMENT '成交额（元×100）',
            update_time DateTime DEFAULT now() COMMENT '更新时间'
        ) ENGINE = ReplacingMergeTree(update_time)
        PARTITION BY toYYYYMMDD(trade_time)
        ORDER BY (ts_code, trade_time)
        COMMENT '股票分钟线数据表'
    """,
}


def create_database(client: ClickHouseClient) -> None:
    """
    创建数据库（如果不存在）

    Args:
        client: ClickHouse客户端实例
    """
    database = settings.clickhouse.database

    try:
        # 检查数据库是否存在
        result = client.execute(
            f"SELECT name FROM system.databases WHERE name = '{database}'"
        )

        if result.result_rows:
            logger.info(f"数据库 {database} 已存在")
        else:
            # 创建数据库
            client.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
            logger.info(f"✅ 成功创建数据库: {database}")

    except Exception as e:
        logger.error(f"创建数据库失败: {e}")
        raise


def drop_table(client: ClickHouseClient, table_name: str) -> None:
    """
    删除表

    Args:
        client: ClickHouse客户端实例
        table_name: 表名
    """
    try:
        client.execute(f"DROP TABLE IF EXISTS {table_name}")
        logger.info(f"✅ 成功删除表: {table_name}")
    except Exception as e:
        logger.error(f"删除表 {table_name} 失败: {e}")
        raise


def create_table(client: ClickHouseClient, table_name: str, table_sql: str) -> None:
    """
    创建表

    Args:
        client: ClickHouse客户端实例
        table_name: 表名
        table_sql: 建表SQL语句
    """
    try:
        # 检查表是否存在
        result = client.execute(
            f"SELECT name FROM system.tables "
            f"WHERE database = '{settings.clickhouse.database}' "
            f"AND name = '{table_name}'"
        )

        if result.result_rows:
            logger.info(f"表 {table_name} 已存在，跳过创建")
            return

        # 创建表
        client.execute(table_sql)
        logger.info(f"✅ 成功创建表: {table_name}")

        # 显示表结构
        result = client.execute(f"DESCRIBE TABLE {table_name}")
        logger.debug(f"表 {table_name} 结构:")
        for row in result.result_rows:
            logger.debug(f"  {row[0]}: {row[1]}")

    except Exception as e:
        logger.error(f"创建表 {table_name} 失败: {e}")
        raise


def verify_tables(client: ClickHouseClient) -> None:
    """
    验证表创建结果

    Args:
        client: ClickHouse客户端实例
    """
    try:
        logger.info("开始验证表结构...")

        # 获取所有表
        result = client.execute(
            f"SELECT name, engine, total_rows "
            f"FROM system.tables "
            f"WHERE database = '{settings.clickhouse.database}'"
        )

        if not result.result_rows:
            logger.warning("⚠️  未找到任何表")
            return

        logger.info(f"数据库 {settings.clickhouse.database} 中的表:")
        for row in result.result_rows:
            table_name, engine, total_rows = row
            logger.info(f"  - {table_name}: {engine} (行数: {total_rows})")

        # 验证分区配置
        logger.info("验证分区配置...")
        for table_name in TABLES.keys():
            result = client.execute(
                f"SELECT partition_key FROM system.tables "
                f"WHERE database = '{settings.clickhouse.database}' "
                f"AND name = '{table_name}'"
            )
            if result.result_rows:
                partition_key = result.result_rows[0][0]
                logger.info(f"  {table_name} 分区键: {partition_key}")

        logger.info("✅ 表结构验证完成")

    except Exception as e:
        logger.error(f"验证表结构失败: {e}")
        raise


def init_database(reset: bool = False) -> None:
    """
    初始化数据库

    Args:
        reset: 是否重置数据库（删除已有表）
    """
    logger.info("=" * 60)
    logger.info("开始初始化ClickHouse数据库")
    logger.info("=" * 60)

    if reset:
        logger.warning("⚠️  重置模式：将删除所有已有表")

    # 第1步：连接到default数据库创建a_share数据库
    logger.info("步骤1: 创建数据库...")
    default_client = ClickHouseClient(database="default")

    try:
        default_client.connect()
        create_database(default_client)
    except Exception as e:
        logger.error(f"❌ 创建数据库失败: {e}")
        sys.exit(1)
    finally:
        default_client.close()

    # 第2步：连接到a_share数据库创建表
    logger.info("步骤2: 创建表结构...")
    client = ClickHouseClient()

    try:
        client.connect()

        # 重置模式：删除所有表
        if reset:
            logger.info("删除已有表...")
            for table_name in TABLES.keys():
                drop_table(client, table_name)

        # 创建表
        logger.info("开始创建表...")
        for table_name, table_sql in TABLES.items():
            create_table(client, table_name, table_sql)

        # 验证结果
        verify_tables(client)

        logger.info("=" * 60)
        logger.info("✅ 数据库初始化完成")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)

    finally:
        client.close()


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="初始化ClickHouse数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/init_db.py           # 初始化数据库
  python scripts/init_db.py --reset   # 重置数据库
        """
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="重置数据库（删除已有表并重建）"
    )

    args = parser.parse_args()

    # 配置日志
    setup_logger()

    # 初始化数据库
    init_database(reset=args.reset)


if __name__ == "__main__":
    main()
