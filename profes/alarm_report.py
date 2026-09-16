# -*- coding: UTF-8 -*-
from datetime import datetime, timedelta


def _recent_range(days=7):
    """返回 (start_time, end_time)，默认取最近 7 天，与历史轨迹巡检窗口一致。
    避免把日期写死导致每日巡检永远查同一个历史窗口（会被数据衰减成空 / 假红）。"""
    now = datetime.now()
    end_time = now.strftime("%Y-%m-%d 23:59:59")
    start_time = (now - timedelta(days=days)).strftime("%Y-%m-%d 00:00:00")
    return start_time, end_time


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

    # 获取报警数据
    def get_alarm_message(self, device_id):
        start_time, end_time = _recent_range()
        res = self.client.send_api(
            "POST",
            "alarm_info",
            json={
                "ids": ["21",
                        "33"],
                "pageNumber": 1,
                "pageSize": 10,
                "queryParams": device_id,
                "queryType": 0,
                "startTime": start_time,
                "endTime": end_time
            }
        )
        # 调试：查看实际响应内容
        # print("Status Code:", res.status_code)
        # print("Response Text:", res.text)  # 查看为什么无法解析为 JSON
        return res.json()

        # 获取ai报警数据
    def get_ai_event_alarm_message(self, device_id):
        start_time, end_time = _recent_range()
        res = self.client.send_api(
            "POST",
            "ai_event_alarm_info",
            json={
                "ids": ["21",
                        "33"],
                "pageNumber": 1,
                "pageSize": 10,
                "queryParams": device_id,
                "queryType": 0,
                "startTime": start_time,
                "endTime": end_time
            }
        )
        # 调试：查看实际响应内容
        # print("Status Code:", res.status_code)
        # print("Response Text:", res.text)  # 查看为什么无法解析为 JSON
        return res.json()

        # 获取常规告警
    def get_general_alarm_message(self, device_id):
        start_time, end_time = _recent_range()
        res = self.client.send_api(
            "POST",
            "get_general_alarm",
            json={
                "ids": ["21",
                        "33"],
                "pageNumber": 1,
                "pageSize": 10,
                "queryParams": device_id,
                "queryType": 0,
                "startTime": start_time,
                "endTime": end_time
            }
        )
        # 调试：查看实际响应内容
        # print("Status Code:", res.status_code)
        # print("Response Text:", res.text)  # 查看为什么无法解析为 JSON
        return res.json()

    #获取停车报表
    def get_parking_report_list(self, device_id):
        start_time, end_time = _recent_range()
        res = self.client.send_api(
            "POST",
            "parking_record",
            json={
                "ids": ["21",
                        "33"],
                "pageNumber": 1,
                "pageSize": 10,
                "queryParams": device_id,
                "queryType": 0,
                "startTime": start_time,
                "endTime": end_time
            }
        )
        # 调试：查看实际响应内容
        # print("Status Code:", res.status_code)
        # print("Response Text:", res.text)  # 查看为什么无法解析为 JSON
        return res.json()

    #获取里程报表
    def get_mileage_report_message(self, device_id):
        start_time, end_time = _recent_range()
        res = self.client.send_api(
            "POST",
            "mileage_report",
            json={
                "pageNumber": 1,
                "pageSize": 10,
                "queryParams": device_id,
                "queryType": 0,
                "startTime": start_time,
                "endTime": end_time
            }
        )
        # 调试：查看实际响应内容
        # print("Status Code:", res.status_code)
        # print("Response Text:", res.text)  # 查看为什么无法解析为 JSON
        return res.json()
