# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/7 11:25 
@Author  : bo_god
@File    : utils.py
@Project : smart_auto_interface 
@Depict    : 封装allure.attach 函数
'''
import json
import allure


def allure_attach_comparison(expected, actual, name="数据对比"):
    """
    优雅地在 Allure 报告中展示预期与实际结果的对比
    :param expected: 预期结果 (支持 int, str, dict, list)
    :param actual: 实际结果
    :param name: 附件展示的名称
    """
    # 状态判断
    is_pass = expected == actual
    status_str = "✅ 通过 (PASS)" if is_pass else "❌ 失败 (FAIL)"

    # 1. 逻辑判断：如果其中一方是复杂对象 (dict/list)
    if isinstance(expected, (dict, list)) or isinstance(actual, (dict, list)):
        # 构造一个结构化的字典，方便在 Allure 以 JSON 格式展示
        comparison_body = {
            "Comparison_Result": status_str,
            "Expected_Data (预期)": expected,
            "Actual_Data (实际)": actual
        }
        try:
            # 必须使用 json.dumps 转换为字符串，Allure 才能正确识别
            content = json.dumps(comparison_body, indent=2, ensure_ascii=False)
            allure.attach(
                body=content,
                name=f"{name} [JSON对比]",
                attachment_type=allure.attachment_type.JSON
            )
        except Exception as e:
            # 极端情况下序列化失败，退化为文本展示
            allure.attach(body=f"解析失败: {e}\n{str(comparison_body)}", name=name,
                          attachment_type=allure.attachment_type.TEXT)

    # 2. 逻辑判断：如果是简单类型 (str, int, float, bool)
    else:
        content = (
            f"校验项目: {name}\n"
            f"测试状态: {status_str}\n"
            f"{'=' * 30}\n"
            f"【预期结果】: {expected} ({type(expected).__name__})\n"
            f"【实际结果】: {actual} ({type(actual).__name__})\n"
            f"{'=' * 30}"
        )
        allure.attach(
            body=content,
            name=f"{name} [文本对比]",
            attachment_type=allure.attachment_type.TEXT
        )