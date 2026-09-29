# -*- coding: UTF-8 -*-
"""
行程分析接口封装（平台私有接口，走 webapi/，用 send_by_key）

接口：POST /itineraryAnalysis/getItineraryAnalysisPageData
抓包来源：
  https://ytest.gpstracktech.com/webapi/itineraryAnalysis/getItineraryAnalysisPageData
      ?__sm_ver=1.28.7-beta.0,20260923102240&platform=PC&version=base

请求体字段（来自实际抓包）：
  vehicleIds   -> number[]  必填，车辆ID（数字，不是设备号字符串）
  startTime    -> string    yyyy-MM-dd HH:mm:ss
  endTime      -> string    yyyy-MM-dd HH:mm:ss
  filterStatus -> number    0 = 全部（沿用抓包值）

注意：
  __sm_ver / platform / version 三个 query 参数由 send_by_key 自动合并
  common_params 注入，业务层不需要也不应该自己传，避免覆盖全局版本号。
"""


class ItineraryAnalysis:
    def __init__(self, client):
        self.client = client

    def get_itinerary_analysis_page_data(
        self,
        vehicle_ids,
        start_time,
        end_time,
        filter_status=0,
    ):
        """
        获取行程分析分页数据

        :param vehicle_ids: 车辆ID，数字或数字列表，如 89641 / [89641]
        :param start_time: 开始时间 "yyyy-MM-dd HH:mm:ss"
        :param end_time:   结束时间 "yyyy-MM-dd HH:mm:ss"
        :param filter_status: 筛选状态，默认 0（全部）
        """
        # 容错：yaml 里可能配成单个数字，统一成数组发给服务端
        if not isinstance(vehicle_ids, (list, tuple)):
            vehicle_ids = [vehicle_ids]

        res = self.client.send_by_key(
            "POST",
            "itinerary_analysis",
            json={
                "vehicleIds": list(vehicle_ids),
                "startTime": start_time,
                "endTime": end_time,
                "filterStatus": filter_status,
            },
        )
        return res.json()
