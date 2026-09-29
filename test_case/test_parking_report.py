# -*- coding: UTF-8 -*-
import json
import allure
import pytest
from base.redConfig import Config
from base.utils import allure_attach_comparison
from profes.alarm_report import AlarmReport

cfg = Config()

# 官方文档定义 /parkingReport/list 响应 data[] 中每条记录应包含的结构字段
PARKING_DATA_KEYS = {
    "deviceName", "deviceId", "deviceType",
    "group", "startTime", "endTime"
}


def _device_id(case):
    """payload.device_id 可能配置成字符串或单元素列表，统一取成字符串。"""
    dv = case.get("payload", {}).get("device_id", "")
    if isinstance(dv, list):
        dv = dv[0] if dv else ""
    return dv


@allure.epic("停车报表")
@allure.feature("查询停车记录")
@pytest.mark.parametrize(
    "get_parking_records",
    cfg.get_cases_by_interface("parking_records", "get_parking_records")
)
def test_get_parking_records(user_client, get_parking_records):
    allure.dynamic.title(get_parking_records["case_name"])  # 在报告左侧显示具体的用例名
    allure.dynamic.description(
        f"预期校验点：{get_parking_records['expect_code']} / {get_parking_records['expect_msg']}"
    )
    device_id = _device_id(get_parking_records)

    parking_api = AlarmReport(user_client)
    result = parking_api.get_parking_report_list(device_id)

    # 关键：附件对比必须用「真实响应」vs「预期」，不能拿预期比预期（假绿）
    actual_code = result.get("code")
    actual_msg = result.get("msg")
    actual_data = result.get("data", [])

    allure_attach_comparison(
        expected=get_parking_records["expect_code"], actual=actual_code, name="响应状态码"
    )
    allure_attach_comparison(
        expected=get_parking_records["expect_msg"], actual=actual_msg, name="响应消息状态"
    )

    # 失败时把完整响应打到断言信息里，方便直接看到服务端真实报错
    assert actual_code == get_parking_records["expect_code"], \
        f"[{get_parking_records['case_name']}] 返回码异常: 期望 {get_parking_records['expect_code']}, " \
        f"实际 {actual_code}, 响应={json.dumps(result, ensure_ascii=False)[:1500]}"
    assert actual_msg == get_parking_records["expect_msg"], \
        f"[{get_parking_records['case_name']}] 返回消息异常: 期望 {get_parking_records['expect_msg']}, 实际 {actual_msg}"

    # 若接口返回了数据，校验每条记录结构符合官方文档契约（避免返回结构偷偷变化而用例仍绿）
    for idx, item in enumerate(actual_data):
        missing = PARKING_DATA_KEYS - item.keys()
        assert not missing, \
            f"[{get_parking_records['case_name']}] 第{idx}条记录缺少字段 {missing}, " \
            f"实际={json.dumps(item, ensure_ascii=False)[:500]}"
