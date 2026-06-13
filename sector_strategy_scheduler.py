"""兼容层：实际实现已移至 modules/sector_strategy/scheduler.py"""
from modules.sector_strategy.scheduler import *  # noqa: F401,F403
try:
    from modules.sector_strategy.scheduler import sector_strategy_scheduler
except ImportError:
    pass
