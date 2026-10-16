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

from test_case.test_temp_humidity_report import (
    verify_temp_humidity_response,
    verify_temp_humidity_detail_response,
)

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

    # ==================== 详情接口 ====================
    print()
    print("=" * 78)
    print("详情接口 /tempHumidityReport/getTempHumidityDetailReport")
    print("=" * 78)

    # ---- 真实捕获：详情有数据（10-16，2 条） ----
    detail_record = {
        "deviceName": "15900000070", "deviceId": "15900000070",
        "group": "DEFAULT_GROUP", "time": "2026-10-16 16:14:01",
        "temperature": ["40.00"], "humidity": ["40.0"],
        "speed": 90, "mileage": 15.0,
        "address": "36.38734N,45.39252E", "alarmList": None,
    }
    detail_record2 = dict(detail_record, time="2026-10-16 16:14:54")
    RESP_DETAIL_OK = {"code": 200, "msg": "Success", "data": [detail_record, detail_record2]}
    # ---- 真实捕获：详情无数据 / 无效车辆（都是这个形态） ----
    RESP_DETAIL_NODATA = {"code": 200, "msg": "No Data", "data": []}

    detail_case = copy.deepcopy(BASE_CASE)
    detail_case["case_name"] = "获取温湿度报表详情"
    detail_case["payload"] = {
        "vehicle_id": 89641,
        "start_time": "2026-10-16 00:00:00",
        "end_time": "2026-10-16 23:59:59",
    }

    def run_detail(title, resp, expect_pass, case=None):
        case = case or detail_case
        try:
            verify_temp_humidity_detail_response(copy.deepcopy(resp), case)
            ok, dt = True, ""
        except AssertionError as e:
            ok, dt = False, str(e).split("\n")[0][:120]
        mark = "✅" if ok == expect_pass else "❌ 与预期不符"
        print(f"{mark} {title}")
        print(f"     预期 {'通过' if expect_pass else '失败'} / 实际 {'通过' if ok else '失败'}")
        if dt:
            print(f"     断言信息: {dt}")
        return ok == expect_pass

    # 1) 有数据 -> 应通过
    results.append(run_detail("详情有数据(10-16)", RESP_DETAIL_OK, True))

    # 2) No Data -> 应失败（msg 校验拦住）
    results.append(run_detail("详情 No Data（无效车辆/无数据）", RESP_DETAIL_NODATA, False))

    # 3) 人为构造「msg=Success 但空数组」-> require_data 应拦住
    resp_fake_ok = {"code": 200, "msg": "Success", "data": []}
    results.append(run_detail("msg=Success 但空数组 + require_data=true", resp_fake_ok, False))

    # 4) 同上但关掉 require_data -> 应通过（开关有效）
    case_off2 = copy.deepcopy(detail_case)
    case_off2["require_data"] = False
    results.append(run_detail("同上 + require_data=false", resp_fake_ok, True, case_off2))

    # 5) temperature 不是数组 -> 应失败
    resp_bad_t = copy.deepcopy(RESP_DETAIL_OK)
    resp_bad_t["data"][0]["temperature"] = 40.0
    results.append(run_detail("temperature 不是数组", resp_bad_t, False))

    # 6) time 越界 -> 应失败
    resp_bad_time = copy.deepcopy(RESP_DETAIL_OK)
    resp_bad_time["data"][0]["time"] = "2026-10-20 08:00:00"
    results.append(run_detail("time 越界", resp_bad_time, False))

    # 7) 混入其他设备 -> 应失败（单车详情不该出现多台设备）
    resp_multi = copy.deepcopy(RESP_DETAIL_OK)
    resp_multi["data"][1]["deviceId"] = "11222111222"
    results.append(run_detail("混入其他设备", resp_multi, False))

    # 8) 缺字段 -> 应失败
    resp_missing2 = copy.deepcopy(RESP_DETAIL_OK)
    del resp_missing2["data"][0]["address"]
    results.append(run_detail("记录缺少 address 字段", resp_missing2, False))

    # 9) 空温度数组 + require_data=true -> 应失败
    resp_empty_arr = copy.deepcopy(RESP_DETAIL_OK)
    resp_empty_arr["data"] = [dict(detail_record, temperature=[], humidity=[])]
    results.append(run_detail("温湿度数组为空", resp_empty_arr, False))

    print("=" * 78)
    print(f"通过 {sum(results)}/{len(results)} 项")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
