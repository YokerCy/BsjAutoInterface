# -*- coding: UTF-8 -*-
'''
历史轨迹接口「No Data」自助排查工具

背景：/track/getTrackList 返回 code=200 但 msg="No Data"，
      表示请求已被正常接受，只是按当前查询条件没查到记录 ——
      是查询条件不匹配，不是接口挂了。最典型的就是 queryType 用错。

⚠️ 限流：文档明确该接口单用户每分钟最多调用 2 次，超限会触发限流，
      一旦被限流，返回的结果也不可信。因此每次调用之间强制间隔 35 秒，请勿调小。

用法：
    python tools/diagnose_trajectory.py                # 默认排查 15900000070
    python tools/diagnose_trajectory.py 13342746312    # 指定设备号
'''
import os
import sys
import time
import json
import requests
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from base.redConfig import Config

CALL_INTERVAL = 35  # 秒，遵守接口「2 次/分钟」的限流要求

cfg = Config()
ENDPOINT = cfg.get_endpoint("historical_trajectory")


def build_base_api_url():
    """
    历史轨迹文档给的示例是 https://y.gpstracktech.com/api/track/getTrackList。
    config 里的 base_api_url 末尾是 '/api/'，拼接时**必须去掉末尾斜杠**，
    否则会拼出 '.../api//track/getTrackList'（双斜杠），部分网关会判定为非法路径。
    """
    return cfg.base_api_url.rstrip("/")


BASE_API_URL = build_base_api_url()
HEADERS = {
    "key": (cfg.env_conf.get("common_headers") or {}).get("key", ""),
    "version": "1.0",
    "Accept-Language": "en",
    "Content-Type": "application/json",
}


def _today():
    d = datetime.now().strftime("%Y-%m-%d")
    return f"{d} 00:00:00", f"{d} 23:59:59"


def _last_days(days=7):
    now = datetime.now()
    return (now - timedelta(days=days - 1)).strftime("%Y-%m-%d 00:00:00"), now.strftime("%Y-%m-%d %H:%M:%S")


def build_cases():
    """
    实测已知信息（2026-09-28 用户确认）：
      - 数据确在 ytest 测试环境，且今天(2026-09-28)确实有数据；
      - 设备名在界面上就显示为 "15900000070"，因此 queryType=0(按设备名) 是对的。
    但仍返回 No Data，故把嫌疑收敛到「时间格式 / 过滤参数」这几个变量上。
    """
    t = _today()
    w = _last_days(7)
    return [
        # 说明, 参数
        ("A 基准：设备名 + 今天 + 文档原样参数",
         dict(queryType=0, begin=t[0], end=t[1], stopStatus=0, posStatus=0, filterTime=0)),
        ("B 设备名 + 今天 + posStatus=1(含未定位)",
         dict(queryType=0, begin=t[0], end=t[1], stopStatus=0, posStatus=1, filterTime=0)),
        ("C 设备名 + 今天 + stopStatus=1(不过滤停车)",
         dict(queryType=0, begin=t[0], end=t[1], stopStatus=1, posStatus=0, filterTime=1)),
        ("D 设备名 + 今天 + 时间只到秒的完整格式(原样)",
         dict(queryType=0, begin=t[0], end=t[1], stopStatus=0, posStatus=0, filterTime=60)),
        ("E 设备名 + 最近7天(全量兜底)",
         dict(queryType=0, begin=w[0], end=w[1], stopStatus=0, posStatus=1, filterTime=0)),
    ]


def call(device, case):
    params = {
        "filterTime": case["filterTime"],
        "stopStatus": case["stopStatus"],
        "posStatus": case["posStatus"],
        "queryType": case["queryType"],
        "queryParam": device,
        "beginTime": case["begin"],
        "endTime": case["end"],
    }
    url = f"{BASE_API_URL}/{ENDPOINT.lstrip('/')}"
    r = requests.get(url, params=params, headers=HEADERS, timeout=30)
    return r.json(), r.url


def main():
    device = sys.argv[1] if len(sys.argv) > 1 else "15900000070"
    cases = build_cases()

    print(f"排查设备: {device}  (界面上显示的设备名)")
    print(f"接口地址: {BASE_API_URL}{ENDPOINT}")
    print(f"限流提示: 该接口 2 次/分钟，每次调用间隔 {CALL_INTERVAL}s，全程约 {len(cases) * CALL_INTERVAL // 60} 分钟")
    print("=" * 80)

    # 记录整体信号：若所有组合都不带 baseInfo，说明是「设备压根没被识别」，
    # 而不是「设备识别到了但没有轨迹数据」——这两种情况的排查方向完全不同。
    any_base_info = False

    for idx, (name, case) in enumerate(cases):
        try:
            data, url = call(device, case)
        except Exception as e:
            print(f"[{name}] 请求异常: {e}")
            time.sleep(CALL_INTERVAL)
            continue

        code = data.get("code")
        msg = data.get("msg")
        d = data.get("data") or {}
        base_info = d.get("baseInfo") or {}
        track_list = d.get("trackList") or []
        if base_info:
            any_base_info = True

        ok = (code == 200 and msg == "Success" and track_list)
        print(f"[{name}] {'✅ 有数据' if ok else '❌ 无数据'}")
        print(f"    code={code} msg={msg} 轨迹点数={len(track_list)} trackTotal={d.get('trackTotal')}")
        if base_info:
            print(f"    命中设备 -> plate(设备名)={base_info.get('plate')} "
                  f"| terminalNo(设备ID)={base_info.get('terminalNo')} "
                  f"| expiredFlag={base_info.get('expiredFlag')}(0正常/1过期)")
        else:
            print("    ⚠️ 响应未返回 baseInfo -> 服务端并未识别到该设备")
        print(f"    URL: {url}")

        if ok:
            print("\n🎉 找到可用组合！把下面的值填进 conf/historical_trajectory_expect.yaml 的 payload：")
            print(f"    query_type: {case['queryType']}")
            print(f"    stop_status: {case['stopStatus']}")
            print(f"    pos_status: {case['posStatus']}")
            print(f"    filter_time: {case['filterTime']}")
            print(f"    begin_time: \"{case['begin']}\"")
            print(f"    end_time: \"{case['end']}\"")
            return

        if idx < len(cases) - 1:
            print(f"    (等待 {CALL_INTERVAL}s 避开限流...)")
            time.sleep(CALL_INTERVAL)

    print("\n" + "=" * 80)
    if not any_base_info:
        print("结论：【所有组合都没返回 baseInfo】—— 服务端始终没识别到这台设备。")
        print("  请重点核对（按可能性排序）：")
        print("  1) key 的数据权限范围：该 key 是 e8 开头（疑似亚洲区账号），")
        print("     确认它对 15900000070 这台设备有权限 —— 换个有权限的设备名再试。")
        print("  2) 设备名是否含隐藏字符/空格：把界面上显示的名字原样复制，别手敲。")
        print("  3) 该设备是否已被删除/停用。")
        print("  4) 换一台确定有轨迹的设备验证接口本身是否正常。")
    else:
        print("结论：【设备能被识别到(返回了 baseInfo)，但轨迹列表为空】——")
        print("  说明设备存在但所选时间窗内确实无轨迹上报，请缩小/调整时间范围，")
        print("  或用本脚本直接带上起止时间试（改 build_cases 里的时间窗）。")


if __name__ == "__main__":
    main()
