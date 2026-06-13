#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilities to launch a browser for PDF generation.
Adds optional Microsoft Edge support controlled via environment variables.
"""

import os
import shutil
from typing import Dict, Optional

EDGE_CANDIDATE_PATHS = [
    r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    "/usr/bin/microsoft-edge",
    "/usr/bin/microsoft-edge-stable",
    "/opt/microsoft/msedge/msedge",
]

CHROME_CANDIDATE_PATHS = [
    r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/google-chrome",
    "/opt/google/chrome/chrome",
]

EDGE_COMMANDS = ("msedge", "microsoft-edge", "microsoft-edge-stable")
CHROME_COMMANDS = ("google-chrome-stable", "google-chrome", "chrome")


def _strip_quotes(path: str) -> str:
    path = path.strip()
    if (path.startswith("\"") and path.endswith("\"")) or (path.startswith("'") and path.endswith("'")):
        path = path[1:-1]
    return path


def _get_custom_browser_path() -> Optional[str]:
    raw_path = os.getenv("PDF_BROWSER_PATH") or os.getenv("EDGE_BROWSER_PATH")
    if not raw_path:
        return None
    browser_path = _strip_quotes(raw_path)
    if os.path.exists(browser_path):
        return browser_path
    print(f"[PDF] PDF_BROWSER_PATH/EDGE_BROWSER_PATH not found: {browser_path}")
    return None


def _find_edge_path() -> Optional[str]:
    candidates = EDGE_CANDIDATE_PATHS + [shutil.which(cmd) for cmd in EDGE_COMMANDS]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def _find_chrome_path() -> Optional[str]:
    candidates = CHROME_CANDIDATE_PATHS + [shutil.which(cmd) for cmd in CHROME_COMMANDS]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def resolve_browser_executable() -> Optional[str]:
    """
    Resolve which browser executable to use for pyppeteer launch.
    Priority:
    1) Explicit PDF_BROWSER_PATH/EDGE_BROWSER_PATH
    2) If PDF_BROWSER=edge/msedge, try Edge then Chrome
    3) If PDF_BROWSER=chrome, try Chrome then Edge
    4) If PDF_BROWSER=auto, try Edge, then Chrome
    5) Fallback to pyppeteer's bundled Chromium
    """
    custom_path = _get_custom_browser_path()
    if custom_path:
        print(f"[PDF] Using custom browser for PDF generation: {custom_path}")
        return custom_path

    browser_choice = (os.getenv("PDF_BROWSER") or "auto").strip().lower()
    edge_path = _find_edge_path()
    chrome_path = _find_chrome_path()

    if browser_choice in ("edge", "msedge"):
        if edge_path:
            print(f"[PDF] Using Microsoft Edge for PDF generation: {edge_path}")
            return edge_path
        if chrome_path:
            print("[PDF] Edge not found; falling back to Google Chrome for PDF generation")
            return chrome_path
        print("[PDF] Edge/Chrome not found; falling back to bundled Chromium")
        return None

    if browser_choice == "chrome":
        if chrome_path:
            print(f"[PDF] Using Google Chrome for PDF generation: {chrome_path}")
            return chrome_path
        if edge_path:
            print("[PDF] Chrome not found; falling back to Microsoft Edge for PDF generation")
            return edge_path
        print("[PDF] Chrome/Edge not found; falling back to bundled Chromium")
        return None

    # auto模式：先Edge后Chrome
    if edge_path:
        print(f"[PDF] Auto-detected Microsoft Edge for PDF generation: {edge_path}")
        return edge_path
    if chrome_path:
        print(f"[PDF] Auto-detected Google Chrome for PDF generation: {chrome_path}")
        return chrome_path

    return None


def get_browser_launch_options() -> Dict[str, object]:
    """Build pyppeteer launch options with optional Edge support."""
    launch_options: Dict[str, object] = {
        "headless": True,
        "handleSIGINT": False,
        "handleSIGTERM": False,
        "handleSIGHUP": False,
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--window-size=1920,1080",
        ],
    }

    executable = resolve_browser_executable()
    if executable:
        launch_options["executablePath"] = executable

    return launch_options

