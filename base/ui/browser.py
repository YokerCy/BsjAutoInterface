# -*- coding: UTF-8 -*-
"""
UI 层基础设施。

只做四件事，不含任何业务断言：
  1. 读 conf/ui.yaml
  2. 判断登录态快照是否还能复用
  3. 解析浏览器渠道（chrome -> msedge -> 自带 chromium）
  4. 用统一参数构建 browser context（超时、视口、下载、UA）

业务页面对象放 ui/pages，业务流程放 ui/flows。
"""
import os
import time
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UI_CONF_PATH = PROJECT_ROOT / "conf" / "ui.yaml"

# 各渠道的常见安装位置（含用户级安装：Chrome 装到 %LOCALAPPDATA% 的情况很常见，
# 只查 Program Files 会漏掉，这里必须覆盖）
_CHANNEL_PATHS = {
    "chrome": [
        r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
        r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
        r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
    ],
    "msedge": [
        r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
        r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
        r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe",
    ],
}


def load_ui_config():
    """读取 UI 配置。缺文件直接失败——静默降级会让问题藏到用例里。"""
    if not UI_CONF_PATH.exists():
        raise FileNotFoundError(f"未找到 UI 配置文件: {UI_CONF_PATH}")
    with open(UI_CONF_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def state_path(cfg):
    """登录态快照的绝对路径。"""
    p = Path(cfg["state_file"])
    return p if p.is_absolute() else PROJECT_ROOT / p


def state_is_fresh(cfg):
    """登录态是否存在且未过期。过期就重登，别拿隔夜 token 去撞 401。"""
    p = state_path(cfg)
    if not p.exists() or p.stat().st_size < 50:
        return False
    ttl_seconds = float(cfg.get("state_ttl_hours", 12)) * 3600
    return (time.time() - p.stat().st_mtime) < ttl_seconds


def artifact_dir(cfg):
    """失败留证目录。"""
    p = Path(cfg.get("artifact_dir", "logs/ui_artifacts"))
    p = p if p.is_absolute() else PROJECT_ROOT / p
    p.mkdir(parents=True, exist_ok=True)
    return p


def _channel_installed(channel: str) -> bool:
    """
    判断某个浏览器渠道是否已安装。

    只查路径不启动进程——启动探测要多花 1~2 秒，而且 headless 启动本身也可能被
    环境策略拦。先看注册表（Windows 标准登记位），再退化为查常见路径。
    """
    try:
        import winreg

        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                key = winreg.OpenKey(
                    root, rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{channel}.exe"
                )
                path, _ = winreg.QueryValueEx(key, "")
                winreg.CloseKey(key)
                if path and os.path.exists(path.strip('"')):
                    return True
            except OSError:
                continue
    except ImportError:
        pass

    for raw in _CHANNEL_PATHS.get(channel, []):
        if os.path.exists(os.path.expandvars(raw)):
            return True
    return False


def resolve_channel(cfg):
    """
    按 ui.yaml 的 browser 段选渠道：首选 -> 回退列表 -> None（用自带 chromium）。

    返回 None 表示所有渠道都不可用，交给 Playwright 用自带内核
    （此时必须已执行过 playwright install chromium，否则启动会报错并提示）。
    """
    bcfg = cfg.get("browser") or {}
    preferred = bcfg.get("channel")
    candidates = ([preferred] if preferred else []) + list(bcfg.get("fallback_channels") or [])

    for ch in candidates:
        if _channel_installed(ch):
            return ch
    return None


def _masked_user_agent(browser):
    """
    构造去掉 Headless 标记的桌面 Chrome UA。

    Playwright 无头模式的 UA 带 "HeadlessChrome"，某些前端环境判断或风控会据此
    走不同分支，导致"自动化跑出来的和用户看到的不一样"。用真实版本号拼一个即可。
    """
    try:
        version = str(browser.version)
        major = version.split(".")[0]
    except Exception:
        return None
    return (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{major}.0.0.0 Safari/537.36"
    )


def build_context(browser, cfg, storage_state=None):
    """
    统一构建 context。所有用例的浏览器环境必须从这里出，
    否则超时/视口/下载/UA 各不相同，用例之间无法互相复现。
    """
    bcfg = cfg.get("browser") or {}
    kwargs = {
        "base_url": cfg["base_url"],
        "viewport": cfg.get("viewport") or {"width": 1600, "height": 900},
        "ignore_https_errors": True,
        "accept_downloads": True,
        "locale": "zh-CN",
    }

    if bcfg.get("mask_headless_ua", True):
        ua = _masked_user_agent(browser)
        if ua:
            kwargs["user_agent"] = ua

    if storage_state:
        kwargs["storage_state"] = str(storage_state)

    context = browser.new_context(**kwargs)
    t = cfg.get("timeouts") or {}
    context.set_default_timeout(t.get("default", 15000))
    context.set_default_navigation_timeout(t.get("navigation", 30000))
    return context
