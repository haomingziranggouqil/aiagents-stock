"""
项目路径工具 - 统一管理数据库和资源文件路径
"""
import os

# 项目根目录 (aiagents-stock/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据库目录
DB_DIR = os.path.join(PROJECT_ROOT, "data_db")


def get_db_path(db_name: str) -> str:
    """获取数据库文件的完整路径"""
    return os.path.join(DB_DIR, db_name)
