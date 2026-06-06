# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/6 19:59 
@Author  : bo_god
@File    : wechat_reporter.py
@Project : smart_auto_interface 
@Depict    : 推送
'''
import requests
import json


def send_wechat_notification(webhook_url, stats):
    if not stats:
        print("❌ 无统计数据，跳过推送")
        return

    # 根据结果决定颜色
    color = "info" if stats['failed'] == 0 else "warning"

    # 构造失败用例的文本
    fail_text = ""
    if stats['fail_list']:
        fail_text = "\n> **失败详情**: <font color=\"warning\">" + ", ".join(stats['fail_list']) + "</font>"

    content = f"""## <font color="{color}">接口自动化巡检报告</font>
> **项目名称**: 智能接口巡检系统
> **测试结果**: <font color="{color}">{stats['pass_rate']} 通过</font>
>
> **用例统计**: 
> - 总数: {stats['total']}
> - 通过: <font color="info">{stats['passed']}</font>
> - 失败: <font color="warning">{stats['failed']}</font>
> - 跳过: {stats['skipped']} {fail_text}
> 
> [点击查看完整 Allure 报告](http://your_jenkins_ip:8080/job/test/allure/)
"""

    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content}
    }

    response = requests.post(webhook_url, json=payload)
    if response.status_code == 200:
        print("✅ 企业微信通知发送成功")
    else:
        print(f"❌ 发送失败: {response.text}")