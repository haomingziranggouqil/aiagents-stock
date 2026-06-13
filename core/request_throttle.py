"""
统一请求限速与重试机制

对 requests 库的 get/post 进行全局包装，实现：
1. 东方财富域名请求自动限速（默认间隔 1.5 秒）
2. 失败自动重试（指数退避，最多 3 次）
3. 不影响非东方财富的请求（如 DeepSeek API）

在程序入口处 import 本模块即可生效。

@File: core/request_throttle.py
@Contains: [install, _throttled_request]
@Responsibilities:
    - 对东方财富相关域名做请求限速
    - 对 ConnectionError/RemoteDisconnected 做自动重试
@Non-Responsibilities:
    - 不负责具体数据解析
    - 不修改请求参数或响应内容
@Input: requests.get/post 的原始调用
@Output: 限速+重试后的原始 Response 对象
"""

import time
import threading
import logging
from functools import wraps
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ============ 配置 ============

# 需要限速的域名关键词
THROTTLE_DOMAINS = [
    "eastmoney.com",
    "push2.eastmoney.com",
    "push2his.eastmoney.com",
    "datacenter-web.eastmoney.com",
]

# 请求最小间隔（秒）
MIN_INTERVAL = 1.5

# 重试配置
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0  # 首次重试等待秒数，后续指数增长

# ============ 内部状态 ============

_lock = threading.Lock()
_last_request_time = 0.0
_installed = False


def _should_throttle(url: str) -> bool:
    """判断该 URL 是否需要限速"""
    if not url:
        return False
    try:
        host = urlparse(url).hostname or ""
        return any(domain in host for domain in THROTTLE_DOMAINS)
    except Exception:
        return False


def _wait_for_throttle():
    """等待直到满足最小间隔"""
    global _last_request_time
    with _lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < MIN_INTERVAL:
            wait_time = MIN_INTERVAL - elapsed
            time.sleep(wait_time)
        _last_request_time = time.time()


def _make_throttled_request(original_func, *args, **kwargs):
    """带限速和重试的请求执行"""
    # 获取URL
    url = args[0] if args else kwargs.get("url", "")
    needs_throttle = _should_throttle(url)

    last_exception = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            if needs_throttle:
                _wait_for_throttle()
            response = original_func(*args, **kwargs)
            return response
        except Exception as e:
            last_exception = e
            error_name = type(e).__name__

            # 只对连接类错误重试
            retriable = any(keyword in error_name or keyword in str(e) for keyword in [
                "ConnectionError", "RemoteDisconnected", "ConnectionReset",
                "ConnectionAborted", "Timeout", "ReadTimeout",
            ])

            if not retriable or attempt >= MAX_RETRIES:
                raise

            delay = RETRY_BASE_DELAY * (2 ** attempt)
            logger.info(
                f"[限速重试] {error_name} on {urlparse(url).hostname}, "
                f"第 {attempt + 1}/{MAX_RETRIES} 次重试，等待 {delay:.1f}s"
            )
            time.sleep(delay)

    raise last_exception


def install():
    """
    安装全局请求限速。在程序入口调用一次即可。
    对 requests.get 和 requests.post 进行包装。
    """
    global _installed
    if _installed:
        return

    import requests

    _original_get = requests.get
    _original_post = requests.post

    @wraps(_original_get)
    def throttled_get(*args, **kwargs):
        return _make_throttled_request(_original_get, *args, **kwargs)

    @wraps(_original_post)
    def throttled_post(*args, **kwargs):
        return _make_throttled_request(_original_post, *args, **kwargs)

    requests.get = throttled_get
    requests.post = throttled_post

    _installed = True
    print("[请求限速] ✅ 已启用全局请求限速（东方财富域名间隔1.5s，失败自动重试3次）")
