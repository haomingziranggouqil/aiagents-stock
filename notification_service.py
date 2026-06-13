"""兼容层：实际实现已移至 core/notification_service.py"""
from core.notification_service import *  # noqa: F401,F403
try:
    from core.notification_service import notification_service
except ImportError:
    pass
