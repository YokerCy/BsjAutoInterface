# -*- coding: UTF-8 -*-
"""
温湿度报表接口封装（平台私有接口，走 webapi/，用 send_by_key）

本模块含两个接口（注意两者的入参差异）：
  1) 列表：POST /tempHumidityReport/getTempHumidityReport
     请求体：pageNum / pageSize / startTime / endTime / vehicleIds[]   ← 车辆ID数组，无 userId
  2) 详情：POST /tempHumidityReport/getTempHumidityDetailReport
     请求体：userId / startTime / endTime / vehicleId(单个) / pageNum / pageSize

抓包来源取样：
  https://ytest.gpstracktech.com/webapi/tempHumidityReport/getTempHumidityReport
      ?__sm_ver=1.28.9-beta.1,20261015162519&platform=PC&version=base

注意：
  pageNum 是本模块两个接口的分页参数名（不是别的报表的 pageNumber）。
  __sm_ver / platform / version 三个 query 参数由 send_by_key 自动合并
  common_params 注入，业务层不需要也不应该自己传，避免覆盖全局版本号。
"""


def _resolve_user_id(client, user_id):
    """
    user_id 未传时自动取登录用户ID。

    user_client 登录后会写入 client.userId（本账号实测为 241）；
    api_client 没有该属性，取不到时明确报错而不是发出 userId=null 的请求。
    """
    if user_id is not None:
        return user_id
    resolved = getattr(client, "userId", None)
    if resolved is None:
        raise ValueError(
            "user_id 未传且无法从 client 获取（client.userId 不存在），请显式传入 user_id"
        )
    return resolved


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

    # ---------------- 详情：温湿度报表详情（单车） ----------------
    def get_temp_humidity_detail_report(
        self,
        vehicle_id,
        start_time,
        end_time,
        user_id=None,
        page_num=1,
        page_size=20,
    ):
        """
        获取温湿度报表详情（单车，分页）

        :param vehicle_id: 车辆ID（数字，**单个**，与列表接口的 vehicleIds 数组不同）
        :param start_time: 开始时间 "yyyy-MM-dd HH:mm:ss"
        :param end_time:   结束时间 "yyyy-MM-dd HH:mm:ss"
        :param user_id:    用户ID，传 None 则自动取当前登录用户ID（本账号实测为 241）
        :param page_num:   页码，从 1 开始（默认 1）
        :param page_size:  每页条数（默认 20）
        """
        res = self.client.send_by_key(
            "POST",
            "temp_humidity_detail_report",
            json={
                "userId": _resolve_user_id(self.client, user_id),
                "startTime": start_time,
                "endTime": end_time,
                "vehicleId": vehicle_id,
                "pageNum": page_num,
                "pageSize": page_size,
            },
        )
        return res.json()
