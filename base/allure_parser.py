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


def get_allure_stats(results_dir):
    """
    解析 Allure 结果目录，统计用例情况
    """
    total = 0
    passed = 0
    failed = 0
    skipped = 0
    broken = 0
    error_details = []

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
                    # 记录失败的具体用例名，方便在消息里直接展示
                    error_details.append(data.get("name"))
                elif status == "skipped":
                    skipped += 1
                else:  # broken 通常指代码报错而非断言失败
                    broken += 1

    return {
        "total": total,
        "passed": passed,
        "failed": failed + broken,
        "skipped": skipped,
        "pass_rate": f"{(passed / total * 100):.2f}%" if total > 0 else "0%",
        "fail_list": error_details[:3]  # 只取前三个失败用例防止消息过长
    }