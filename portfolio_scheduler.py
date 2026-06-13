"""兼容层：实际实现已移至 modules/portfolio/scheduler.py"""
from modules.portfolio.scheduler import *  # noqa: F401,F403
try:
    from modules.portfolio.scheduler import portfolio_scheduler
except ImportError:
    pass
