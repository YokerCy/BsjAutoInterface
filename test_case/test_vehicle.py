# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/9 09:49 
@Author  : bo_god
@File    : test_vehicle.py
@Project : smart_auto_interface 
@Depict    :
'''
from profes.vehicle_api import VehicleApi, find_group_by_name
import allure
import pytest
from base.redConfig import Config
from base.utils import allure_attach_comparison
from profes.userApi import UserApi

cfg = Config()

@allure.epic("车辆管理系统巡检")
@allure.feature("车组模块")
@pytest.mark.parametrize(
    "add_group",
    cfg.get_cases_by_interface("vehicle_expect", "add_Group")
)
def test_add_group(user_client, add_group, clear_group):
    allure.dynamic.title(add_group["case_name"])  # 在报告左侧显示具体的用例名
    allure.dynamic.description(f"预期校验点：{add_group['expect_code']} / {add_group['expect_msg']}")

    user_api = VehicleApi(user_client)

    group_add = user_api.add_group(user_client.userId, add_group["payload"]["group_name"], group_id='')

    code = add_group["expect_code"]
    msg = add_group["expect_msg"]

    allure_attach_comparison(expected=add_group["expect_code"], actual=code, name="响应状态码")
    allure_attach_comparison(expected=add_group["expect_msg"], actual=msg, name="响应消息状态")

    assert group_add["code"] == code
    assert group_add["msg"] == msg


@allure.epic("车辆管理系统巡检")
@allure.feature("车组模块")
@pytest.mark.parametrize(
    "delete_group",
    cfg.get_cases_by_interface("vehicle_expect", "delete_group"),
)
def test_delete_group(new_group, user_client, delete_group):
    allure.dynamic.title(delete_group["case_name"])  # 在报告左侧显示具体的用例名
    allure.dynamic.description(f"预期校验点：{delete_group['expect_code']} / {delete_group['expect_msg']}")

    vehicle_api = VehicleApi(user_client)
    user_api = UserApi(user_client)

    # step 1, 获取用户下所有车组
    userid = user_api.get_load_sim_user(user_client.userId)
    # step 2, 通过车组名反向查找所属车组ID
    group_id = find_group_by_name(userid["data"]["list"], delete_group["payload"]["group_name"])
    # step 3, 删除添加的车组
    delt_group = vehicle_api.delete_group(group_id["groupId"])

    code = delete_group["expect_code"]
    msg = delete_group["expect_msg"]

    allure_attach_comparison(expected=delete_group["expect_code"], actual=code, name="响应状态码")
    allure_attach_comparison(expected=delete_group["expect_msg"], actual=msg, name="响应消息状态")

    assert delt_group["code"] == code
    assert delt_group["msg"] == msg