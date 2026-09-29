# -*- coding: UTF-8 -*-
'''
告警 / 里程接口 queryType 验证工具（只读，不改任何文件）

背景：历史轨迹接口实测证明 15900000070 必须用 queryType=1（按设备ID）才能查到数据，
      但 alarm_report.py 里 4 个接口用的是 queryType=0（按设备名）。
      本脚本对同一接口分别用 0 和 1 各查一次，用返回的 msg/data 数量判断哪个才对。

⚠️ 只做诊断，不修改代码。确认结论后再决定是否统一修正。

用法：
    python tools/verify_query_type.py
'''
import os
import sys
import time
import json
import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from base.redConfig import Config

CALL_INTERVAL = 3  # 秒，这几个报表接口未标注限流，保守留点间隔即可

cfg = Config()
BASE_API_URL = cfg.base_api_url.rstrip("/")
HEADERS = dict(cfg.env_conf.get("common_headers") or {})

DEVICE = "15900000070"
DATE_FROM = "2026-09-18 00:00:00"
DATE_TO = "2026-09-18 23:59:59"


def post(endpoint_key, body):
    path = str(cfg.get_endpoint(endpoint_key)).lstrip("/")
    url = f"{BASE_API_URL}/{path}"
    r = requests.post(url, json=body, headers=HEADERS, timeout=30)
    try:
        return r.json(), url
    except Exception:
        return {"_raw": r.text[:300]}, url


def summarize(resp):
    code, msg = resp.get("code"), resp.get("msg")
    data = resp.get("data")
    if isinstance(data, list):
        n = len(data)
    elif isinstance(data, dict):
        n = len(data.get("list") or data.get("records") or []) or (1 if data else 0)
    else:
        n = 0
    return code, msg, n


# (接口名, endpoint key, 说明, 附加字段)
TARGETS = [
    ("告警信息", "alarm_info", "ids=[25]",
     lambda qt: {"ids": [25], "pageNumber": 1, "pageSize": 10,
                 "queryParams": [DEVICE], "queryType": qt,
                 "startTime": DATE_FROM, "endTime": DATE_TO}),
    ("AI事件信息", "ai_event_alarm_info", "ids=[206]",
     lambda qt: {"ids": [206], "pageNumber": 1, "pageSize": 10,
                 "queryParams": [DEVICE], "queryType": qt,
                 "startTime": DATE_FROM, "endTime": DATE_TO}),
    ("里程报表", "mileage_report", "无 ids",
     lambda qt: {"pageNumber": 1, "pageSize": 10,
                 "queryParams": [DEVICE], "queryType": qt,
                 "startTime": DATE_FROM, "endTime": DATE_TO}),
    ("停车报表", "parking_record", "无 ids",
     lambda qt: {"pageNumber": 0, "pageSize": 10,
                 "queryParams": [DEVICE], "queryType": qt,
                 "startTime": DATE_FROM, "endTime": DATE_TO}),
]


def main():
    print(f"设备: {DEVICE}   时间窗: {DATE_FROM} ~ {DATE_TO}")
    print("=" * 78)
    verdicts = []
    for name, key, note, builder in TARGETS:
        print(f"\n【{name}】endpoint={key}  ({note})")
        results = {}
        for qt in (0, 1):
            try:
                resp, url = post(key, builder(qt))
                code, msg, n = summarize(resp)
                results[qt] = (code, msg, n)
                flag = "✅ 有数据" if (code == 200 and n > 0) else "❌ 无数据"
                print(f"  queryType={qt} -> code={code} msg={msg} 记录数={n}  {flag}")
                if code != 200 or n == 0:
                    print(f"      响应片段: {json.dumps(resp, ensure_ascii=False)[:200]}")
            except Exception as e:
                results[qt] = ("ERR", str(e), 0)
                print(f"  queryType={qt} -> 请求异常: {e}")
            time.sleep(CALL_INTERVAL)

        r0, r1 = results.get(0), results.get(1)
        if r0 and r1:
            n0, n1 = r0[2], r1[2]
            if n1 > n0:
                verdicts.append((name, key, 1, f"queryType=1 记录更多({n1} vs {n0})"))
            elif n0 > n1:
                verdicts.append((name, key, 0, f"queryType=0 记录更多({n0} vs {n1})"))
            else:
                verdicts.append((name, key, None, f"两者相同({n0})，无法据此区分"))

    print("\n" + "=" * 78)
    print("结论：")
    for name, key, qt, why in verdicts:
        mark = {1: "应改为 queryType=1", 0: "保持 queryType=0", None: "无法判定"}[qt]
        print(f"  {name:12s} -> {mark:22s} ({why})")
    print("\n注意：本脚本只做诊断，未修改任何文件。")


if __name__ == "__main__":
    main()
