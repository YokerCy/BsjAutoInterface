import allure
import pytest
from base.redConfig import Config
from base.utils import allure_attach_comparison
from profes.alarm_report import AlarmReport

cfg = Config()

@allure.epic("告警报表")
@allure.feature("告警查询模块")
@pytest.mark.parametrize(
    "get_alarm_type",
    cfg.get_cases_by_interface("alarm_report","get_alarm_type")
)
def test_get_alarm_type(user_client, get_alarm_type):
    allure.dynamic.title(get_alarm_type["case_name"]) #在报告左侧显示具体的用例名
    allure.dynamic.description(f"预期校验点：{get_alarm_type["expect_code"]} / {get_alarm_type['expect_msg']}")

    alarm_report_api = AlarmReport(user_client)
    alarm_type = alarm_report_api.get_alarm_type()

    code = get_alarm_type["expect_code"]
    msg = get_alarm_type["expect_msg"]
    quantity = get_alarm_type["quantity"]

    allure_attach_comparison(expected=get_alarm_type["expect_code"], actual=code, name="响应状态码")
    allure_attach_comparison(expected=get_alarm_type["expect_msg"], actual=msg, name="响应消息状态")
    allure_attach_comparison(expected=get_alarm_type["quantity"], actual=quantity, name="响应消息状态")

    # 调试：打印实际返回的内容
    # print(f"API返回类型: {type(alarm_type)}")
    # print(f"API返回完整内容: {alarm_type}")
    # print(f"所有可用键: {list(alarm_type.keys())}")

    # # 如果存在嵌套结构，进一步查看
    # if isinstance(alarm_type, dict):
    #     for key, value in alarm_type.items():
    #         print(f"键 '{key}' 的类型: {type(value)}, 值: {str(value)[:200]}")

    assert alarm_type["code"] == code

    get_msg = alarm_type.get("msg")
    assert get_msg == msg

    assert len(alarm_type["data"]) >= quantity

@allure.epic("告警报表")
@allure.feature("查询告警信息")
@pytest.mark.parametrize(
    "get_alarm_information",
    cfg.get_cases_by_interface("alarm_report","get_alarm_information")
)
def test_get_ai_event_information(user_client, get_alarm_information):
    allure.dynamic.title(get_alarm_information["case_name"])  # 在报告左侧显示具体的用例名
    allure.dynamic.description(f"预期校验点：{get_alarm_information["expect_code"]} / {get_alarm_information['expect_msg']}")
    device_id = get_alarm_information["payload"]["device_id"]

    alarm_report_api = AlarmReport(user_client)
    alarm_information = alarm_report_api.get_alarm_message(device_id)

    code = get_alarm_information["expect_code"]
    msg = get_alarm_information["expect_msg"]


    allure_attach_comparison(expected=get_alarm_information["expect_code"], actual=code, name="响应状态码")
    allure_attach_comparison(expected=get_alarm_information["expect_msg"], actual=msg, name="响应消息状态")

    # # 检查响应是否包含错误信息
    # if "status" in alarm_information and alarm_information["status"] == 404:
    #     print(f"API返回404: {alarm_information['error']}, 路径: {alarm_information['path']}")
    #     # 根据测试策略，可以选择跳过或标记为失败
    #     pytest.fail(f"API返回404错误: {alarm_information['error']}")

    # 如果正常响应，则进行正常断言
    code = alarm_information.get("code")
    assert code == get_alarm_information["expect_code"]

    get_msg = alarm_information.get("msg")
    print(f"返回的消息为：:{get_msg}")

