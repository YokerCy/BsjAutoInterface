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
        "policy": "always",
        "first_run_as_new": True,
        "mention_on_push": False,
        "mention_userids": [],
        "snapshot_path": "logs/last_result.json",
    },
    "report": {
        "mode": "serve",        # serve / generate / none
        "serve_port": 0,
        "open_browser": True,
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


def validate_webhook(url):
    """
    校验企微 webhook 地址格式，返回 (是否合法, 问题描述)。

    常见错误：把整条 webhook 地址又粘到了 key= 后面
    （表现为 key 的值以 http 开头且长度很长），
    此时请求会返回 errcode=93000 invalid webhook url，
    但 HTTP 状态码仍是 200 —— 极易被误判成「发送成功」。
    """
    if not url:
        return False, "webhook 未配置"

    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(url)
    if parsed.netloc != "qyapi.weixin.qq.com":
        return False, f"域名应为 qyapi.weixin.qq.com，实际为 {parsed.netloc or '(空)'}"
    if "/cgi-bin/webhook/send" not in parsed.path:
        return False, f"路径应为 /cgi-bin/webhook/send，实际为 {parsed.path or '(空)'}"

    qs = parse_qs(parsed.query)
    key = (qs.get("key") or [""])[0]
    if not key:
        return False, "缺少 key 参数"
    if key.startswith("http"):
        return False, (
            "key 的值看起来是整条 URL —— 你可能把完整的 webhook 地址粘到了 key= 后面。"
            "key 应只是那段 32 位左右的字符串（形如 693a91f6-xxxx-xxxx-xxxx-xxxxxxxxxxxx）"
        )
    if len(key) > 64:
        return False, f"key 长度异常（{len(key)} 位），企微机器人 key 通常为 32 位左右"

    return True, "OK"
