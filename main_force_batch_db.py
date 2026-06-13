"""兼容层：实际实现已移至 modules/main_force/batch_db.py"""
from modules.main_force.batch_db import *  # noqa: F401,F403
try:
    from modules.main_force.batch_db import batch_db
except ImportError:
    pass
