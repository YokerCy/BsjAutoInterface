# -*- coding: UTF-8 -*-
"""
探测 /tempHumidityReport/getTempHumidityReport（温湿度报表）的真实返回结构。
只读诊断，不改任何文件。

目的（决定断言怎么写）：
  1) 拿到 data 的真实字段，用于「有意义的」契约断言（避免只比状态码的假绿）
  2) 确认「有空数据」与「无数据」在响应里如何区分（假绿陷阱排查）
  3) 确认无效 vehicleId 的行为（返回 200 还是 500）
  4) 确认分页字段名与行为
"""
import sys
import time

sys.path.insert(0, ".")

from tools.api_probe import make_client, show
from profes.temp_humidity_report import TempHumidityReport


def main():
    client, _ = make_client()
    api = TempHumidityReport(client)

    # ---- 探测 1：按抓包原样请求 ----
    r1 = api.get_temp_humidity_report(
        vehicle_ids=[89641],
        start_time="2026-10-16 00:00:00",
        end_time="2026-10-16 23:59:59",
        page_num=1,
        page_size=20,
    )
    show("探测1 正常（10-16 全天）", r1)

    time.sleep(3)

    # ---- 探测 2：空时间窗（昨天）—— 判断无数据时的返回 ----
    r2 = api.get_temp_humidity_report(
        vehicle_ids=[89641],
        start_time="2026-10-15 00:00:00",
        end_time="2026-10-15 23:59:59",
        page_num=1,
        page_size=20,
    )
    show("探测2 空窗口（10-15 全天）", r2)

    time.sleep(3)

    # ---- 探测 3：无效车辆 ----
    r3 = api.get_temp_humidity_report(
        vehicle_ids=[99999999],
        start_time="2026-10-16 00:00:00",
        end_time="2026-10-16 23:59:59",
        page_num=1,
        page_size=20,
    )
    show("探测3 无效车辆 99999999", r3)

    time.sleep(3)

    # ---- 探测 4：分页 pageNum=2 ----
    r4 = api.get_temp_humidity_report(
        vehicle_ids=[89641],
        start_time="2026-10-16 00:00:00",
        end_time="2026-10-16 23:59:59",
        page_num=2,
        page_size=20,
    )
    show("探测4 pageNum=2", r4)


if __name__ == "__main__":
    main()
