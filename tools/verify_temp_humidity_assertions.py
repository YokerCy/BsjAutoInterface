# -*- coding: UTF-8 -*-
"""
离线验证温湿度报表用例的断言逻辑（不依赖网络）。

用 tools/probe_temp_humidity.py 实际捕获到的三种响应作为输入，
确认断言「既不会恒真（假绿），也不会误伤正常响应」。

重点验证：无数据时服务端返回的是「占位记录」而非空数组，
         断言必须能识别出来，否则会假绿。
"""
import copy
import sys

sys.path.insert(0, ".")

from test_case.test_temp_humidity_report import verify_temp_humidity_response

# ---- 真实捕获：有数据（10-16） ----
RECORD_WITH_DATA = {
    "vehicleId": 89641, "deviceName": "15900000070", "deviceId": "15900000070",
    "group": "DEFAULT_GROUP",
    "time": "2026-10-16 16:14:01~2026-10-16 16:14:54",
    "avgTemp": 40.0, "lowTempCount": 0, "highTempCount": 0,
    "avgHumidity": 40.0, "drivingMileage": 0.0,
}
RESP_WITH_DATA = {"code": 200, "msg": "Success", "data": [RECORD_WITH_DATA]}

# ---- 真实捕获：空时间窗（10-15）返回的是「占位记录」 ----
RECORD_PLACEHOLDER = {
    "vehicleId": 89641, "deviceName": "15900000070", "deviceId": "15900000070",
    "group": "DEFAULT_GROUP",
    "time": "-",
    "avgTemp": None, "lowTempCount": 0, "highTempCount": 0,
    "avgHumidity": None, "drivingMileage": 0.0,
}
RESP_PLACEHOLDER = {"code": 200, "msg": "Success", "data": [RECORD_PLACEHOLDER]}

# ---- 真实捕获：无效车辆 ----
RESP_NO_DATA = {"code": 200, "msg": "No Data", "data": []}

BASE_CASE = {
    "case_name": "获取温湿度报表",
    "expect_code": 200,
    "expect_msg": "Success",
    "require_data": True,
    "payload": {
        "vehicle_ids": [89641],
        "start_time": "2026-10-16 00:00:00",
        "end_time": "2026-10-16 23:59:59",
    },
}


def run(title, resp, expect_pass, case=None):
    case = case or BASE_CASE
    try:
        verify_temp_humidity_response(copy.deepcopy(resp), case)
        ok, detail = True, ""
    except AssertionError as e:
        ok, detail = False, str(e).split("\n")[0][:120]

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

    # 2) 占位记录（空窗口）+ require_data=true -> 应失败
    #    ★ 这是核心：证明断言能识破「占位记录」造成的假绿
    results.append(run("占位记录(10-15) + require_data=true", RESP_PLACEHOLDER, False))

    # 3) 占位记录 + require_data=false -> 应通过（开关有效）
    case_off = copy.deepcopy(BASE_CASE)
    case_off["require_data"] = False
    results.append(run("占位记录(10-15) + require_data=false", RESP_PLACEHOLDER, True, case_off))

    # 4) 无效车辆（msg=No Data）-> 应失败
    results.append(run("无效车辆（msg=No Data）", RESP_NO_DATA, False))

    # 5) 缺字段 -> 应失败
    resp_missing = copy.deepcopy(RESP_WITH_DATA)
    del resp_missing["data"][0]["avgHumidity"]
    results.append(run("记录缺少 avgHumidity 字段", resp_missing, False))

    # 6) 返回了未被请求的车辆 -> 应失败（查询过滤校验）
    resp_other = copy.deepcopy(RESP_WITH_DATA)
    resp_other["data"][0]["vehicleId"] = 27106
    results.append(run("返回未被请求的车辆(27106)", resp_other, False))

    # 7) 返回码错误 -> 应失败
    results.append(run("返回码 500", {"code": 500, "msg": "error", "data": None}, False))

    # 8) 空数组 + require_data=true -> 应失败
    results.append(run("空数组 + require_data=true", {"code": 200, "msg": "Success", "data": []}, False))

    print("=" * 78)
    print(f"通过 {sum(results)}/{len(results)} 项")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
