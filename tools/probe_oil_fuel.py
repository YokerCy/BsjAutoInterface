# -*- coding: UTF-8 -*-
"""
探测 /oil/vehicleFuel（价格单车油耗分析表）的真实返回结构。
只读诊断，不改任何文件。

目的：
  1) 拿到 data 的真实字段，用于写「有意义的」契约断言（避免只比状态码的假绿）
  2) 确认登录返回的 userId 是否就是抓包里的 241
  3) 确认 clientTime 是否被服务端校验
"""
import sys
import json
import time

sys.path.insert(0, ".")

import requests
from base.redConfig import Config
from profes.oil_report import OilReport


def build_client(cfg):
    """复刻 conftest 的登录流程，拿到带 token 的 session。"""
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
    print("== 登录返回 ==")
    print("  code:", res.get("code"), "| msg:", res.get("msg"))
    data = res.get("data") or {}
    print("  userId:", data.get("userId"), "| sid:", str(data.get("sid"))[:12], "...")
    session.headers.update({"token": data.get("sid")})

    class Client:
        def __init__(self, session, cfg):
            self.session = session
            self.config = cfg

        def send_by_key(self, method, endpoint_key, **kwargs):
            url = (
                cfg.base_url.rstrip("/")
                + "/"
                + cfg.get_endpoint(endpoint_key).lstrip("/")
            )
            params = cfg.data["environments"][cfg.env]["common_params"].copy()
            if "params" in kwargs:
                params.update(kwargs.pop("params"))
            kwargs["params"] = params
            return self.session.request(method, url, **kwargs)

    return Client(session, cfg), data.get("userId")


def show(title, res_json):
    print(f"\n== {title} ==")
    print("  code:", res_json.get("code"), "| msg:", res_json.get("msg"))
    d = res_json.get("data")
    print("  data 类型:", type(d).__name__)
    print("  data 内容:", json.dumps(d, ensure_ascii=False)[:1200])


def main():
    cfg = Config()
    client, login_user_id = build_client(cfg)
    api = OilReport(client)

    # ---- 探测 1：完全按抓包参数请求 ----
    r1 = api.get_vehicle_fuel(
        user_id=241,
        vehicle_id=89641,
        start_time="2026-10-16 00:00:00",
        end_time="2026-10-16 23:59:59",
        unit_price=1,
        client_time="2026-10-16 16:19:29",
    )
    show("探测1 按抓包原样", r1)

    time.sleep(5)

    # ---- 探测 2：clientTime 用当前时间（验证是否被校验） ----
    r2 = api.get_vehicle_fuel(
        user_id=241,
        vehicle_id=89641,
        start_time="2026-10-16 00:00:00",
        end_time="2026-10-16 23:59:59",
        unit_price=1,
        # client_time 不传 -> 走默认当前时间
    )
    show("探测2 clientTime=当前时间", r2)

    time.sleep(5)

    # ---- 探测 3：换一个不存在的 vehicleId（验证是否假绿陷阱） ----
    r3 = api.get_vehicle_fuel(
        user_id=241,
        vehicle_id=99999999,
        start_time="2026-10-16 00:00:00",
        end_time="2026-10-16 23:59:59",
        unit_price=1,
        client_time="2026-10-16 16:19:29",
    )
    show("探测3 无效 vehicleId", r3)

    print("\n== 登录 userId ==", login_user_id, "（抓包里传的是 241）")


if __name__ == "__main__":
    main()
