"""
登录会话 token：签名 + 过期时间，用于跨浏览器标签的cookie持久化登录。

token 形如 base64(payload).hmac_sig，payload 含用户名与过期时间戳。
签名密钥存于 data_db/session_secret.key（不进版本库），首次使用自动生成。
"""

import base64
import hmac
import hashlib
import json
import os
import secrets
import time

# token 默认有效期（秒）：7 天
DEFAULT_TTL = 7 * 24 * 3600


def _secret_path():
    from core.paths import get_db_path
    return get_db_path("session_secret.key")


def _load_secret():
    """加载签名密钥，不存在则生成一个并持久化。"""
    path = _secret_path()
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read().strip()
            if data:
                return data
    # 生成新密钥
    secret = secrets.token_bytes(32)
    db_dir = os.path.dirname(path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    with open(path, "wb") as f:
        f.write(secret)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass
    return secret


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def issue_token(username, ttl=DEFAULT_TTL):
    """为已登录用户签发 token。"""
    payload = {"u": username, "exp": int(time.time()) + ttl}
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = _b64encode(payload_bytes)
    sig = hmac.new(_load_secret(), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return f"{payload_b64}.{_b64encode(sig)}"


def verify_token(token):
    """校验 token，返回用户名；无效或过期返回 None。"""
    if not token or "." not in token:
        return None
    try:
        payload_b64, sig_b64 = token.split(".", 1)
        expected_sig = hmac.new(
            _load_secret(), payload_b64.encode("ascii"), hashlib.sha256
        ).digest()
        actual_sig = _b64decode(sig_b64)
        # 常量时间比较防时序攻击
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(_b64decode(payload_b64))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload.get("u")
    except Exception:
        return None
