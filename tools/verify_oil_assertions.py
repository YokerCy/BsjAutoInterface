# -*- coding: UTF-8 -*-
"""
离线验证油耗分析表用例的断言逻辑（不依赖网络）。

用 tools/probe_oil_fuel.py 实际捕获到的响应作为输入，
确认断言「既不会恒真（假绿），也不会误伤正常响应」。
"""
import copy
import sys

sys.path.insert(0, ".")

from test_case.test_oil_report import verify_fuel_response

# ---- 真实捕获的响应：有数据（2026-10-16） ----
RESP_WITH_DATA = {
    "code": 200, "msg": "Success",
    "data": {
        "addCount": 0, "reduceCount": 0,
        "data": [
            {"time": "2026-10-16 16:14:01", "speed": 90.0,
             "data": {"1": {"value": 15.0, "actionType": 0, "actionValue": 0.0,
                            "liquidLevel": 0, "percent": 15, "voltage": 0.0}}},
            {"time": "2026-10-16 16:14:54", "speed": 90.0,
             "data": {"1": {"value": 15.0, "actionType": 0, "actionValue": 0.0,
                            "liquidLevel": 0, "percent": 15, "voltage": 0.0}}},
        ],
        "fuel": 0.0, "mileage": 0.0, "fuelKilometers": 0.0,
        "fuelCost": 0.0, "channelIds": [1],
    },
}

# ---- 真实捕获的响应：无数据（2026-10-15） ----
RESP_NO_DATA = {
    "code": 200, "msg": "Success",
    "data": {
        "addCount": 0, "reduceCount": 0, "data": [],
        "fuel": 0.0, "mileage": 0.0, "fuelKilometers": 0.0,
        "fuelCost": 0.0, "channelIds": None,
    },
}

BASE_CASE = {
    "case_name": "获取价格单车油耗分析表",
    "expect_code": 200,
    "expect_msg": "Success",
    "require_data": True,
    "payload": {
        "vehicle_id": 89641,
        "start_time": "2026-10-16 00:00:00",
        "end_time": "2026-10-16 23:59:59",
    },
}


def run(title, resp, expect_pass, case=None):
    case = case or BASE_CASE
    try:
        verify_fuel_response(copy.deepcopy(resp), case)
        ok = True
        detail = ""
    except AssertionError as e:
        ok = False
        detail = str(e).split("\n")[0][:110]

    mark = "✅" if ok == expect_pass else "❌ 与预期不符"
    print(f"{mark} {title}")
    print(f"     预期 {'通过' if expect_pass else '失败'} / 实际 {'通过' if ok else '失败'}")
    if detail:
        print(f"     断言信息: {detail}")
    return ok == expect_pass


def main():
    print("=" * 78)
    print("离线验证断言逻辑（输入为真实捕获的响应）")
    print("=" * 78)
    results = []

    # 1) 有数据 + require_data=true -> 应通过
    results.append(run("有数据(10-16) + require_data=true", RESP_WITH_DATA, True))

    # 2) 无数据 + require_data=true -> 应失败（证明断言有牙齿，能拦住假绿）
    results.append(run("无数据(10-15) + require_data=true", RESP_NO_DATA, False))

    # 3) 无数据 + require_data=false -> 应通过（证明开关有效）
    case_nodata = copy.deepcopy(BASE_CASE)
    case_nodata["require_data"] = False
    results.append(run("无数据(10-15) + require_data=false", RESP_NO_DATA, True, case_nodata))

    # 4) 曲线点时间越界 -> 应失败（证明时间过滤断言有效）
    resp_out = copy.deepcopy(RESP_WITH_DATA)
    resp_out["data"]["data"][0]["time"] = "2026-10-20 08:00:00"
    results.append(run("曲线点时间越界", resp_out, False))

    # 5) 缺少指标字段 -> 应失败
    resp_missing = copy.deepcopy(RESP_WITH_DATA)
    del resp_missing["data"]["fuelCost"]
    results.append(run("缺少 fuelCost 字段", resp_missing, False))

    # 6) 曲线点缺少 time 字段 -> 应失败
    resp_pt = copy.deepcopy(RESP_WITH_DATA)
    del resp_pt["data"]["data"][1]["speed"]
    results.append(run("曲线点缺少 speed 字段", resp_pt, False))

    # 7) 返回码错误 -> 应失败
    resp_500 = {"code": 500, "msg": "There was a slight error, please try again later!!!", "data": None}
    results.append(run("返回码 500（无效车辆实测返回）", resp_500, False))

    print("=" * 78)
    print(f"通过 {sum(results)}/{len(results)} 项")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
