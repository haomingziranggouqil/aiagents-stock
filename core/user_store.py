"""
用户凭证存储（独立SQLite数据库 + pbkdf2加盐哈希）

将登录账号从配置文件中分离，密码以哈希形式存储，文件泄露也看不到明文。
提供给登录校验（verify_user）与命令行管理脚本（增删改查）共用。
"""

import sqlite3
import hashlib
import os
import secrets
from datetime import datetime

# pbkdf2 参数
_ALGO = "sha256"
_ITERATIONS = 240000
_SALT_BYTES = 16


class UserStore:
    """用户凭证存储，密码使用 pbkdf2_hmac 加盐哈希。"""

    def __init__(self, db_path=None):
        if db_path is None:
            from core.paths import get_db_path
            db_path = get_db_path("users.db")
        self.db_path = db_path
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    @staticmethod
    def _hash_password(password, salt):
        """用给定salt（hex字符串）计算密码哈希，返回hex字符串。"""
        dk = hashlib.pbkdf2_hmac(
            _ALGO, password.encode("utf-8"), bytes.fromhex(salt), _ITERATIONS
        )
        return dk.hex()

    def add_user(self, username, password, overwrite=False):
        """新增用户。overwrite=False时若已存在则报错。"""
        username = (username or "").strip()
        if not username or not password:
            raise ValueError("用户名和密码不能为空")
        if not overwrite and self.user_exists(username):
            raise ValueError(f"用户已存在: {username}")

        salt = secrets.token_hex(_SALT_BYTES)
        pwd_hash = self._hash_password(password, salt)
        now = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO users (username, salt, password_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                salt=excluded.salt,
                password_hash=excluded.password_hash,
                updated_at=excluded.updated_at
        ''', (username, salt, pwd_hash, now, now))
        conn.commit()
        conn.close()

    def set_password(self, username, password):
        """修改已有用户的密码。"""
        if not self.user_exists(username):
            raise ValueError(f"用户不存在: {username}")
        self.add_user(username, password, overwrite=True)

    def delete_user(self, username):
        """删除用户，返回是否删除了记录。"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        deleted = cur.rowcount > 0
        conn.close()
        return deleted

    def user_exists(self, username):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        exists = cur.fetchone() is not None
        conn.close()
        return exists

    def list_users(self):
        """返回所有用户名列表（不含密码）。"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("SELECT username FROM users ORDER BY username")
        rows = [r[0] for r in cur.fetchall()]
        conn.close()
        return rows

    def count(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("SELECT COUNT(*) FROM users")
        n = cur.fetchone()[0]
        conn.close()
        return n

    def verify_user(self, username, password):
        """校验用户名+密码是否正确。使用常量时间比较防时序攻击。"""
        if not username or not password:
            return False
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "SELECT salt, password_hash FROM users WHERE username = ?", (username,)
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return False
        salt, stored_hash = row
        candidate = self._hash_password(password, salt)
        return secrets.compare_digest(candidate, stored_hash)


# 全局实例
user_store = UserStore()
