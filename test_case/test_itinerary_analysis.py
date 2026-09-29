# -*- coding: UTF-8 -*-
import json
import allure
import pytest
from base.redConfig import Config
from base.utils import allure_attach_comparison
from profes.itinerary_analysis import ItineraryAnalysis

cfg = Config()

# 实际返回结构（抓包实测）：
#   data = {
#     "hasData":   [{"vehicleId": 89641, "plate": "...", "terminalNo": "...",
#                    "groupId": 390, "plateColor": "yellow"}],
#     "emptyData": null
#   }
# 注意：hasData 是「在该时间段内**有行程数据**的车辆清单」，
#       不是行程明细列表 —— 契约校验按这个真实结构来，别再拍脑袋猜。
VEHICLE_ITEM_KEYS = {"vehicleId", "plate", "terminalNo"}


def _vehicle_ids(case):
    """payload.vehicle_ids 支持单个数字或数组，统一成列表。"""
    v = case.get("payload", {}).get("vehicle_ids", [])
    if not isinstance(v, list):
        v = [v]
    return v


@allure.epic("行程分析")
@allure.feature("查询行程分析分页数据")
@pytest.mark.parametrize(
    "get_itinerary_analysis",
    cfg.get_cases_by_interface("itinerary_analysis", "get_itinerary_analysis_page_data")
)
def test_get_itinerary_analysis_page_data(user_client, get_itinerary_analysis):
    allure.dynamic.title(get_itinerary_analysis["case_name"])
    allure.dynamic.description(
        f"预期校验点：{get_itinerary_analysis['expect_code']} / {get_itinerary_analysis['expect_msg']}"
    )

    payload = get_itinerary_analysis.get("payload", {})
    vehicle_ids = _vehicle_ids(get_itinerary_analysis)

    itinerary_api = ItineraryAnalysis(user_client)
    result = itinerary_api.get_itinerary_analysis_page_data(
        vehicle_ids=vehicle_ids,
        start_time=payload.get("startTime"),
        end_time=payload.get("endTime"),
        filter_status=payload.get("filterStatus", 0),
    )

    actual_code = result.get("code")
    actual_msg = result.get("msg")
    actual_data = result.get("data") or {}

    allure_attach_comparison(
        expected=get_itinerary_analysis["expect_code"], actual=actual_code, name="响应状态码"
    )
    allure_attach_comparison(
        expected=get_itinerary_analysis["expect_msg"], actual=actual_msg, name="响应消息状态"
    )

    # 失败时把完整响应带进断言信息，直接看到服务端真实报错
    assert actual_code == get_itinerary_analysis["expect_code"], \
        f"[{get_itinerary_analysis['case_name']}] 返回码异常: " \
        f"期望 {get_itinerary_analysis['expect_code']}, 实际 {actual_code}, " \
        f"响应={json.dumps(result, ensure_ascii=False)[:1500]}"
    assert actual_msg == get_itinerary_analysis["expect_msg"], \
        f"[{get_itinerary_analysis['case_name']}] 返回消息异常: " \
        f"期望 {get_itinerary_analysis['expect_msg']}, 实际 {actual_msg}"

    # ---- 真正的契约校验（避免「只比码」的假绿） ----
    assert "hasData" in actual_data, \
        f"[{get_itinerary_analysis['case_name']}] 响应 data 缺少 hasData 字段, " \
        f"实际 data={json.dumps(actual_data, ensure_ascii=False)[:500]}"

    has_data = actual_data.get("hasData") or []
    assert isinstance(has_data, list), \
        f"[{get_itinerary_analysis['case_name']}] hasData 应为数组, 实际 {type(has_data).__name__}"

    # 1) 每条车辆记录的结构契约
    for idx, item in enumerate(has_data):
        missing = VEHICLE_ITEM_KEYS - set(item.keys())
        assert not missing, \
            f"[{get_itinerary_analysis['case_name']}] hasData 第{idx}条缺少字段 {missing}, " \
            f"实际={json.dumps(item, ensure_ascii=False)[:500]}"

    # 2) 业务有效性：请求的车辆应能在结果里被找到（真正证明「查得到」）
    #    若服务端返回 hasData 为空，说明该时间窗内确实无行程数据，
    #    这属于测试数据问题而非接口故障 —— 显式报出来，不要静默通过。
    returned_ids = {item.get("vehicleId") for item in has_data}
    for vid in vehicle_ids:
        assert vid in returned_ids, \
            f"[{get_itinerary_analysis['case_name']}] 请求车辆 {vid} 未出现在结果中 " \
            f"(hasData={returned_ids or '空'})，可能是该时间段无行程数据，请检查测试数据"
