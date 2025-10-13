"""
pytest配置文件

定义全局fixtures和配置
"""
import pytest
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def project_root_dir():
    """项目根目录"""
    return project_root


@pytest.fixture
def test_data_dir():
    """测试数据目录"""
    return project_root / "tests" / "data"