"""兼容层：实际实现已移至 modules/portfolio/manager.py"""
from modules.portfolio.manager import *  # noqa: F401,F403
try:
    from modules.portfolio.manager import portfolio_manager
except ImportError:
    pass
