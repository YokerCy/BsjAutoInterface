# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/6 20:01 
@Author  : bo_god
@File    : allure_parser.py
@Project : smart_auto_interface 
@Depict    : 统计执行结果
'''
import os
import json
from datetime import datetime


def _extract_id(data):
    """
    取跨运行稳定的用例标识。

    注意：data["name"] 是 allure.dynamic.title() 设置的动态标题（如「用户树验证2」），
    会随 yaml 用例文案变化而改变，不能当作跨运行对比的 key，
    否则改一次文案就会被误判成「新增失败」。
    fullName 形如 test_case.test_user#test_user_tree，稳定且可读，用作对比键。
    """
    uid = data.get("fullName")
    if uid:
        return uid
    # 兜底：用 parentSuite/suite + name 拼一个
    labels = {l.get("name"): l.get("value") for l in data.get("labels", [])}
    return f"{labels.get('parentSuite', '')}.{labels.get('suite', '')}#{data.get('name')}"


def _failure_message(data, limit=300):
    """提取失败原因（断言信息/异常堆栈），便于企微消息里直接看到错在哪。"""
    sd = data.get("statusDetails") or {}
    msg = (sd.get("message") or sd.get("trace") or "").strip()
    return msg[:limit]


def get_allure_stats(results_dir):
    """
    解析 Allure 结果目录，统计用例情况。

    返回字典中：
      failures  -> 结构化失败明细 [{id, name, message}]，用于「新增失败」对比
      fail_list -> 兼容旧字段（用例名列表，截断 3 条）
    """
    total = 0
    passed = 0
    failed = 0
    skipped = 0
    broken = 0
    failures = []

    if not os.path.exists(results_dir):
        return None

    # 遍历目录下所有以 -result.json 结尾的文件
    for file_name in os.listdir(results_dir):
        if file_name.endswith("-result.json"):
            total += 1
            file_path = os.path.join(results_dir, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                status = data.get("status")

                if status == "passed":
                    passed += 1
                elif status == "failed":
                    failed += 1
                    failures.append({
                        "id": _extract_id(data),
                        "name": data.get("name"),
                        "message": _failure_message(data),
                    })
                elif status == "skipped":
                    skipped += 1
                else:  # broken 通常指代码报错而非断言失败，同样计为失败
                    broken += 1
                    failures.append({
                        "id": _extract_id(data),
                        "name": data.get("name"),
                        "message": _failure_message(data),
                    })

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": total,
        "passed": passed,
        "failed": failed + broken,
        "skipped": skipped,
        "pass_rate": f"{(passed / total * 100):.2f}%" if total > 0 else "0%",
        "failures": failures,
        "fail_list": [f["name"] for f in failures][:3],  # 兼容旧字段，防止消息过长
    }
