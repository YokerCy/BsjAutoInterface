# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/6 11:42 
@Author  : bo_god
@File    : vehicle_api.py
@Project : smart_auto_interface 
@Depict    :
'''
class VehicleApi:
    def __init__(self, client):
        self.client = client # 这里的 client 就是我们在 conftest 里的 user_client

    def add_vehicle(self, userId, groupId):
        """增加车辆接口封装"""
        # 从 yaml 模版获取 payload，并传入参数
        body = {
            "userId": userId,
            "groupId": groupId,
            "plate": "newAddVehicle",
            "vehicleType": 1,
            "sim": "",
            "terminalNo": "12322221111",
            "terminalType": "ED02R",
            "terminalTypeAlias": "ED02R",
            "cameraNum": 4,
            "cameraLine": "[1,2,3,4]",
            "onlineLink": "ytest.gpstracktech.com:7788",
            "messageTemplate": "<SPBSJ*P:BSJGPS*D:ytest.gpstracktech.com,7788>",
            "serviceCode": "",
            "remark": "",
            "locateMode": 0,
            "protocol": 1,
            "plateColor": "",
            "drivingLicense": "",
            "insuranceDueDate": "",
            "maintainDate": "",
            "driverName": "",
            "driverCard": "",
            "driverPhone": "",
            "driverGender": 0,
            "driverPicture": "",
            "driverRemark": "",
            "frameNo": "",
            "iconType": "1",
            "iccId": "",
            "imei": "",
            "trialPeriod": 0,
            "brand": "",
            "softWareVersion": "",
            "permission": "{\"speak\":true}",
            "vehicleTypeEnum": 1
        }
        # 调用 conftest 里的基础方法发送请求
        res = self.client.send_by_key("POST", "add_vehicle", json=body)
        return res.json()

    def delete_vehicle(self, vehicle_id):
        """删除车辆接口封装"""
        return self.client.send_by_key("GET",
                                       "vehicle_delete",
                                       params={"id": vehicle_id}
                                       )

    def add_group(self, userid, group_name, group_id):
        """
        新增车组
        :param userid: 用户ID
        :param group_name: 车组名称
        :param group_id: 车组ID 没有为空
        :return: JSON对象
        """
        res = self.client.send_by_key(
            "POST",
            "add_Group",
            json={
                "groupId": group_id,
                "userId": userid,
                "groupName": group_name,
                "email": "",
                "phone": "",
                "remark": "",
                "logo": ''
            }
        )
        return res.json()

    def get_group_one(self, group_id):
        """
        获取单个车组信息
        :param group_id:
        :return:
        """
        res = self.client.send_by_key("GET", "group_one", params={"groupId": group_id})
        return res.json()

    def delete_group(self, group_id):
        res = self.client.send_by_key(
            "GET",
            "delete_Group",
            params={"ids": group_id}
        )
        return res.json()

    def group_list(self, user_id):
        """
        用户下所属车组
        :param user_id:
        :return:
        """
        res = self.client.send_by_key("GET", "group_list", path_params={'userId': user_id})
        return res.json()

    def user_devices(self, user_id):
        """
        用户下所属车组和车辆信息
        :param user_id:
        :return:
        """
        res = self.client.send_by_key("GET", "user_device", path_params={'user_id': user_id})
        return res.json()


def find_group_by_name(data, target_name):
    """
    通过value反向查找所属对象
    数据源: /monitor/loadSimpleByUsers  object.['data']['list']
    :param data:
    :param target_name:
    :return: 返回对应的json对象
    {'groupId': 2250, 'userId': 241, 'groupName': 'addGoups', 'key': '2250', 'label': 'addGoups', 'value': '2250', 'children': []}
    """
    for index, group in enumerate(data):
        if group.get("groupName") == target_name:
            # return index, group   # 返回：位置 + 对应JSON
            return group
    return None

def find_user_by_name(data, target_name):
    """
    通过value反向查找所属对象
    数据源: /user/getUserTree  object.['data']['list']
    :param data:
    :param target_name:
    :return: 返回对应的json对象
    """
    for index, user in enumerate(data):
        if user.get("userName") == target_name:
            # return index, group   # 返回：位置 + 对应JSON
            return user
    return None


if __name__ == '__main__':
    temp = [
            {
                "groupId": 390,
                "userId": 241,
                "groupName": "DEFAULT_GROUP",
                "key": "390",
                "label": "DEFAULT_GROUP",
                "value": "390",
                "children": []
            },
            {
                "groupId": 489,
                "userId": 241,
                "groupName": "auto_分组",
                "key": "489",
                "label": "auto_分组",
                "value": "489",
                "children": [
                    {
                        "key": "489_27106",
                        "value": "489_27106",
                        "label": "qqw",
                        "plate": "qqw",
                        "vehicleId": 27106,
                        "groupId": 489,
                        "terminalNo": "11222111222",
                        "vehicleType": 1,
                        "expireDate": '',
                        "vehicleState": 3,
                        "posState": 5,
                        "terminalType": "ED02R",
                        "terminalTypeAlias": "ED02R",
                        "accState": 2,
                        "videoType": 1,
                        "vehicleTypeEnum": 1,
                        "lon": '',
                        "lat": '',
                        "direct": 0,
                        "speed": 0,
                        "terminalClassify": 1,
                        "attentionState": 0,
                        "cameraNum": 4,
                        "cameraLine": "[1,2,3,4]",
                        "iconType": '',
                        "protocol": 1
                    }
                ]
            },
            {
                "groupId": 2250,
                "userId": 241,
                "groupName": "addGoups",
                "key": "2250",
                "label": "addGoups",
                "value": "2250",
                "children": []
            }
        ]
    temp2 = [{'groupId': 2272, 'userId': 241, 'groupName': 'auto_车组', 'key': '2272', 'label': 'auto_车组', 'value': '2272', 'children': []}, {'groupId': 390, 'userId': 241, 'groupName': 'DEFAULT_GROUP', 'key': '390', 'label': 'DEFAULT_GROUP', 'value': '390', 'children': []}, {'groupId': 489, 'userId': 241, 'groupName': 'auto_分组', 'key': '489', 'label': 'auto_分组', 'value': '489', 'children': [{'key': '489_27106', 'value': '489_27106', 'label': 'qqw', 'plate': 'qqw', 'vehicleId': 27106, 'groupId': 489, 'terminalNo': '11222111222', 'vehicleType': 1, 'expireDate': None, 'vehicleState': 3, 'posState': 5, 'terminalType': 'ED02R', 'terminalTypeAlias': 'ED02R', 'accState': 2, 'videoType': 1, 'vehicleTypeEnum': 1, 'lon': None, 'lat': None, 'direct': 0, 'speed': 0.0, 'terminalClassify': 1, 'attentionState': 0, 'cameraNum': 4, 'cameraLine': '[1,2,3,4]', 'iconType': None, 'protocol': 1}]}]

    # print(find_group_by_name(data=temp2, target_name='auto_车组'))

    data = {'delete_group': {'case_name': '删除车组', 'interface': 'delete_group', 'expect_code': 200, 'expect_msg': 'Success', 'payload': {'group_name': 'auto_delete'}, 'pre_x': 'auto_delete'}}
    # key, case_data = next(iter(data.items()))
    # print(case_data, key)

    temp3 = [
    {
        "id": 98,
        "parentId": 4,
        "order": 101,
        "name": "testAlarm",
        "phone": '',
        "webUrl": '',
        "label": "testAlarm",
        "paymentLink": '',
        "userName": "testAlarm",
        "email": "",
        "children": [
            {
                "id": 369,
                "parentId": 98,
                "order": 0,
                "name": "444444",
                "phone": "1111111111111111",
                "webUrl": "",
                "label": "444444",
                "paymentLink": '',
                "userName": "444444",
                "email": ""
            },
            {
                "id": 334,
                "parentId": 98,
                "order": 104,
                "name": "zyh",
                "phone": '',
                "webUrl": "",
                "label": "zyh",
                "paymentLink": '',
                "userName": "zyh",
                "email": ""
            }
        ]
    }
]
    temp4 = [{'id': 241, 'parentId': 98, 'order': 1, 'name': 'youself', 'phone': None, 'webUrl': '9999999999999999999999999999999999999999999999999999999', 'label': 'youself', 'paymentLink': None, 'userName': 'youself', 'email': '', 'children': [{'id': 310, 'parentId': 241, 'order': 0, 'name': 'you2', 'phone': None, 'webUrl': '000', 'label': 'you2', 'paymentLink': 'http://web.global-iot.m2mzy.com/#/?iccid=', 'userName': 'you2', 'email': ''}, {'id': 1634, 'parentId': 241, 'order': 2, 'name': '前置用户待删除', 'phone': None, 'webUrl': None, 'label': '前置用户待删除', 'paymentLink': None, 'userName': '前置用户待删除', 'email': ''}, {'id': 1639, 'parentId': 241, 'order': 3, 'name': '自动创建用户', 'phone': None, 'webUrl': None, 'label': '自动创建用户', 'paymentLink': None, 'userName': '自动创建用户', 'email': ''}]}]
    temp5 = [{'id': 310, 'parentId': 241, 'order': 0, 'name': 'you2', 'customerKey': 'a8f01f6b-8c76-4fbe-9dbb-a14a050918ca', 'money': 0, 'phone': None, 'createTime': '2024-01-25 14:13:11', 'webUrl': '000', 'label': 'you2', 'paymentLink': 'http://web.global-iot.m2mzy.com/#/?iccid=', 'userName': 'you2', 'email': ''}, {'id': 1634, 'parentId': 241, 'order': 2, 'name': '前置用户待删除', 'customerKey': 'fb6d128c-7e1d-43d5-9e10-669e95603c48', 'money': 0, 'phone': None, 'createTime': '2026-02-26 14:28:09', 'webUrl': None, 'label': '前置用户待删除', 'paymentLink': None, 'userName': '前置用户待删除', 'email': ''}]
    # print(find_user_by_name(data=temp5[0]["children"], target_name='自动创建用户'))
    print(find_user_by_name(data=temp5, target_name='新增待修改用户'))