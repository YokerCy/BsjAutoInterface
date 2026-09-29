# -*- coding: UTF-8 -*-
'''
@Time    : 2026/6/1 10:52
@Author  : Yoker
@File    : historical_trajectory_api.py
@Project : smart_auto_interface
@Depict    : 历史轨迹
'''

from datetime import datetime, timedelta


def _recent_range(days=7):
    """返回 (begin, end) 最近 N 天窗口，用于替代硬编码日期做每日巡检。"""
    now = datetime.now()
    end_time = now.strftime("%Y-%m-%d %H:%M:%S")
    start_time = (now - timedelta(days=days - 1)).strftime("%Y-%m-%d 00:00:00")
    return start_time, end_time


class HistoricalTrajectoryApi:
    def __init__(self, client):
        self.client = client

    def get_query_device_historical_trajectory(
            self,
            query_param="15900000070",
            query_type=0,
            begin_time="2026-09-28 00:00:00",
            end_time="2026-09-28 23:59:59",
            filter_time=0,
            stop_status=1,
            pos_status=0,
    ):
        """
        查询设备历史轨迹（GET /track/getTrackList）

        参数含义依据官方文档：
          filterTime : number 必填  停车时间过滤，单位分钟
          stopStatus : number 必填  0: 过滤停车数据   1: 不过滤
          posStatus  : number 必填  0: 仅已定位  1: 全部（含未定位）  2: 仅未定位
          queryType  : number 必填  0: 按设备名(plate)   1: 按设备ID(terminalNo)
          queryParam : string 必填  设备名或设备ID

        ⚠️ 11 位纯数字通常是 terminalNo（设备ID），应配 query_type=1；
           若配成 0（按设备名）会匹配不到设备，服务端返回 code=200 + msg="No Data"。
        ⚠️ 限流：该接口单用户每分钟最多调用 2 次，超限会被限流。
        """
        res = self.client.send_api(
            "GET",
            "historical_trajectory",
            params={
                "filterTime": filter_time,
                "stopStatus": stop_status,
                "posStatus": pos_status,
                "queryType": query_type,
                "queryParam": query_param,
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
