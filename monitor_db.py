"""兼容层：实际实现已移至 modules/monitor/db.py"""
from modules.monitor.db import *  # noqa: F401,F403
try:
    from modules.monitor.db import monitor_db
except ImportError:
    pass
