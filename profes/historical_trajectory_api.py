# # -*- coding: UTF-8 -*-
# '''
# @Time    : 2026/6/1 10:52
# @Author  : Yoker
# @File    : historical_trajectory_api.py
# @Project : smart_auto_interface
# @Depict    : 历史轨迹
# '''

#
#
class HistoricalTrajectoryApi:
    def __init__(self, client):
        self.client = client

    def get_query_device_historical_trajectory(self):
        """查询设备历史轨迹封装"""
        # 调用conftest 里的基础方法发送请求
        res = self.client.send_api(
            "GET",
            "historical_trajectory",
            params={
                "filterTime": 0,
                "stopStatus": 1,
                "posStatus": 0,
                "queryType": 0,
                "queryParam": "15900000070",
                "beginTime": "2026-03-17 00:00:00",
                "endTime": "2026-03-18 01:00:00"
        })
        return res.json()

    def real_time_location(self):
        """检索设备的最新实时位置和状态信息封装"""
        res = self.client.send_api(
            "POST",
            "real_time_location",
            params = {
                "queryType": "1",
                "queryParams":["15900000070"]
            }
        )
        return res.json()