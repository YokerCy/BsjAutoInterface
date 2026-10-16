# -*- coding: UTF-8 -*-
import json
from datetime import datetime

import allure
import pytest

from base.redConfig import Config
from base.utils import allure_attach_comparison
from profes.temp_humidity_report import TempHumidityReport

cfg = Config()

# ---------------------------------------------------------------------------
# 实测返回结构（探测 tools/probe_temp_humidity.py 得到）：
#   data 是**纯数组**（没有 total/pageNum 分页包装）：
#   [
#     {"vehicleId": 89641, "deviceName": "15900000070", "deviceId": "15900000070",
#      "group": "DEFAULT_GROUP",
#      "time": "2026-10-16 16:14:01~2026-10-16 16:14:54",   <-- 区间字符串，不是单点时间
#      "avgTemp": 40.0, "lowTempCount": 0, "highTempCount": 0,
#      "avgHumidity": 40.0, "drivingMileage": 0.0}
#   ]
#
# ⚠️ 无数据时（实测）**不是空数组**，而是一条「占位记录」：
#   [{"vehicleId": 89641, ..., "time": "-", "avgTemp": null, "avgHumidity": null,
#     "lowTempCount": 0, "highTempCount": 0, "drivingMileage": 0.0}]
#   → code=200 / msg=Success / 数组长度 1，只看状态码或长度会假绿。
#   → lowTempCount / highTempCount / drivingMileage 在任何情况下都是 0，不可作判据。
#   → 有效判据是 avgTemp / avgHumidity 是否为 null（或 time 是否为 "-"）。
#
# 无效 vehicleId 时（实测）：code=200 但 msg="No Data"、data=[]。
# ---------------------------------------------------------------------------

# 每条记录应包含的字段（实测返回的完整集合，做契约校验）
TEMP_HUMIDITY_KEYS = {
    "vehicleId", "deviceName", "deviceId", "group", "time",
    "avgTemp", "lowTempCount", "highTempCount", "avgHumidity", "drivingMileage",
}
# 这些计数/里程字段任何情况下都应为数字
ALWAYS_NUMERIC_KEYS = {"lowTempCount", "highTempCount", "drivingMileage"}


def _payload(case):
    return case.get("payload", {})


def _vehicle_ids(p):
    """payload.vehicle_ids 支持单个数字或数组，统一成列表。"""
    v = p.get("vehicle_ids", [])
    if not isinstance(v, list):
        v = [v]
    return v


def verify_temp_humidity_response(result, case):
    """
    校验温湿度报表响应（纯函数，不依赖网络，便于离线回归断言逻辑）。

    :param result: 接口返回的 JSON dict
    :param case:   yaml 用例（提供 expect_code/expect_msg/payload/require_data）
    :raises AssertionError: 任一校验点不通过
    """
    p = _payload(case)
    name = case["case_name"]

    actual_code = result.get("code")
    actual_msg = result.get("msg")
    actual_data = result.get("data")

    # 失败时把完整响应带进断言信息，直接看到服务端真实报错
    assert actual_code == case["expect_code"], \
        f"[{name}] 返回码异常: 期望 {case['expect_code']}, 实际 {actual_code}, " \
        f"响应={json.dumps(result, ensure_ascii=False)[:1500]}"

    if actual_msg != case["expect_msg"]:
        hint = ""
        if actual_msg == "No Data":
            hint = ("（服务端 No Data 通常表示查询条件没有匹配到车辆，"
                    "请检查 vehicle_ids 是否有效、或该时间窗内是否有设备数据）")
        raise AssertionError(
            f"[{name}] 返回消息异常: 期望 {case['expect_msg']}, 实际 {actual_msg}{hint}"
        )

    # ---- 契约校验（避免「只比状态码」的假绿） ----
    assert isinstance(actual_data, list), \
        f"[{name}] data 应为数组, 实际 {type(actual_data).__name__}, " \
        f"data={json.dumps(actual_data, ensure_ascii=False)[:500]}"

    for idx, item in enumerate(actual_data):
        missing = TEMP_HUMIDITY_KEYS - set(item.keys())
        assert not missing, \
            f"[{name}] 第{idx}条记录缺少字段 {missing}, " \
            f"实际={json.dumps(item, ensure_ascii=False)[:600]}"

        for k in ALWAYS_NUMERIC_KEYS:
            v = item.get(k)
            assert isinstance(v, (int, float)) and not isinstance(v, bool), \
                f"[{name}] 第{idx}条 {k} 应为数字, 实际 {type(v).__name__}={v!r}"

        assert isinstance(item.get("time"), str) and item["time"], \
            f"[{name}] 第{idx}条 time 应为非空字符串, 实际 {item.get('time')!r}"

    # 查询过滤是否生效：返回记录的 vehicleId 都应落在请求的 vehicleIds 内
    req_ids = set(_vehicle_ids(p))
    if req_ids:
        returned = {item.get("vehicleId") for item in actual_data}
        unexpected = returned - req_ids
        assert not unexpected, \
            f"[{name}] 返回了未被请求的车辆 {unexpected}（请求={sorted(req_ids)}），" \
            f"查询过滤可能未生效"

    # ---- 数据存在性校验（可用 yaml 的 require_data: false 关闭） ----
    # 见文件头注释：无数据时服务端返回一条 avgTemp/avgHumidity 为 null 的占位记录，
    # 数组长度恒为 1，必须用字段值判定，否则会假绿。
    if case.get("require_data", True):
        assert actual_data, \
            f"[{name}] data 为空数组：车辆 {sorted(req_ids)} 在 " \
            f"[{p['start_time']} ~ {p['end_time']}] 内查不到温湿度数据。" \
            f"若确认该时段本就无数据，请调整测试数据或把 yaml 的 require_data 设为 false"

        valid = [
            it for it in actual_data
            if it.get("avgTemp") is not None and it.get("avgHumidity") is not None
        ]
        assert valid, \
            f"[{name}] 所有记录的 avgTemp/avgHumidity 均为 null、time 为 \"-\"，" \
            f"说明该时段没有真实的温湿度数据（返回的是占位记录）。" \
            f"若确认该时段本就无数据，请调整测试数据或设 require_data=false。" \
            f"实际={json.dumps(actual_data, ensure_ascii=False)[:600]}"


