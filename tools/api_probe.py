# -*- coding: UTF-8 -*-
"""
探测脚本的共用工具：登录 + 构造一个轻量 client。

为什么单独抽出来：
  tools/ 下的探测脚本都需要「登录拿 token，然后按 send_by_key 的规则发请求」，
  之前每个脚本各复制一份，已有 2 份重复。这里统一一处，后续新增接口探测直接复用。

注意：这里只是「探测用」的轻量实现，与 conftest.py 的正式 client 保持一致的
      请求规则（base_url + common_params 合并），但不含节流/重试/Allure 附件。
"""
import sys

import requests

sys.path.insert(0, ".")

from base.redConfig import Config


class ProbeClient:
    """探测用 client：复刻 conftest 里 send_by_key 的行为。"""

    def __init__(self, session, cfg, user_id=None):
        self.session = session
        self.config = cfg
        self.userId = user_id

    def send_by_key(self, method, endpoint_key, **kwargs):
        cfg = self.config
        url = cfg.base_url.rstrip("/") + "/" + cfg.get_endpoint(endpoint_key).lstrip("/")
        params = cfg.data["environments"][cfg.env]["common_params"].copy()
        if "params" in kwargs:
            params.update(kwargs.pop("params"))
        kwargs["params"] = params
        return self.session.request(method, url, **kwargs)


def make_client(cfg=None):
    """
    登录并返回 (ProbeClient, 登录返回的 data)。

    :param cfg: 可选，复用已有的 Config 实例
    """
    cfg = cfg or Config()
    env_conf = cfg.data["environments"][cfg.env]

    session = requests.Session()
    session.headers.update(env_conf["common_headers"])

    pwd = cfg.aes_encrypt_like_cryptojs_ecb(env_conf["accounts"]["admin"]["password"])
    res = session.post(
        cfg.base_url.rstrip("/") + "/user/login",
        json={
            "userName": env_conf["accounts"]["admin"]["username"],
            "password": pwd,
        },
    ).json()

    data = res.get("data") or {}
    session.headers.update({"token": data.get("sid")})

    print("== 登录 ==")
    print("  code:", res.get("code"), "| msg:", res.get("msg"))
    print("  userId:", data.get("userId"))

    return ProbeClient(session, cfg, user_id=data.get("userId")), data


def show(title, res_json, limit=1200):
    """打印一次响应，便于人工判断结构。"""
    print(f"\n== {title} ==")
    print("  code:", res_json.get("code"), "| msg:", res_json.get("msg"))
    d = res_json.get("data")
    print("  data 类型:", type(d).__name__)
    print("  data 内容:", __import__("json").dumps(d, ensure_ascii=False)[:limit])
