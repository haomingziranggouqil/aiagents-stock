"""兼容层：实际实现已移至 services/miniqmt_interface.py"""
from services.miniqmt_interface import *  # noqa: F401,F403
try:
    from services.miniqmt_interface import miniqmt, get_miniqmt_status, QuantStrategyConfig
except ImportError:
    pass
