# -*- coding: UTF-8 -*-
import logging
import allure
import pytest
from base.redConfig import Config
from base.utils import allure_attach_comparison
from profes.historical_trajectory_api import HistoricalTrajectoryApi

#
#
cfg = Config()


#
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

    # value = historical_trajectory["payload"]
    # queryparam = value["queryparam"]
    trajectory_api = HistoricalTrajectoryApi(user_client)

    historical_trajectory_api = trajectory_api.get_query_device_historical_trajectory()

    code = historical_trajectory["expect_code"]
    msg = historical_trajectory["expect_msg"]

    allure_attach_comparison(expected=historical_trajectory["expect_code"], actual=code, name="响应状态码")
    allure_attach_comparison(expected=historical_trajectory["expect_msg"], actual=msg, name="响应消息状态")

    assert historical_trajectory_api["code"] == code
    # assert historical_trajectory_api["msg"] == msg


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

    # value = historical_trajectory["payload"]
    # queryparam = value["queryparam"]


    device_real_time_location = HistoricalTrajectoryApi(user_client)

    real_time_location_api = device_real_time_location.real_time_location()

    code = get_real_time_location["expect_code"]
    msg = get_real_time_location["expect_msg"]



    allure_attach_comparison(expected=get_real_time_location["expect_code"], actual=code, name="响应状态码")
    allure_attach_comparison(expected=get_real_time_location["expect_msg"], actual=msg, name="响应消息状态")

    assert real_time_location_api['code'] == code

    # assert real_time_location_api['msg'] == msg
