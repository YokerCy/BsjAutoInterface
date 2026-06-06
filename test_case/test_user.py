# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/6 11:16 
@Author  : bo_god
@File    : test_user.py
@Project : smart_auto_interface 
@Depict    :
'''
import logging
from profes.userApi import UserApi
import allure
import pytest
from base.redConfig import Config
from base.utils import allure_attach_comparison
from profes.vehicle_api import find_user_by_name

cfg = Config()
# test_cases = cfg.get_test_data("user_expect")
#
# # 筛选出所有属于 get_user_info 接口的数据
# info_cases = [c for c in test_cases if c["interface"] == "get_user_info"]

@allure.epic("车辆管理系统巡检")
@allure.feature("用户树模块")
@pytest.mark.parametrize(
    "user_tree",
    cfg.get_cases_by_interface("user_expect", "get_user_tree")
)
def test_user_tree(user_client, user_tree):
    allure.dynamic.title(user_tree["case_name"])  # 在报告左侧显示具体的用例名
    allure.dynamic.description(f"预期校验点：{user_tree['self_name']} / {user_tree['children_name']}")

    user_api = UserApi(user_client)

    user_trees = user_api.get_user_tree()
    # paymentLink / parentId / id / order / phone

    code = user_tree["expect_code"]
    msg = user_tree["expect_msg"]
    children_name = user_tree["children_name"]
    self_name = user_tree["self_name"]

    allure_attach_comparison(expected=user_tree["expect_code"], actual=code, name="响应状态码")
    allure_attach_comparison(expected=user_tree["expect_msg"], actual=msg, name="响应消息状态")
    allure_attach_comparison(expected=user_tree["children_name"], actual=children_name, name="校验子级用户名")
    allure_attach_comparison(expected=user_tree["self_name"], actual=self_name, name="验证本身用户名")

    assert user_trees["code"] == code
    assert user_trees["msg"] == msg
    assert user_trees["data"][0]["children"][0]["name"] == children_name  # 子级第一个用户名
    assert user_trees["data"][0]["name"] == self_name  # 本身用户名


@allure.epic("车辆管理系统巡检")
@allure.feature("用户所属车组")
@pytest.mark.parametrize(
    "user_groups",
    cfg.get_cases_by_interface("user_expect", "loadSimpleByUsers")
)
def test_load_simple_by_users(user_client, user_groups):
    allure.dynamic.title(user_groups["case_name"])
    allure.dynamic.description(f"预期校验点：{user_groups['expect_code']} / {user_groups['expect_msg']}")

    user_api= UserApi(user_client)
    user_load = user_api.get_load_sim_user(user_client.userId)

    code = user_groups["expect_code"]
    msg = user_groups["expect_msg"]
    quantity = user_groups["quantity"]

    allure_attach_comparison(expected=user_groups["expect_code"], actual=code, name="响应状态码")
    allure_attach_comparison(expected=user_groups["expect_msg"], actual=msg, name="响应消息状态")
    allure_attach_comparison(expected=user_groups["quantity"], actual=quantity,name="数据体数量")

    assert user_load["code"] == code
    assert user_load["msg"] == msg
    assert len(user_load["data"]["list"]) >= quantity

@allure.epic("车辆管理系统巡检")
@allure.feature("新增用户")
@pytest.mark.parametrize(
    "add_user",
    cfg.get_cases_by_interface("user_expect", "addUser")
)
def test_add_user(clear_add_user, user_client, add_user):
    allure.dynamic.title(add_user["case_name"])
    allure.dynamic.description(f"预期校验点：{add_user['expect_code']} / {add_user['expect_msg']}")
    values = add_user["payload"]
    logging.info(f"新增用户-配置文件-payload: {values}")

    user_api= UserApi(user_client)

    user_name = values["userName"]
    email = values["email"]
    pwd = cfg.aes_encrypt_like_cryptojs_ecb(values["password"])
    phone = values["phone"]
    parent_id = user_client.userId
    logging.info(f"新增用户入参:{user_name, email, pwd, phone}")
    user_load = user_api.add_user(user_name, email, pwd, phone, parent_id)

    code = add_user["expect_code"]
    msg = add_user["expect_msg"]

    allure_attach_comparison(expected=add_user["expect_code"], actual=code, name="响应状态码")
    allure_attach_comparison(expected=add_user["expect_msg"], actual=msg, name="响应消息状态")

    assert user_load["code"] == code
    assert user_load["msg"] == msg


@allure.epic("车辆管理系统巡检")
@allure.feature("修改用户信息")
@pytest.mark.parametrize(
    "upg_user",
    cfg.get_cases_by_interface("user_expect", "updateUser")
)
def test_update_user(teardown_update_user_info, user_client, upg_user):
    allure.dynamic.title(upg_user["case_name"])
    allure.dynamic.description(f"预期校验点：{upg_user['expect_code']} / {upg_user['expect_msg']}")
    before_modification = upg_user["pre"]
    before_end = upg_user["payload"]

    # 查找需要修改用户名 并执行修改用户名
    user_api= UserApi(user_client)
    get_name = user_api.get_user_tree()["data"][0]["children"]
    find_name = find_user_by_name(get_name, before_modification["userName"])
    user_id = find_name["id"]
    logging.info(f"查找修改用户ID>>>: {user_id}")
    user_load = user_api.update_user(user_id, before_end["userName"], before_end["email"], before_end["phone"])

    code = upg_user["expect_code"]
    msg = upg_user["expect_msg"]
    end_user_name = before_end["userName"]

    allure_attach_comparison(expected=upg_user["expect_code"], actual=code, name="响应状态码")
    allure_attach_comparison(expected=upg_user["expect_msg"], actual=msg, name="响应消息状态")
    allure_attach_comparison(expected=before_end["userName"], actual=end_user_name, name="用户名校验")

    assert user_load["code"] == code
    assert user_load["msg"] == msg
    assert user_load["data"]['userName'] == end_user_name

@allure.epic("车辆管理系统巡检")
@allure.feature("删除用户")
@pytest.mark.parametrize(
    "del_user",
    cfg.get_cases_by_interface("user_expect", "delUser")
)
def test_del_user(setup_user_add, user_client, del_user):
    allure.dynamic.title(del_user["case_name"])
    allure.dynamic.description(f"预期校验点：{del_user['expect_code']} / {del_user['expect_msg']}")

    user_api= UserApi(user_client)
    get_name = user_api.get_user_tree()
    # 查找到需要删除用户名并执行删除
    value = get_name["data"][0]["children"]

    logging.info(f"用户数: {value}")
    delete_id = del_user["payload"]["userName"]

    find_name = find_user_by_name(value, delete_id)
    logging.info(f"查找删除用户名对应id: {find_name}")

    user_id = find_name["id"]
    logging.info(f"查找删除用户ID>>>: {user_id}")

    user_load = user_api.del_user(user_id)

    code = del_user["expect_code"]
    msg = del_user["expect_msg"]
    empty = True

    allure_attach_comparison(expected=del_user["expect_code"], actual=code, name="响应状态码")
    allure_attach_comparison(expected=del_user["expect_msg"], actual=msg, name="响应消息状态")
    allure_attach_comparison(expected=True, actual=empty, name="empty为true")

    assert user_load["code"] == code
    assert user_load["msg"] == msg
    assert user_load["empty"] == empty
