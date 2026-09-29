# -*- coding: UTF-8 -*-
import json
import allure
import pytest
from base.redConfig import Config
from base.utils import allure_attach_comparison
from profes.alarm_report import AlarmReport

cfg = Config()


def _device_id(case):
    """payload.device_id 可能配置成字符串或单元素列表，统一取成字符串。
    注意：之前 yaml 里写成列表 ["15900000070"]，会被原样发给服务端导致 queryParams 变成数组 -> 500。"""
    dv = case.get("payload", {}).get("device_id", "")
    if isinstance(dv, list):
        dv = dv[0] if dv else ""
    return dv


@allure.epic("告警报表")
@allure.feature("告警查询模块")
@pytest.mark.parametrize(
    "get_alarm_type",
    cfg.get_cases_by_interface("alarm_report", "get_alarm_type")
)
def test_get_alarm_type(user_client, get_alarm_type):
    allure.dynamic.title(get_alarm_type["case_name"])  # 在报告左侧显示具体的用例名
    allure.dynamic.description(f"预期校验点：{get_alarm_type['expect_code']} / {get_alarm_type['expect_msg']}")

    alarm_report_api = AlarmReport(user_client)
    alarm_type = alarm_report_api.get_alarm_type()

    # 关键：附件对比必须用「真实响应」vs「预期」，不能拿预期比预期（假绿）
    actual_code = alarm_type.get("code")
    actual_msg = alarm_type.get("msg")
    actual_data = alarm_type.get("data", [])

    allure_attach_comparison(expected=get_alarm_type["expect_code"], actual=actual_code, name="响应状态码")
    allure_attach_comparison(expected=get_alarm_type["expect_msg"], actual=actual_msg, name="响应消息状态")

    assert actual_code == get_alarm_type["expect_code"], \
        f"[{get_alarm_type['case_name']}] 返回码异常: 期望 {get_alarm_type['expect_code']}, 实际 {actual_code}, 响应={json.dumps(alarm_type, ensure_ascii=False)[:1500]}"
    assert actual_msg == get_alarm_type["expect_msg"], \
        f"[{get_alarm_type['case_name']}] 返回消息异常: 期望 {get_alarm_type['expect_msg']}, 实际 {actual_msg}"
    assert len(actual_data) >= get_alarm_type.get("quantity", 1), \
        f"[{get_alarm_type['case_name']}] 数据量不足: 期望 >= {get_alarm_type.get('quantity', 1)}, 实际 {len(actual_data)}"


@allure.epic("获取常规告警")
@allure.feature("查询获取常规告警")
@pytest.mark.parametrize(
    "get_alarm_information",
    cfg.get_cases_by_interface("alarm_report", "get_alarm_information")
)
def test_get_alarm_informationn(user_client, get_alarm_information):
    # 获取告警信息
    allure.dynamic.title(get_alarm_information["case_name"])  # 在报告左侧显示具体的用例名
    allure.dynamic.description(f"预期校验点：{get_alarm_information['expect_code']} / {get_alarm_information['expect_msg']}")
    device_id = _device_id(get_alarm_information)

    alarm_report_api = AlarmReport(user_client)
    alarm_information = alarm_report_api.get_alarm_message(device_id)

    actual_code = alarm_information.get("code")
    actual_msg = alarm_information.get("msg")

    allure_attach_comparison(expected=get_alarm_information["expect_code"], actual=actual_code, name="响应状态码")
    allure_attach_comparison(expected=get_alarm_information["expect_msg"], actual=actual_msg, name="响应消息状态")

    # 失败时把完整响应打到断言信息里，方便直接看到服务端真实报错（如 queryParams 类型错误）
    assert actual_code == get_alarm_information["expect_code"], \
        f"[{get_alarm_information['case_name']}] 返回码异常: 期望 {get_alarm_information['expect_code']}, 实际 {actual_code}, 响应={json.dumps(alarm_information, ensure_ascii=False)[:1500]}"
    assert actual_msg == get_alarm_information["expect_msg"], \
        f"[{get_alarm_information['case_name']}] 返回消息异常: 期望 {get_alarm_information['expect_msg']}, 实际 {actual_msg}"


@allure.epic("AI告警")
@allure.feature("查询AI告警信息")
@pytest.mark.parametrize(
    "get_ai_event_alarm",
    cfg.get_cases_by_interface("alarm_report", "get_ai_event_alarm")
)
def test_get_ai_event_alarm_information(user_client, get_ai_event_alarm):
    # 获取ai告警信息
    allure.dynamic.title(get_ai_event_alarm["case_name"])  # 在报告左侧显示具体的用例名
    allure.dynamic.description(f"预期校验点：{get_ai_event_alarm['expect_code']} / {get_ai_event_alarm['expect_msg']}")
    device_id = _device_id(get_ai_event_alarm)

    alarm_report_api = AlarmReport(user_client)
    general_alarm = alarm_report_api.get_ai_event_alarm_message(device_id)

    actual_code = general_alarm.get("code")
    actual_msg = general_alarm.get("msg")

    allure_attach_comparison(expected=get_ai_event_alarm["expect_code"], actual=actual_code, name="响应状态码")
    allure_attach_comparison(expected=get_ai_event_alarm["expect_msg"], actual=actual_msg, name="响应消息状态")

    # 注意：原先错误地用响应体 general_alarm["expect_code"] 做断言（响应里没有该字段，会 KeyError）
    assert actual_code == get_ai_event_alarm["expect_code"], \
        f"[{get_ai_event_alarm['case_name']}] 返回码异常: 期望 {get_ai_event_alarm['expect_code']}, 实际 {actual_code}, 响应={json.dumps(general_alarm, ensure_ascii=False)[:1500]}"
    assert actual_msg == get_ai_event_alarm["expect_msg"], \
        f"[{get_ai_event_alarm['case_name']}] 返回消息异常: 期望 {get_ai_event_alarm['expect_msg']}, 实际 {actual_msg}"


@allure.epic("里程报表")
@allure.feature("查询里程报表信息")
@pytest.mark.parametrize(
    "get_mileage_report",
    cfg.get_cases_by_interface("alarm_report", "get_mileage_report")
)
def test_get_mileage_report_message(user_client, get_mileage_report):
    # 里程报表
    allure.dynamic.title(get_mileage_report["case_name"])  # 在报告左侧显示具体的用例名
    allure.dynamic.description(f"预期校验点：{get_mileage_report['expect_code']} / {get_mileage_report['expect_msg']}")
    device_id = _device_id(get_mileage_report)

    alarm_report_api = AlarmReport(user_client)
    mileage_report = alarm_report_api.get_mileage_report_message(device_id)

    actual_code = mileage_report.get("code")
    actual_msg = mileage_report.get("msg")

    allure_attach_comparison(expected=get_mileage_report["expect_code"], actual=actual_code, name="响应状态码")
    allure_attach_comparison(expected=get_mileage_report["expect_msg"], actual=actual_msg, name="响应消息状态")

    # 注意：原先 assert code == mileage_report["code"] 是自比，恒为通过（假绿）
    assert actual_code == get_mileage_report["expect_code"], \
        f"[{get_mileage_report['case_name']}] 返回码异常: 期望 {get_mileage_report['expect_code']}, 实际 {actual_code}, 响应={json.dumps(mileage_report, ensure_ascii=False)[:1500]}"
    assert actual_msg == get_mileage_report["expect_msg"], \
        f"[{get_mileage_report['case_name']}] 返回消息异常: 期望 {get_mileage_report['expect_msg']}, 实际 {actual_msg}"
