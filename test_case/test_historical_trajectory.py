# -*- coding: UTF-8 -*-
import json
import allure
import pytest
from base.redConfig import Config
from base.utils import allure_attach_comparison
from profes.historical_trajectory_api import HistoricalTrajectoryApi


cfg = Config()


@allure.epic("历史轨迹")
@allure.feature("查询历史轨迹信息")
@pytest.mark.parametrize(
    "historical_trajectory",
    cfg.get_cases_by_interface("historical_trajectory_expect", "get_historical_trajectory")
)
def test_query_device_historical_trajectory(user_client, historical_trajectory):
    allure.dynamic.title(historical_trajectory["case_name"])  # 在报告左侧显示具体的用例名
    allure.dynamic.description(
        f"预期校验点：{historical_trajectory['expect_code']} / {historical_trajectory['expect_msg']}")

    payload = historical_trajectory.get("payload") or {}

    trajectory_api = HistoricalTrajectoryApi(user_client)
    resp = trajectory_api.get_query_device_historical_trajectory(
        query_param=payload.get("query_param", "15900000070"),
        query_type=payload.get("query_type", 0),
        begin_time=payload.get("begin_time", "2026-09-28 00:00:00"),
        end_time=payload.get("end_time", "2026-09-28 23:59:59"),
        filter_time=payload.get("filter_time", 0),
        stop_status=payload.get("stop_status", 1),
        pos_status=payload.get("pos_status", 0),
    )

    actual_code = resp.get("code")
    actual_msg = resp.get("msg")

    # 关键：附件对比必须是「实际响应」vs「预期」，不能拿预期比预期（假绿）
    allure_attach_comparison(expected=historical_trajectory["expect_code"], actual=actual_code, name="响应状态码")
    allure_attach_comparison(expected=historical_trajectory["expect_msg"], actual=actual_msg, name="响应消息状态")

    # 把请求条件也贴到报告里，方便一眼看出是条件配错还是接口挂了
    allure.attach(json.dumps(payload, ensure_ascii=False, indent=2), name="本次请求条件",
                  attachment_type=allure.attachment_type.JSON)

    assert actual_code == historical_trajectory["expect_code"], \
        f"历史轨迹接口返回码异常: 期望 {historical_trajectory['expect_code']}, 实际 {actual_code}, msg={actual_msg}"

    # No Data 单独给出可操作的排查指引，避免只看到一句断言失败
    if actual_msg == "No Data":
        pytest.fail(
            "历史轨迹返回 No Data —— 请求已被服务端接受(code=200)，但按当前条件没查到任何记录，"
            "属于查询条件不匹配，不是接口挂了。\n"
            "排查顺序：\n"
            "  1) query_type: 0=按设备名(plate)、1=按设备ID(terminalNo)。"
            f"当前 query_type={payload.get('query_type', 0)}, query_param={payload.get('query_param')}，"
            "11 位纯数字通常是 terminalNo，应改成 1。\n"
            "  2) 时间窗内该设备是否确有轨迹上报（注意该接口限流 2 次/分钟）。\n"
            "  3) 直接跑 `python tools/diagnose_trajectory.py` 自动试出可用组合。\n"
            f"实际请求条件: {json.dumps(payload, ensure_ascii=False)}\n"
            f"完整响应: {json.dumps(resp, ensure_ascii=False)[:1000]}"
        )

    assert actual_msg == historical_trajectory["expect_msg"], \
        f"历史轨迹接口返回消息异常: 期望 {historical_trajectory['expect_msg']}, 实际 {actual_msg}"

    # 结构校验：成功响应应包含轨迹列表，避免只验 code 不验结构导致的假绿
    data = resp.get("data") or {}
    base_info = data.get("baseInfo") or {}
    track_list = data.get("trackList")
    assert isinstance(track_list, list) and len(track_list) > 0, \
        f"data.trackList 应为非空列表, 实际={track_list}, trackTotal={data.get('trackTotal')}"

    # 顺带把命中的设备信息打出来，便于确认查到的是不是预期那台设备
    assert base_info, "data.baseInfo 缺失，无法确认命中的是哪台设备"

# 学会造数据再使用
# @allure.epic("历史轨迹")
# @allure.feature("定位车辆当前位置和状态")
# @pytest.mark.parametrize(
#     "get_real_time_location",
#     cfg.get_cases_by_interface("historical_trajectory_expect", "get_real_time_location")
# )
# def test_device_real_time_location(user_client, get_real_time_location):
#     allure.dynamic.title(get_real_time_location["case_name"])  # 在报告左侧显示具体的用例名
#     allure.dynamic.description(
#         f"预期校验点：{get_real_time_location['expect_code']} / {get_real_time_location['expect_msg']}")
#
#     device_real_time_location = HistoricalTrajectoryApi(user_client)
#     resp = device_real_time_location.real_time_location()
#
#     actual_code = resp.get("code")
#     actual_msg = resp.get("msg")
#
#     allure_attach_comparison(expected=get_real_time_location["expect_code"], actual=actual_code, name="响应状态码")
#     allure_attach_comparison(expected=get_real_time_location["expect_msg"], actual=actual_msg, name="响应消息状态")
#
#     assert actual_code == get_real_time_location["expect_code"], \
#         f"实时位置接口返回码异常: 期望 {get_real_time_location['expect_code']}, 实际 {actual_code}, msg={actual_msg}"
#     assert actual_msg == get_real_time_location["expect_msg"], \
#         f"实时位置接口返回消息异常: 期望 {get_real_time_location['expect_msg']}, 实际 {actual_msg}"
