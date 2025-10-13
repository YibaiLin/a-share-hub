"""
A-Share Hub 主程序入口

用途：启动任务调度器
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """主函数"""
    print("A-Share Hub")
    print("=" * 50)
    print("项目初始化完成！")
    print("下一步：Phase 2 - 配置管理模块")
    print("=" * 50)


if __name__ == "__main__":
    main()