# -*- coding: UTF-8 -*-
"""
温湿度报表接口封装（平台私有接口，走 webapi/，用 send_by_key）

接口：POST /tempHumidityReport/getTempHumidityReport
抓包来源：
  https://ytest.gpstracktech.com/webapi/tempHumidityReport/getTempHumidityReport
      ?__sm_ver=1.28.9-beta.1,20261015162519&platform=PC&version=base

请求体字段（来自实际抓包）：
  pageNum    -> number   页码，从 1 开始（注意本接口是 pageNum，不是别的报表的 pageNumber）
  pageSize   -> number   每页条数，如 20
  startTime  -> string   yyyy-MM-dd HH:mm:ss
  endTime    -> string   yyyy-MM-dd HH:mm:ss
  vehicleIds -> number[] 车辆ID数组（数字，不是设备号字符串）

注意：
  __sm_ver / platform / version 三个 query 参数由 send_by_key 自动合并
  common_params 注入，业务层不需要也不应该自己传，避免覆盖全局版本号。
"""


class TempHumidityReport:
    def __init__(self, client):
        self.client = client

    # ---------------- 列表：温湿度报表 ----------------
    def get_temp_humidity_report(
        self,
        vehicle_ids,
        start_time,
        end_time,
        page_num=1,
        page_size=20,
    ):
        """
        获取温湿度报表（分页列表）

        :param vehicle_ids: 车辆ID，数字或数字列表，如 89641 / [89641]
        :param start_time: 开始时间 "yyyy-MM-dd HH:mm:ss"
        :param end_time:   结束时间 "yyyy-MM-dd HH:mm:ss"
        :param page_num:   页码，从 1 开始（默认 1）
        :param page_size:  每页条数（默认 20）
        """
        # 容错：yaml 里可能配成单个数字，统一成数组发给服务端
        if not isinstance(vehicle_ids, (list, tuple)):
            vehicle_ids = [vehicle_ids]

        res = self.client.send_by_key(
            "POST",
            "temp_humidity_report",
            json={
                "pageNum": page_num,
                "pageSize": page_size,
                "startTime": start_time,
                "endTime": end_time,
                "vehicleIds": list(vehicle_ids),
            },
        )
        return res.json()
