"""兼容层：实际实现已移至 core/database.py"""
from core.database import *  # noqa: F401,F403
try:
    from core.database import db
except ImportError:
    pass
