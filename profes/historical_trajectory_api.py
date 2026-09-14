# -*- coding: UTF-8 -*-
'''
@Time    : 2026/6/1 10:52
@Author  : Yoker
@File    : historical_trajectory_api.py
@Project : smart_auto_interface
@Depict    : 历史轨迹
'''

from datetime import datetime, timedelta


class HistoricalTrajectoryApi:
    def __init__(self, client):
        self.client = client

    def get_query_device_historical_trajectory(self):
        """查询设备历史轨迹封装（动态取最近7天，避免硬编码导致巡检长期查同一时间窗）"""
        now = datetime.now()
        begin_time = (now - timedelta(days=6)).strftime("%Y-%m-%d 00:00:00")
        end_time = now.strftime("%Y-%m-%d 23:59:59")
        res = self.client.send_api(
            "GET",
            "historical_trajectory",
            params={
                "filterTime": 0,
                "stopStatus": 1,
                "posStatus": 0,
                "queryType": 0,
                "queryParam": "15900000070",
                "beginTime": begin_time,
                "endTime": end_time,
            },
        )
        return res.json()

    def real_time_location(self):
        """检索设备的最新实时位置和状态信息封装"""
        res = self.client.send_api(
            "POST",
            "real_time_location_api",
            params={
                "queryType": "1",
                "queryParams": ["15900000070"],
            },
        )
        return res.json()
