# -*- coding: UTF-8 -*-
import logging
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

    trajectory_api = HistoricalTrajectoryApi(user_client)
    resp = trajectory_api.get_query_device_historical_trajectory()

    actual_code = resp.get("code")
    actual_msg = resp.get("msg")

    # 关键：附件对比必须是「实际响应」vs「预期」，不能拿预期比预期（假绿）
    allure_attach_comparison(expected=historical_trajectory["expect_code"], actual=actual_code, name="响应状态码")
    allure_attach_comparison(expected=historical_trajectory["expect_msg"], actual=actual_msg, name="响应消息状态")

    assert actual_code == historical_trajectory["expect_code"], \
        f"历史轨迹接口返回码异常: 期望 {historical_trajectory['expect_code']}, 实际 {actual_code}, msg={actual_msg}"
    assert actual_msg == historical_trajectory["expect_msg"], \
        f"历史轨迹接口返回消息异常: 期望 {historical_trajectory['expect_msg']}, 实际 {actual_msg}"

    # 结构校验：成功响应应包含轨迹列表，避免只验 code 不验结构导致的假绿
    if actual_code == 200:
        assert isinstance(resp.get("data", {}).get("trackList"), list), "data.trackList 应为列表"


@allure.epic("历史轨迹")
@allure.feature("定位车辆当前位置和状态")
@pytest.mark.parametrize(
    "get_real_time_location",
    cfg.get_cases_by_interface("historical_trajectory_expect", "get_real_time_location")
)
def test_device_real_time_location(user_client, get_real_time_location):
    allure.dynamic.title(get_real_time_location["case_name"])  # 在报告左侧显示具体的用例名
    allure.dynamic.description(
        f"预期校验点：{get_real_time_location['expect_code']} / {get_real_time_location['expect_msg']}")

    device_real_time_location = HistoricalTrajectoryApi(user_client)
    resp = device_real_time_location.real_time_location()

    actual_code = resp.get("code")
    actual_msg = resp.get("msg")

    allure_attach_comparison(expected=get_real_time_location["expect_code"], actual=actual_code, name="响应状态码")
    allure_attach_comparison(expected=get_real_time_location["expect_msg"], actual=actual_msg, name="响应消息状态")

    assert actual_code == get_real_time_location["expect_code"], \
        f"实时位置接口返回码异常: 期望 {get_real_time_location['expect_code']}, 实际 {actual_code}, msg={actual_msg}"
    assert actual_msg == get_real_time_location["expect_msg"], \
        f"实时位置接口返回消息异常: 期望 {get_real_time_location['expect_msg']}, 实际 {actual_msg}"