@allure.epic("温湿度报表")
@allure.feature("温湿度报表列表")
@pytest.mark.parametrize(
    "get_temp_humidity_report",
    cfg.get_cases_by_interface("temp_humidity_report", "get_temp_humidity_report")
)
def test_get_temp_humidity_report(user_client, get_temp_humidity_report):
    allure.dynamic.title(get_temp_humidity_report["case_name"])
    allure.dynamic.description(
        f"预期校验点：{get_temp_humidity_report['expect_code']} / "
        f"{get_temp_humidity_report['expect_msg']}"
    )

    p = _payload(get_temp_humidity_report)

    api = TempHumidityReport(user_client)
    result = api.get_temp_humidity_report(
        vehicle_ids=_vehicle_ids(p),
        start_time=p.get("start_time"),
        end_time=p.get("end_time"),
        page_num=p.get("page_num", 1),
        page_size=p.get("page_size", 20),
    )

    allure_attach_comparison(
        expected=get_temp_humidity_report["expect_code"],
        actual=result.get("code"), name="响应状态码"
    )
    allure_attach_comparison(
        expected=get_temp_humidity_report["expect_msg"],
        actual=result.get("msg"), name="响应消息状态"
    )

    verify_temp_humidity_response(result, get_temp_humidity_report)


# ===========================================================================
# 温湿度报表详情（POST /tempHumidityReport/getTempHumidityDetailReport）
# ---------------------------------------------------------------------------
# 实测返回结构（探测 tools/probe_temp_humidity.py 得到）：
#   data 是数组，每条记录：
#   {"deviceName": "15900000070", "deviceId": "15900000070",
#    "group": "DEFAULT_GROUP",
#    "time": "2026-10-16 16:14:01",              <-- 单点时间（列表接口是区间）
#    "temperature": ["40.00"], "humidity": ["40.0"],   <-- 数组，不是数字
#    "speed": 90, "mileage": 15.0,
#    "address": "36.38734N,45.39252E", "alarmList": null}
#
# 与列表接口的差异（重要）：
#   - 无数据时返回 msg="No Data" + data=[]（**不是**占位记录，比列表接口直白）
#   - 没有 vehicleId 字段，只有 deviceName/deviceId
#   - 实测 pageNum=2 仍返回与第 1 页相同的数据（分页是否生效存疑，故不作断言）
# ===========================================================================

# 详情记录应包含的字段
TEMP_HUMIDITY_DETAIL_KEYS = {
    "deviceName", "deviceId", "group", "time",
    "temperature", "humidity", "speed", "mileage", "address", "alarmList",
}
DETAIL_TIME_FMT = "%Y-%m-%d %H:%M:%S"


