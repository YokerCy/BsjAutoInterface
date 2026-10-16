# -*- coding: UTF-8 -*-
"""
价格单车油耗分析表接口封装（平台私有接口，走 webapi/，用 send_by_key）

接口：POST /oil/vehicleFuel
抓包来源：
  https://ytest.gpstracktech.com/webapi/oil/vehicleFuel
      ?__sm_ver=1.28.9-beta.1,20261015162519&platform=PC&version=base

请求体字段（来自实际抓包）：
  userId     -> number  用户ID，如 241
  vehicleId  -> number  车辆ID，如 89641
  startTime  -> string  yyyy-MM-dd HH:mm:ss
  endTime    -> string  yyyy-MM-dd HH:mm:ss
  clientTime -> string  yyyy-MM-dd HH:mm:ss，客户端发起时刻
  unitPrice  -> number  油价单价（元/L），如 1

注意：
  __sm_ver / platform / version 三个 query 参数由 send_by_key 自动合并
  common_params 注入，业务层不需要也不应该自己传，避免覆盖全局版本号。
"""
from datetime import datetime


def _now_str():
    """当前时间，格式 yyyy-MM-dd HH:mm:ss"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class OilReport:
    def __init__(self, client):
        self.client = client

    def get_vehicle_fuel(
        self,
        user_id,
        vehicle_id,
        start_time,
        end_time,
        unit_price=1,
        client_time=None,
    ):
        """
        获取价格单车油耗分析表

        :param user_id:    用户ID，如 241。传 None 则自动取当前登录用户ID
                           （实测登录返回的 userId 正是 241，用动态值可避免换账号后失效）
        :param vehicle_id: 车辆ID（数字），如 89641
        :param start_time: 开始时间 "yyyy-MM-dd HH:mm:ss"
        :param end_time:   结束时间 "yyyy-MM-dd HH:mm:ss"
        :param unit_price: 油价单价（元/L），默认 1
        :param client_time: 客户端时间，不传则自动取当前时间。
                            语义上是「发起请求的时刻」，写死会在日后运行中失真，
                            故默认动态取当前时间；如需复现抓包可显式传入。
        """
        if user_id is None:
            # user_client 登录后会写入 userId；api_client 没有该属性，取不到时报错提示
            user_id = getattr(self.client, "userId", None)
            if user_id is None:
                raise ValueError(
                    "user_id 未传且无法从 client 获取（client.userId 不存在），"
                    "请显式传入 user_id"
                )

        res = self.client.send_by_key(
            "POST",
            "oil_vehicle_fuel",
            json={
                "userId": user_id,
                "vehicleId": vehicle_id,
                "startTime": start_time,
                "endTime": end_time,
                "clientTime": client_time or _now_str(),
                "unitPrice": unit_price,
            },
        )
        return res.json()
