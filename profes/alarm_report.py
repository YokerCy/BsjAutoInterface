# -*- coding: UTF-8 -*-
from datetime import datetime, timedelta

# 先注释，后续会造数据了，再传最近7天的值
# def _recent_range(days=7):
#     """返回 (start_time, end_time)，默认取最近 7 天，与历史轨迹巡检窗口一致。
#     避免把日期写死导致每日巡检永远查同一个历史窗口（会被数据衰减成空 / 假红）。"""
#     now = datetime.now()
#     end_time = now.strftime("%Y-%m-%d 23:59:59")
#     start_time = (now - timedelta(days=days)).strftime("%Y-%m-%d 00:00:00")
#     return start_time, end_time




class AlarmReport:
    def __init__(self, client):
        self.client = client

    # 获取报警类型
    def get_alarm_type(self):
        res = self.client.send_by_key(
            "GET",
            "get_alarm_type",
            json={"type": "0"}
        )
        return res.json()

    # 依据 /alarm/getAlarmInfo 官方文档：
    #   ids        -> number[]  必填，告警类型ID，示例 [17]（注意是数字不是字符串）
    #   queryParams-> string[]  必填，设备名/设备ID，示例 ["authTest1"]（数组）
    #   queryType  -> 0 按设备名 / 1 按设备ID
    #   startTime/endTime -> yyyy-MM-dd HH:mm:ss
    # startTime和endTime先写死，后续会造数据了，再传最近7天的值
    # 获取报警数据
    def get_alarm_message(self, device_id):
        # start_time, end_time = _recent_range()
        res = self.client.send_api(
            "POST",
            "alarm_info",
            json={
                "ids": [25],
                "pageNumber": 1,
                "pageSize": 10,
                "queryParams": [device_id],
                "queryType": 0,
                "startTime": "2026-09-18 00:00:00",
                "endTime": "2026-09-18 23:59:59",
            }
        )
        return res.json()

    # 获取ai报警数据
    def get_ai_event_alarm_message(self, device_id):
        # start_time, end_time = _recent_range()
        res = self.client.send_api(
            "POST",
            "ai_event_alarm_info",
            json={
                "ids": [206],
                "pageNumber": 1,
                "pageSize": 10,
                "queryParams": [device_id],
                "queryType": 0,
                # "startTime": start_time,
                # "endTime": end_time
                "startTime": "2026-09-18 00:00:00",
                "endTime": "2026-09-18 23:59:59",
            }
        )
        return res.json()

    # 获取常规告警
    def get_general_alarm_message(self, device_id):
        # start_time, end_time = _recent_range()
        res = self.client.send_api(
            "POST",
            "get_general_alarm",
            json={
                "ids": 25,
                "pageNumber": 1,
                "pageSize": 10,
                "queryParams": [device_id],
                "queryType": 0,
                # "startTime": start_time,
                # "endTime": end_time
                "startTime": "2026-09-18 00:00:00",
                "endTime": "2026-09-18 23:59:59",
            }
        )
        return res.json()

    # 获取停车报表（POST /parkingReport/list）
    # 依据官方文档：
    #   queryParams -> string[]（设备名/设备ID，按列表传入）
    #   queryType   -> 0 按设备名 / 1 按设备ID
    #   startTime/endTime -> yyyy-MM-dd HH:mm:ss
    #   pageNumber/pageSize -> 分页（默认 1 / 50）
    # 注意：停车报表接口没有 ids 字段，原 stub 误带了 ids=ALARM_IDS，已移除。
    # startTime和endTime先写死，后续会造数据了，再传最近7天的值
    def get_parking_report_list(self, device_id):
        res = self.client.send_api(
            "POST",
            "parking_record",
            json={
                "startTime": "2026-09-18 00:00:00",
                "endTime": "2026-09-18 23:59:59",
                "pageNumber": 0,
                "pageSize": 10,
                "queryParams": [device_id],
                "queryType": 1
            }
        )
        return res.json()

    #获取里程报表
    def get_mileage_report_message(self, device_id):
        # start_time, end_time = _recent_range()
        res = self.client.send_api(
            "POST",
            "mileage_report",
            json={
                "pageNumber": 1,
                "pageSize": 10,
                "queryParams": [device_id],
                "queryType": 0,
                # "startTime": start_time,
                # "endTime": end_time
                "startTime": "2026-09-18 00:00:00",
                "endTime": "2026-09-18 23:59:59",
            }
        )
        return res.json()