def verify_temp_humidity_detail_response(result, case):
    """
    校验温湿度报表详情响应（纯函数，不依赖网络，便于离线回归断言逻辑）。

    :param result: 接口返回的 JSON dict
    :param case:   yaml 用例（提供 expect_code/expect_msg/payload/require_data）
    :raises AssertionError: 任一校验点不通过
    """
    p = _payload(case)
    name = case["case_name"]

    actual_code = result.get("code")
    actual_msg = result.get("msg")
    actual_data = result.get("data")

    assert actual_code == case["expect_code"], \
        f"[{name}] 返回码异常: 期望 {case['expect_code']}, 实际 {actual_code}, " \
        f"响应={json.dumps(result, ensure_ascii=False)[:1500]}"

    if actual_msg != case["expect_msg"]:
        hint = ""
        if actual_msg == "No Data":
            hint = ("（服务端 No Data 表示该车辆在此时间窗内没有温湿度数据；"
                    "请检查 vehicleId 是否有效、时间窗内是否有数据）")
        raise AssertionError(
            f"[{name}] 返回消息异常: 期望 {case['expect_msg']}, 实际 {actual_msg}{hint}"
        )

    assert isinstance(actual_data, list), \
        f"[{name}] data 应为数组, 实际 {type(actual_data).__name__}, " \
        f"data={json.dumps(actual_data, ensure_ascii=False)[:500]}"

    start_dt = datetime.strptime(p["start_time"], DETAIL_TIME_FMT)
    end_dt = datetime.strptime(p["end_time"], DETAIL_TIME_FMT)

    for idx, item in enumerate(actual_data):
        missing = TEMP_HUMIDITY_DETAIL_KEYS - set(item.keys())
        assert not missing, \
            f"[{name}] 第{idx}条记录缺少字段 {missing}, " \
            f"实际={json.dumps(item, ensure_ascii=False)[:600]}"

        # 温湿度是数组（本接口按通道返回），不是标量
        for k in ("temperature", "humidity"):
            assert isinstance(item.get(k), list), \
                f"[{name}] 第{idx}条 {k} 应为数组, " \
                f"实际 {type(item.get(k)).__name__}={item.get(k)!r}"

        # speed / mileage 应为数字
        for k in ("speed", "mileage"):
            v = item.get(k)
            assert isinstance(v, (int, float)) and not isinstance(v, bool), \
                f"[{name}] 第{idx}条 {k} 应为数字, 实际 {type(v).__name__}={v!r}"

        # 时间格式 + 落在请求区间内（验证时间过滤真的生效）
        try:
            pt_time = datetime.strptime(item["time"], DETAIL_TIME_FMT)
        except Exception:
            raise AssertionError(
                f"[{name}] 第{idx}条 time 格式不符合 yyyy-MM-dd HH:mm:ss: {item['time']!r}"
            )
        assert start_dt <= pt_time <= end_dt, \
            f"[{name}] 第{idx}条时间 {item['time']} 超出请求区间 " \
            f"[{p['start_time']} ~ {p['end_time']}]，时间过滤可能未生效"

    # 单车详情：返回记录不应混入其他设备
    if actual_data:
        device_ids = {item.get("deviceId") for item in actual_data}
        assert len(device_ids) == 1, \
            f"[{name}] 单车详情返回了多台设备的数据 {device_ids}，车辆过滤可能未生效"

    # ---- 数据存在性校验（可用 yaml 的 require_data: false 关闭） ----
    if case.get("require_data", True):
        assert actual_data, \
            f"[{name}] data 为空数组：vehicleId={p.get('vehicle_id')} 在 " \
            f"[{p['start_time']} ~ {p['end_time']}] 内查不到温湿度明细。" \
            f"若确认该时段本就无数据，请调整测试数据或把 yaml 的 require_data 设为 false"

        valid = [
            it for it in actual_data
            if it.get("temperature") and it.get("humidity")
        ]
        assert valid, \
            f"[{name}] 所有记录的 temperature/humidity 均为空数组，" \
            f"说明返回的不是有效温湿度明细。" \
            f"若确认该时段本就无数据，请设 require_data=false。" \
            f"实际={json.dumps(actual_data, ensure_ascii=False)[:600]}"


@allure.epic("温湿度报表")
@allure.feature("温湿度报表详情")
@pytest.mark.parametrize(
    "get_temp_humidity_detail_report",
    cfg.get_cases_by_interface("temp_humidity_report", "get_temp_humidity_detail_report")
)
def test_get_temp_humidity_detail_report(user_client, get_temp_humidity_detail_report):
    allure.dynamic.title(get_temp_humidity_detail_report["case_name"])
    allure.dynamic.description(
        f"预期校验点：{get_temp_humidity_detail_report['expect_code']} / "
        f"{get_temp_humidity_detail_report['expect_msg']}"
    )

    p = _payload(get_temp_humidity_detail_report)

    api = TempHumidityReport(user_client)
    result = api.get_temp_humidity_detail_report(
        vehicle_id=p.get("vehicle_id"),
        start_time=p.get("start_time"),
        end_time=p.get("end_time"),
        user_id=p.get("user_id"),          # None -> 自动取登录用户ID
        page_num=p.get("page_num", 1),
        page_size=p.get("page_size", 20),
    )

    allure_attach_comparison(
        expected=get_temp_humidity_detail_report["expect_code"],
        actual=result.get("code"), name="响应状态码"
    )
    allure_attach_comparison(
        expected=get_temp_humidity_detail_report["expect_msg"],
        actual=result.get("msg"), name="响应消息状态"
    )

    verify_temp_humidity_detail_response(result, get_temp_humidity_detail_report)
