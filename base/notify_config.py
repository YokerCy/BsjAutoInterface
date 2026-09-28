# -*- coding: UTF-8 -*-
'''
加载「通知 / 报告」专用配置。

设计要点：
  1) 敏感值（企微 webhook / userid）一律放 conf/config.local.yaml，该文件已进 .gitignore；
  2) 非敏感策略配置放 conf/notify.yaml，可安全入库；
  3) 两者做深度合并，local 覆盖 notify（这样 local 里也能临时开关项）。
'''
import os
import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT = {
    "notify": {
        "enabled": True,
        "policy": "on_new_failure",
        "first_run_as_new": True,
        "mention_on_push": False,
        "mention_userids": [],
        "snapshot_path": "logs/last_result.json",
    },
    "report": {
        "generate": True,
        "output_dir": "./allure-report",
    },
    "wechat": {},
}


def _read_yaml(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _deep_merge(base, override):
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_notify_config():
    """读取 conf/notify.yaml 并用 conf/config.local.yaml 覆盖（后者含敏感值）。"""
    cfg = _deep_merge(DEFAULT, _read_yaml(os.path.join(PROJECT_ROOT, "conf", "notify.yaml")))
    cfg = _deep_merge(cfg, _read_yaml(os.path.join(PROJECT_ROOT, "conf", "config.local.yaml")))
    return cfg


def get_webhook(cfg=None):
    """取出 webhook；未配置或仍是占位值时返回空字符串。"""
    cfg = cfg or load_notify_config()
    url = ((cfg.get("wechat") or {}).get("webhook_url") or "").strip()
    # 过滤掉示例占位符，避免把占位地址当真配置去请求
    if ("把这里换成" in url) or ("your_key" in url) or (not url.startswith("http")):
        return ""
    return url
