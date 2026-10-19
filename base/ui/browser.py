# -*- coding: UTF-8 -*-
"""
UI 层基础设施。

只做三件事，不含任何业务断言：
  1. 读 conf/ui.yaml
  2. 判断登录态快照是否还能复用
  3. 用统一参数构建 browser context（超时、视口、下载、trace）

业务页面对象放 ui/pages，业务流程放 ui/flows。
"""
import os
import time
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UI_CONF_PATH = PROJECT_ROOT / "conf" / "ui.yaml"


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


def build_context(browser, cfg, storage_state=None):
    """
    统一构建 context。所有用例的浏览器环境必须从这里出，
    否则超时/视口/下载行为各不相同，用例之间无法互相复现。
    """
    kwargs = {
        "base_url": cfg["base_url"],
        "viewport": cfg.get("viewport") or {"width": 1600, "height": 900},
        "ignore_https_errors": True,
        "accept_downloads": True,
        "locale": "zh-CN",
    }
    if storage_state:
        kwargs["storage_state"] = str(storage_state)

    context = browser.new_context(**kwargs)
    t = cfg.get("timeouts") or {}
    context.set_default_timeout(t.get("default", 15000))
    context.set_default_navigation_timeout(t.get("navigation", 30000))
    return context
