"""兼容层：实际实现已移至 modules/main_force/selector.py"""
from modules.main_force.selector import *  # noqa: F401,F403
try:
    from modules.main_force.selector import main_force_selector
except ImportError:
    pass
