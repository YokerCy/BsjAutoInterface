# -*- coding: UTF-8 -*-
import json
from datetime import datetime

import allure
import pytest

from base.redConfig import Config
from base.utils import allure_attach_comparison
from profes.oil_report import OilReport

cfg = Config()

# ---------------------------------------------------------------------------
# 实测返回结构（探测 tools/probe_oil_fuel.py 得到）：
#   data = {
#     "addCount": 0, "reduceCount": 0,
#     "data": [                                   <-- 曲线点数组（注意是嵌套的 data）
#       {"time": "2026-10-16 16:14:01", "speed": 90.0,
#        "data": {"1": {"value": 15.0, "actionType": 0, "actionValue": 0.0,
#                       "liquidLevel": 0, "percent": 15, "voltage": 0.0}}}
#     ],
#     "fuel": 0.0, "mileage": 0.0, "fuelKilometers": 0.0,
#     "fuelCost": 0.0, "channelIds": [1]
#   }
#
# 无数据时（实测）：
#   {"addCount":0,"reduceCount":0,"data":[],"fuel":0.0,"mileage":0.0,
#    "fuelKilometers":0.0,"fuelCost":0.0,"channelIds":null}
#   —— 注意 fuel/mileage 在有数据与无数据时**都是 0**，
#      光看指标值无法区分「有数据但油耗为 0」和「根本没数据」，
#      必须靠 channelIds / 曲线点判定，否则用例会假绿。
# ---------------------------------------------------------------------------

# 顶层核心指标字段（油耗/里程/每公里油耗/油费/油量通道）
FUEL_METRIC_KEYS = {"fuel", "mileage", "fuelKilometers", "fuelCost", "channelIds"}
# 曲线点字段
FUEL_POINT_KEYS = {"time", "speed", "data"}
# 数值型指标（用于类型校验）
FUEL_NUMERIC_KEYS = {"fuel", "mileage", "fuelKilometers", "fuelCost"}
TIME_FMT = "%Y-%m-%d %H:%M:%S"


def _payload(case):
    return case.get("payload", {})


def _vehicle(p):
    """用于断言信息的车辆标识，缺失时给个占位符，避免报错信息里出现 None。"""
    return p.get("vehicle_id", "<未配置 vehicle_id>")


def _parse_time(s):
    return datetime.strptime(s, TIME_FMT)


def verify_fuel_response(result, case):
    """
    校验油耗分析表响应（纯函数，不依赖网络，便于离线回归断言逻辑）。

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
    assert actual_msg == case["expect_msg"], \
        f"[{name}] 返回消息异常: 期望 {case['expect_msg']}, 实际 {actual_msg}"

    # ---- 契约校验（避免「只比状态码」的假绿） ----
    assert isinstance(actual_data, dict), \
        f"[{name}] data 应为对象, 实际 {type(actual_data).__name__}, " \
        f"data={json.dumps(actual_data, ensure_ascii=False)[:500]}"

    missing = FUEL_METRIC_KEYS - set(actual_data.keys())
    assert not missing, \
        f"[{name}] 响应缺少核心指标字段 {missing}, 实际字段={sorted(actual_data.keys())}"

    # 指标值应为数字（允许 int/float，注意 bool 是 int 子类需排除）
    for k in FUEL_NUMERIC_KEYS:
        v = actual_data.get(k)
        assert isinstance(v, (int, float)) and not isinstance(v, bool), \
            f"[{name}] 指标 {k} 应为数字, 实际 {type(v).__name__}={v!r}"

    # channelIds：数组或 null（null 表示该时间窗内没有油量传感器数据）
    channels = actual_data.get("channelIds")
    assert isinstance(channels, (list, type(None))), \
        f"[{name}] channelIds 应为数组或 null, 实际 {type(channels).__name__}={channels!r}"

    # 曲线点
    points = actual_data.get("data")
    assert isinstance(points, list), \
        f"[{name}] 曲线点 data 应为数组, 实际 {type(points).__name__}"

    # ---- 数据存在性校验（可用 yaml 的 require_data: false 关闭） ----
    # 见文件头注释：指标值无法区分有无数据，必须用曲线点/通道判定。
    # 注意：require_data 是用例级期望，写在 yaml 顶层而非 payload 里。
    if case.get("require_data", True):
        assert points, \
            f"[{name}] 曲线点 data 为空：车辆 {_vehicle(p)} 在 " \
            f"[{p['start_time']} ~ {p['end_time']}] 内查不到油耗曲线数据。" \
            f"若确认该时段本就无数据，请调整测试数据或把 yaml 的 require_data 设为 false"
        assert channels, \
            f"[{name}] channelIds 为 {channels!r}：该时段未取到任何油量传感器通道。" \
            f"同上，若确认无数据请调整测试数据或设 require_data=false"

    start_dt = _parse_time(p["start_time"])
    end_dt = _parse_time(p["end_time"])

    for idx, pt in enumerate(points):
        pt_missing = FUEL_POINT_KEYS - set(pt.keys())
        assert not pt_missing, \
            f"[{name}] 曲线点第{idx}条缺少字段 {pt_missing}, " \
            f"实际={json.dumps(pt, ensure_ascii=False)[:500]}"

        # 时间过滤是否真的生效：曲线点时间必须落在请求区间内
        # （若服务端忽略 startTime/endTime，这条会立刻抓到）
        try:
            pt_time = _parse_time(pt["time"])
        except Exception:
            raise AssertionError(
                f"[{name}] 曲线点第{idx}条 time 格式不符合 yyyy-MM-dd HH:mm:ss: {pt['time']!r}"
            )
        assert start_dt <= pt_time <= end_dt, \
            f"[{name}] 曲线点第{idx}条时间 {pt['time']} 超出请求区间 " \
            f"[{p['start_time']} ~ {p['end_time']}]，时间过滤可能未生效"


@allure.epic("油耗报表")
@allure.feature("价格单车油耗分析表")
@pytest.mark.parametrize(
    "get_vehicle_fuel",
    cfg.get_cases_by_interface("oil_report", "get_vehicle_fuel")
)
def test_get_vehicle_fuel(user_client, get_vehicle_fuel):
    allure.dynamic.title(get_vehicle_fuel["case_name"])
    allure.dynamic.description(
        f"预期校验点：{get_vehicle_fuel['expect_code']} / {get_vehicle_fuel['expect_msg']}"
    )

    p = _payload(get_vehicle_fuel)

    oil_api = OilReport(user_client)
    result = oil_api.get_vehicle_fuel(
        user_id=p.get("user_id"),          # None -> 自动取登录用户ID
        vehicle_id=p.get("vehicle_id"),
        start_time=p.get("start_time"),
        end_time=p.get("end_time"),
        unit_price=p.get("unit_price", 1),
        client_time=p.get("client_time"),  # None -> 自动取当前时间
    )

    allure_attach_comparison(
        expected=get_vehicle_fuel["expect_code"], actual=result.get("code"), name="响应状态码"
    )
    allure_attach_comparison(
        expected=get_vehicle_fuel["expect_msg"], actual=result.get("msg"), name="响应消息状态"
    )

    verify_fuel_response(result, get_vehicle_fuel)
