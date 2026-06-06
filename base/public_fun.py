# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/6 11:03 
@Author  : bo_god
@File    : public_fun.py
@Project : smart_auto_interface 
@Depict    :
'''
import time
import re
import requests
import json
from bs4 import BeautifulSoup
from mailslurp_client import Configuration, ApiClient, WaitForControllerApi, InboxControllerApi, EmailControllerApi


class ByskSmart(object):

    def __int__(self):
        # 邮箱地址（你绑定的）
        self.YOUR_EMAIL = '***REMOVED***'
        self.psw = '***REMOVED***'
        self.token = None

    def email_register(self):
        # MailSlurp API key
        API_KEY = '***REMOVED***'  # <<< 替换成你的 key
        INBOX_ID = '***REMOVED***'

        # 平台注册 POST 接口
        REGISTER_URL = 'https://y.gpstracktech.com/webapi/user/sendRegisterUrl?__sm_ver=1.21.3-4,20250718190538&platform=PC&version=base'  # <<< 替换为实际接口

        # 注册参数
        payload = {
            "email": '***REMOVED***',
            "password": '***REMOVED***',
            "privacyFlag": 1,
            "redirectPath": "https://y.gpstracktech.com"
        }
        headers = {'Content-Type': 'application/json'}

        # 初始化 MailSlurp 客户端
        configuration = Configuration()
        configuration.api_key['x-api-key'] = API_KEY
        api_client = ApiClient(configuration)
        wait_api = WaitForControllerApi(api_client)
        inbox_api = InboxControllerApi(api_client)
        email_api = EmailControllerApi(api_client)

        # ========== Step 1. 提交注册请求 ==========
        print("🚀 正在向平台注册用户...")
        res = requests.post(REGISTER_URL, json=payload, headers=headers)
        assert res.status_code == 200, f"注册请求失败: {res.text}"
        print("✅ 注册请求已发送")

        # ========== Step 2. 等待并获取邮件 ==========
        print("📨 等待主题为‘电子邮件通知’的邮件...")
        email = wait_api.wait_for_latest_email(
            inbox_id=INBOX_ID,
            timeout=60000,
            unread_only=True
        )

        assert "Email notification" in email.subject, "主题不匹配"
        # 提取 HTML 内容
        html_content = email.body or email.body_html
        assert html_content, "邮件内容为空"

        # 提取注册链接
        soup = BeautifulSoup(html_content, 'html.parser')
        link = None
        for a_tag in soup.find_all('a', href=True):
            if '注册' in a_tag.text or '激活' in a_tag.text or '点击' in a_tag.text:
                link = a_tag['href']
                break
        if not link:
            match = re.search(r'https?://[^\s"]+', html_content)
            if match:
                link = match.group()

        assert link, "❌ 没有提取到激活链接"
        print(f"✅ 找到注册链接: {link}")

        # 模拟点击注册链接
        res = requests.get(link)
        print("📦 激活响应状态:", res.status_code)

        # ========== Step 3. 模拟用户点击注册链接 ==========
        print("🌐 模拟点击注册链接...")
        response = requests.get(link)
        assert response.status_code == 200, f"点击注册链接失败: {response.status_code}"
        print("🎉 注册流程已完成")
        return response.status_code

    def user_login(self):
        # 前置条件: 用户注册成功, 用户登录
        server = 'https://ytest.gpstracktech.com/webapi/user/login'
        jsons = {
            "userName": self.YOUR_EMAIL,
            "password": self.psw
        }
        params = {
            "__sm_ver": "1.21.3-4,20250718190538",
            "platform": "PC",
            "version": "base"
        }
        response = requests.post(url=server, data=json.dumps(jsons), params=params, verify=False)
        self.token = response.json()['data']['sid']

    # 新增车组
    def add_group(self, userId):
        server = 'https://ytest.gpstracktech.com/webapi/group/add'
        headers = {
            "Accept": "application/json, text/plain, */*",
            'Accept-Language': "en",
            'Content-Type': 'application/json',
            "token": self.token
        }
        params = {
            "__sm_ver": "1.21.3-4,20250718190538",
            "platform": "PC",
            "version": "base"
        }
        jsons = {
            "groupId": '',
            "userId": userId,
            "groupName": "testAdd",
            "email": "",
            "phone": "",
            "remark": "",
            "logo": ''
        }
        r = requests.post(url=server, data=json.dumps(jsons), params=params, headers=headers, verify=False)
        return r.json()['msg']

    # 新增单车
    def add_vehicle(self, userId, groupId):
        server = 'https://y.gpstracktech.com/webapi/vehicle/addVehicle'
        headers = {
            "Accept": "application/json, text/plain, */*",
            'Accept-Language': "en",
            'Content-Type': 'application/json',
            "token": self.token
        }
        jsons = {
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
        params = {
            "__sm_ver": "1.21.3-4,20250718190538",
            "platform": "PC",
            "version": "base"
        }

        r = requests.post(url=server, data=json.dumps(jsons), params=params, headers=headers,verify=False)
        vehicleID = r.json()['data']['vehicleId']
        return vehicleID

    # 批量加车-校验
    def checkBatch(self, userId, groupId):
        server = 'https://ytest.gpstracktech.com/webapi/vehicle/checkBatch'
        headers = {
            "Accept": "application/json, text/plain, */*",
            'Accept-Language': "en",
            'Content-Type': 'application/json',
            "token": self.token
        }
        jsons = {
            'terminalType': 'ED02R',
            'protocol': 1,
            'userId': userId,
            'groupId': groupId,
            'rechargeYear': 0,
            'trialPeriod': 0,
            'terminalTypeAlias': 'ED02R',
            'terminalNos': '11231230000, 11231230001'
        }
        params = {
            "__sm_ver": "1.21.3-4,20250718190538",
            "platform": "PC",
            "version": "base"
        }
        r = requests.post(url=server, data=json.dumps(jsons), headers=headers, params=params, verify=False)
        return r.json()['msg']  # ass "操作成功"

    # 批量加车
    def submit(self, userId, groupId):
        server = 'https://ytest.gpstracktech.com/webapi/vehicle/submit'
        headers = {
            "Accept": "application/json, text/plain, */*",
            'Accept-Language': "en",
            'Content-Type': 'application/json',
            "token": self.token
        }
        jsons = {
            'terminalType': 'ED02R',
            'protocol': 1,
            'userId': userId,
            'groupId': groupId,
            'rechargeYear': 0,
            'trialPeriod': 0,
            'terminalTypeAlias': 'ED02R',
            'terminalNos': '11231230000, 11231230001'
        }
        params = {
            "__sm_ver": "1.21.3-4,20250718190538",
            "platform": "PC",
            "version": "base"
        }
        r = requests.post(url=server, data=json.dumps(jsons), headers=headers, params=params, verify=False)
        return r.json()['msg']  # "操作成功"

    # 查询车辆
    def check_vehicle(self, vehicleId):
        server = 'https://ytest.gpstracktech.com/webapi/vehicle/getVehicle'
        headers = {
            "Accept": "application/json, text/plain, */*",
            'Accept-Language': "en",
            'Content-Type': 'application/json',
            "token": self.token
        }
        params = {
            'vehicleId': vehicleId,
            '__sm_ver': '1.21.3-4,20250718190538',
            'platform': 'PC',
            'version': 'base'
        }
        r = requests.get(url=server, headers=headers, params=params, verify=False)
        data = r.json()['data']
        userId = data['userId']
        vehicleIds = data['vehicleId']
        groupId = data['groupId']
        return userId, vehicleIds, groupId

    # 修改车辆
    def update_vehicle(self, userId, vehicleId, groupId):
        server = 'https://ytest.gpstracktech.com/webapi/vehicle/updateVehicle'
        headers = {
            "Accept": "application/json, text/plain, */*",
            'Accept-Language': "en",
            'Content-Type': 'application/json',
            "token": self.token
        }
        jsons = {
                    "userId": userId,
                    "vehicleId": vehicleId,
                    "groupId": groupId,
                    "groupName": "DEFAULT_GROUP",
                    "plate": "newAddVehicle",
                    "plateColor": "yellow",
                    "vehicleType": 1,
                    "sim": 'null',
                    "terminalNo": "12322221111",
                    "terminalType": "ED02R",
                    "terminalTypeAlias": "ED02R",
                    "videoMachine": 1,
                    "cameraNum": 4,
                    "cameraLine": "[1,2,3,4]",
                    "protocol": 1,
                    "onlineLink": "ytest.gpstracktech.com:7788",
                    "messageTemplate": "<SPBSJ*P:BSJGPS*D:ytest.gpstracktech.com,7788>",
                    "serviceCode": 'null',
                    "remark": "",
                    "drivingLicense": 'null',
                    "activationTme": 'null',
                    "expireDate": 'null',
                    "activationTmeStr": 'null',
                    "expireDateStr": 'null',
                    "insuranceDueDate": 'null',
                    "maintainDate": 'null',
                    "insuranceDueDateStr": 'null',
                    "maintainDateStr": 'null',
                    "driverName": 'null',
                    "driverCard": 'null',
                    "driverPhone": 'null',
                    "driverGender": 0,
                    "driverPicture": "",
                    "driverRemark": "",
                    "createTime": "2025-07-28 09:34:24",
                    "createTimeStr": 'null',
                    "updateTime": "2025-07-28 09:34:24",
                    "vehicleTypeEnum": 1,
                    "vehicleTypeEnumStr": 'null',
                    "ftpPath": "/driverPhotos",
                    "expired": 'null',
                    "renewNum": 'null',
                    "locateMode": 0,
                    "person": 'null',
                    "frameNo": "",
                    "vehicleState": 'null',
                    "vehicleStateStr": 'null',
                    "protocolName": "808",
                    "vehicleTypeStr": 'null',
                    "iconType": "1",
                    "imei": "",
                    "iccId": "",
                    "lastOnlineTime": 'null',
                    "lastOffTime": 'null',
                    "lbs": 'null',
                    "wifi": 'null',
                    "trialPeriod": 0,
                    "permission": "{\"speak\":true}",
                    "brand": "",
                    "softWareVersion": ""
                }
        params = {
            "__sm_ver": "1.21.3-4,20250718190538",
            "platform": "PC",
            "version": "base"
        }
        r = requests.post(url=server, data=json.dumps(jsons), headers=headers, params=params, verify=False)
        return r.json()['msg']  # "操作成功"

    # 删除车辆
    def del_vehicle(self, vehicleIds):
        server = 'https://ytest.gpstracktech.com/webapi/vehicle/delVehicle'
        headers = {
            "Accept": "application/json, text/plain, */*",
            'Accept-Language': "en",
            'Content-Type': 'application/json',
            "token": self.token
        }
        params = {
            "vehicleIds": vehicleIds,
            "__sm_ver": "1.21.3-4,20250718190538",
            "platform": "PC",
            "version": "base"
        }
        r = requests.get(url=server, headers=headers, params=params, verify=False)
        return r.json()['msg']  # "操作成功"

    # 新增用户
    def add_user(self):
        # 返回新增用户id
        server = 'https://ytest.gpstracktech.com/webapi/user/addUser'
        headers = {
            "Accept": "application/json, text/plain, */*",
            'Accept-Language': "en",
            'Content-Type': 'application/json',
            "token": self.token
        }
        jsons = {
                "id": 'null',
                "userName": "adduser",
                "email": "",
                "password": "***REMOVED***",
                "phone": "",
                "permission": "SVBMHM01,SVBMQA02,SVBMRE03,SVBMAS05,SV7FUSAU,SV7FUSEU,SV7FUSDU,SVHNGPAG,SVHNGPEG,SVHNGPDG,SV5MDEAD,SV5MDEBA,SV5MDEED,SV5MDEDD,SV5MDESM,SVGXMORE,SVTADRAD,SVTADRED,SVTADRDD,SVGXMOPL,SVGXMNPB,SVGXMOSP,SVGXMOHT,SVGXMOTP,SVGXMOCM,SV9PRUAP,SV9PRUEP,SV9PRUDP,SVN0RUAL,SVN0RUEL,SVN0RUDL,SVA7RUAG,SVA7RUEG,SVA7RUDG,SVC1RPML,SVC1RPWE,SVC1RPTH,SVC1RPFU,SVC1RPDR,SVC1RPPR,SVC1RPID,SVC1RPOR,SVC1RPCI,SVC1RPMU,SVC1RPAL,SVC1RPDD,SVC1RPDL,SVC1RPTX,SVC1RPME,SVC1RPAI,SVC1OFRD,SVC1RPAS,SV46ASSC,SV46VSSR,SVC1NFRE,SVC1ONRA,SVC1ONRD,SVC1RPTS,SVC1RPTD,SVC1RPDS,SVC1RPFC,SVC1RPPA,SVC1RPPD,SVMML6DM,SVC1RVWE,SVC1RPVF,SV46DRSC,SVD0QATB,SVD0QADO,SV46ASDB,SV46ASHS,SVJKIDAD,SVJKIDED,SVJKIDD4,SV6FJ9AD,SV6FJ9ED,SV6FJ9DE",
                "webUrl": "",
                "remark": "",
                "whiteIp": ""
            }
        params = {
            "__sm_ver": "1.21.3-4,20250718190538",
            "platform": "PC",
            "version": "base"
        }
        r = requests.post(url=server, data=json.dumps(jsons), headers=headers, params=params, verify=False)
        return r.json()['data']['userId']

    # 查询用户树
    def get_user(self):
        # 返回子用户ID
        server = 'https://ytest.gpstracktech.com/webapi/user/getUserTree'
        headers = {
            "Accept": "application/json, text/plain, */*",
            'Accept-Language': "en",
            'Content-Type': 'application/json',
            "token": self.token
        }
        params = {
            "__sm_ver": "1.21.3-4,20250718190538",
            "platform": "PC",
            "version": "base"
        }
        r = requests.get(url=server, headers=headers, params=params, verify=False)
        return r.json()['data'][0]['id']

    # 查询单个用户
    def getOne(self, userId):
        server = 'https://ytest.gpstracktech.com/webapi/user/getOne'
        headers = {
            "Accept": "application/json, text/plain, */*",
            'Accept-Language': "en",
            'Content-Type': 'application/json',
            "token": self.token
        }
        params = {
            "userId": userId,
            "__sm_ver": "1.21.3-4,20250718190538",
            "platform": "PC",
            "version": "base"
        }
        r = requests.get(url=server, headers=headers, params=params, verify=False)
        return r.json()['data']['userId']  # parentId

    # 修改用户
    def update_user(self, userid):
        server = 'https://ytest.gpstracktech.com/webapi/user/updateUser?__sm_ver=1.21.3-4,20250718190538&platform=PC&version=base'
        headers = {
            "Accept": "application/json, text/plain, */*",
            'Accept-Language': "en",
            'Content-Type': 'application/json',
            "token": self.token
        }
        params = {
            "__sm_ver": "1.21.3-4,20250718190538",
            "platform": "PC",
            "version": "base"
        }
        jsons = {
                "id": userid,
                "userName": "adduser",
                "email": 'null',
                "phone": 'null',
                "permission": "SVBMHM01,SVBMQA02,SVBMRE03,SVD0QATB,SVD0QADO,SV7FUSAU,SV7FUSEU,SV7FUSDU,SVHNGPAG,SVHNGPEG,SVHNGPDG,SV5MDEAD,SV5MDEBA,SV5MDEED,SV5MDEDD,SV5MDESM,SVGXMOPL,SVGXMNPB,SVGXMOSP,SVGXMOHT,SVGXMOTP,SVGXMOCM,SVGXMORE,SVTADRAD,SVTADRED,SVTADRDD,SV9PRUAP,SV9PRUEP,SV9PRUDP,SVN0RUAL,SVN0RUEL,SVN0RUDL,SVA7RUAG,SVA7RUEG,SVA7RUDG,SVC1RPML,SVC1RPWE,SVC1RPTH,SVC1RPFU,SVC1RPDR,SVC1RPPR,SVC1RPID,SVC1RPOR,SVC1RPCI,SVC1RPMU,SVC1RPAI,SVC1RPAL,SVC1RPDD,SVC1RPDL,SVC1RPTX,SVC1RPAS,SVBMAS05,SV46ASSC,SV46ASDB,SV46ASHS,SV46VSSR,SVC1RPME,SVJKIDAD,SVJKIDED,SVJKIDD4,SVC1NFRE,SVC1ONRA,SVC1ONRD,SVC1OFRD,SVC1RPTS,SVC1RPTD,SVC1RPDS,SV6FJ9AD,SV6FJ9ED,SV6FJ9DE,SVC1RPFC,SVC1RPPA,SVC1RPPD,SVMML6DM,SVC1RVWE,SVC1RPVF,SV46DRSC",
                "webUrl": "",
                "remark": "",
                "customerKey": "adf9c0bc-2b4e-4b96-ba45-4a6503703986",
                "whiteIp": ""
            }
        r = requests.post(url=server, data=json.dumps(jsons), headers=headers, params=params, verify=False)
        return r.json()['msg']

    # 删除用户
    def del_user(self, userid):
        server = 'https://ytest.gpstracktech.com/webapi/user/delUser?userId=1444&__sm_ver=1.21.3-4,20250718190538&platform=PC&version=base'
        headers = {
            "Accept": "application/json, text/plain, */*",
            'Accept-Language': "en",
            'Content-Type': 'application/json',
            "token": self.token
        }
        params = {
                "id": userid,
                "__sm_ver": "1.21.3-4,20250718190538",
                "platform": "PC",
                "version": "base"
            }
        r = requests.get(url=server, headers=headers, params=params, verify=False)
        return r.json()['msg']  # "操作成功"


if __name__ == '__main__':
    em = ByskSmart()
    em.email_register()