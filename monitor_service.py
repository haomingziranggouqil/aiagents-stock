"""兼容层：实际实现已移至 modules/monitor/service.py"""
from modules.monitor.service import *  # noqa: F401,F403
try:
    from modules.monitor.service import monitor_service
except ImportError:
    pass
