"""兼容层：实际实现已移至 core/config_manager.py"""
from core.config_manager import *  # noqa: F401,F403
# 保持单例导出
try:
    from core.config_manager import config_manager
except ImportError:
    pass
