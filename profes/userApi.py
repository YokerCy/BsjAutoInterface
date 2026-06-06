# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/6 13:52 
@Author  : bo_god
@File    : userApi.py
@Project : smart_auto_interface 
@Depict    : 登录/ 用户
'''


class UserApi:
    def __init__(self, client):
        self.client = client

    # 用户树
    def get_user_tree(self):
        res = self.client.send_by_key(
            "GET",
            "userTree", )
        # print(f"响应类型:{type(res)}")
        return res.json()
    # data[0]."children"[0].[id/name/parentId/phone/userName]

    def get_load_sim_user(self, userid):
        """
        获取用户车组
        :param userid: 用户ID
        :return: object对象
        """
        res = self.client.send_by_key(
            "POST",
            "loadSimpleByUsers",
            json={"userIds": [userid]}
        )
        return res.json()

    def add_user(self, user_name, email, pwd, phone, parent_id):
        """
        新增用户
        :param user_name: 新增用户名 必填项
        :param email: 邮箱 可选项
        :param pwd: 密码 必填项 6位数字加字母
        :param phone: 电话号码 可选项
        :param parent_id: 上级用户ID
        :return:
        """
        res = self.client.send_by_key(
            "POST",
            "addUser",
            json={
                 "userName": user_name,
                 "email": email,
                 "password": pwd,
                 "phone": phone,
                 "parentId": parent_id
            }
        )
        return res.json()

    def del_user(self, user_id):
        """
        删除用户
        :param user_id: 待删除用户ID
        :return:
        """
        res = self.client.send_by_key(
            "GET",
            "delUser",
            params={"userId": user_id}
        )
        return res.json()

    def update_user(self, user_id, user_name, email, phone):
        """
        修改用户信息
        :param user_id: 用户id
        :param user_name: 用户名
        :param email: 邮箱 可选参数
        :param phone: 电话号码 可选参数
        :return:
        """
        res = self.client.send_by_key(
            "POST",
            "updateUser",
            json={
                "id": user_id,
                 "userName": user_name,
                 "email": email,
                 "phone": phone
                }
        )
        return res.json()
