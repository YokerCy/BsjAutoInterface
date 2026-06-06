# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/6 10:45 
@Author  : bo_god
@File    : conftest.py
@Project : smart_auto_interface 
@Depict    :
'''
import pytest

from profes import vehicle_api
from profes.vehicle_api import VehicleApi, find_group_by_name, find_user_by_name
from profes.userApi import UserApi
from base.log import logger
from base.redConfig import Config


cfg = Config()


@pytest.fixture(scope="function")
def new_group(user_client, request):
    """
        通过 request.param 获取参数化中的当前 case 对象
    """
    params = request.node.callspec.params
    logger.info(f"前置参数 pre 为: {params}")
    key, case_data = next(iter(params.items()))
    case_datas = case_data['pre']
    logger.info(f"groupName: {case_datas}")

    vehicle_api = VehicleApi(user_client)
    # 调用接口创建车组
    vehicle_api.add_group(user_client.userId, case_datas, group_id='')

    yield

    # 用例结束后清理数据
    user_api = UserApi(user_client)
    # step 1, 获取用户下所有车组
    user_id = user_client.userId
    logger.info(f"获取用户ID: {user_id}")
    userid = user_api.get_load_sim_user(user_id)
    tear_d = userid["data"]["list"]
    logger.info(f"后置用户ID>> : {tear_d}, 前置获取用户名:{case_datas}")
    # step 2, 通过车组名反向查找所属车组ID

    group_id = find_group_by_name(tear_d, case_datas)
    logger.info(f"获取待删除车组ID: {group_id}")
    # step 3, 删除添加的车组, 判空处理
    if group_id:
        try:
            vehicle_api.delete_group(group_id["groupId"])
            logger.info(f"teardown 清理成功，group_id={group_id}")
        except Exception as e:
            logger.warning(f"teardown 清理失败，但不影响测试主结果: {e}")


@pytest.fixture(scope="function")
def clear_group(user_client, request):
    logger.info(f"清理车组后置执行")
    yield
    params = request.node.callspec.params
    logger.info(f"删除车组前置参数 pre 为: {params}")
    key, case_data = next(iter(params.items()))
    case_datas = case_data['pre']
    logger.info(f"待删除车组名: {case_datas}")

    user_api = UserApi(user_client)
    vehicle_api = VehicleApi(user_client)
    # step 1, 获取用户下所有车组
    user_id = user_client.userId
    logger.info(f"获取用户ID: {user_id}")

    userid = user_api.get_load_sim_user(user_id)
    tear_d = userid["data"]["list"]
    logger.info(f"用户下所有车组信息: {tear_d}")
    logger.info(f"查找删除车组名: {case_datas}")

    group_id = find_group_by_name(tear_d, case_datas)
    clear_id = group_id["groupId"]
    logger.info(f"获取待删除车组ID: {clear_id}")
    if clear_id:
        try:
            vehicle_api.delete_group(clear_id)
            logger.info(f"teardown 清理成功，group_id={clear_id}")
        except Exception as e:
            logger.warning(f"teardown 清理失败，但不影响测试主结果: {e}")

@pytest.fixture(scope="function")
def clear_add_user(user_client, request):
    logger.info(f"新增用户前置执行")
    # 1、检查用户是否存在
    # 2、存在删除
    # 3、执行用例
    # 4、后置清理新增用户
    user_api = UserApi(user_client)
    name_id = user_api.get_user_tree()
    names = name_id["data"][0]["children"]
    logger.info(f"获取接口响应: {names}")

    params = request.node.callspec.params
    logger.info(f"新增用户参数 pre: {params}")
    key, case_data = next(iter(params.items()))
    case_datas = case_data['pre']
    is_name = find_user_by_name(names, case_datas)

    if is_name:
        logger.info(f"前置发现用户存在: {is_name}")
        user_id = is_name["id"]
        logger.info(f"删除用户ID>> : {user_id}")
        result = user_api.del_user(user_id)
        logger.info(f"新增用户前置删除: {result}")
    else:
        logger.info(f"新增用户前置用户空")

    yield
    name = user_api.get_user_tree()
    data_list = name["data"][0]["children"]
    # logger.info(f"新增用户后置用户树响应: {data_list}, 查找用户名: {case_datas}")
    find_name = find_user_by_name(data_list, case_datas)
    del_user_id = find_name["id"]
    # logger.info(f"新增用户后置用户树结果集: {find_name}, 删除用户ID: {del_user_id}")
    user_api.del_user(del_user_id)


@pytest.fixture(scope="function")
def setup_user_add(user_client, request):
    logger.info(f"删除用户前置处理器")
    # 前置 确保删除用户存在，不存在需要添加，
    # 后置重新检查用户是否删除
    user_api = UserApi(user_client)

    params = request.node.callspec.params
    logger.info(f"删除用户参数 pre: {params}")
    key, case_data = next(iter(params.items()))
    case_datas = case_data['pre']
    payloads = case_data['payload']

    logger.info(f"删除-新增用户名: {case_datas}")
    logger.info(f"删除-payloads: {payloads}")

    get_name = user_api.get_user_tree()
    names = get_name["data"][0]["children"]
    logger.info(f"前置-用户树接口响应: {names}")
    fin_name = find_user_by_name(names, case_datas)
    logger.info(f"前置-查找删除用户: {fin_name}")

    if fin_name is not None:
        pass
    else:
        pwd = cfg.aes_encrypt_like_cryptojs_ecb(payloads["password"])
        add_name = user_api.add_user(payloads["userName"], payloads["email"], pwd, payloads["phone"], user_client.userId)
        logger.info(f"前置新增用户: {add_name}")
    yield
    # 后置再检查一次用户是否已删除
    get_name = user_api.get_user_tree()
    names = get_name["data"][0]["children"]
    logger.info(f"后置-用户树接口响应: {names}")

    find_name = find_user_by_name(names, case_datas)
    logger.info(f"后置-查找用户结果: {find_name}")

    if find_name is not None:
        try:
            del_user_id = find_name["id"]
            logger.info(f"后置-查找待删除用户ID>> : {del_user_id}")

            user_api.del_user(del_user_id)
            logger.info(f"后置执行删除用户")
        except Exception as e:
            logger.error(f"后置删除用户执行异常: {e}")

@pytest.fixture(scope="function")
def teardown_update_user_info(user_client, request):
    logger.info(f"修改用户名-前置处理器")

    user_api = UserApi(user_client)

    # 先检查登录用户下是否存在 待修改用户
    params = request.node.callspec.params
    key, case_data = next(iter(params.items()))
    case_datas = case_data['pre']
    before_end = case_data["payload"]

    # logger.info(f"新增带修改用户-pre: {params}")
    pwd = cfg.aes_encrypt_like_cryptojs_ecb(case_datas["password"])

    get_user_tree = user_api.get_user_tree()
    # logger.info(f"step2-获取用户数: {get_user_tree}")

    user_tree = get_user_tree["data"][0]["children"]
    name = case_datas["userName"]
    find_name = find_user_by_name(user_tree, name)
    # print(f"step3-判断-用户是否存在: {find_name}, 查找用户名: {name}")
    try:
        if find_name is None:

            upd_add_user =  user_api.add_user(case_datas["userName"], case_datas["email"], pwd, case_datas["phone"], user_client.userId)
            new_name = upd_add_user["data"]["userName"]
            user_id = upd_add_user["data"]["userId"]
            logger.info(f"修改用户-新用户名: {new_name}, 用户ID>> : {user_id}")
    except Exception as e:
        logger.info(f"修改用户新增异常: {e}")

    yield

    # 测试修改用户名校验后，后置处理器还原用户名
    get_name = user_api.get_user_tree()
    names = get_name["data"][0]["children"]
    # logger.info(f"修改用户-获取用户数: {names}")

    find_name = find_user_by_name(names, before_end["userName"])
    user_id2 = find_name['id']
    logger.info(f"后置-获取用户ID>> : {user_id2}")

    del_user = user_api.del_user(user_id2)
    logger.info(f"修改用户-后置删除用户: {del_user}")