# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/6 17:21 
@Author  : bo_god
@File    : main.py
@Project : smart_auto_interface 
@Depict    : 总入口
'''
import pytest
import os
import argparse
import sys
import subprocess
import time
from base.log import logger
from base.allure_parser import get_allure_stats
from base.wechat_reporter import send_wechat_notification


def run():
    # 1. 创建参数解析器，方便在命令行通过 -m 或 -f 传参
    parser = argparse.ArgumentParser(description="接口自动化巡检执行入口")

    parser.add_argument("-env", default="test", help="运行环境: test 或 prod")
    parser.add_argument("-f", "--file", help="指定运行的测试文件路径, 例如: tests/test_vehicle.py")
    parser.add_argument("-m", "--module", help="运行指定的模块标签, 例如: smoke")
    parser.add_argument("-d", "--dir", help="指定运行的目录, 例如: tests_case/vehicle_module/")

    args = parser.parse_args()

    # 2. 构建 pytest 执行参数列表
    # --alluredir 自动生成报告数据
    # --clean-alluredir 每次运行前清空旧数据
    pytest_args = ["--alluredir=./allure-results", "--clean-alluredir"]

    if args.env:
        pytest_args.extend(["--env", args.env])
    # 3. 根据输入动态添加路径或筛选条件
    if args.file:
        pytest_args.append(args.file)
    elif args.dir:
        pytest_args.append(args.dir)
    elif args.module:
        pytest_args.extend(["-m", args.module])
    else:
        # 默认执行 tests 目录下所有用例
        pytest_args.append("test_case/")

    # 4. 打印当前执行信息，方便调试
    logger.info(f"🚀 开始执行巡检...")
    logger.info(f"📂 执行参数: {pytest_args}")

    # 5. 调用 pytest
    exit_code = pytest.main(pytest_args)

    # 6. (可选) 自动生成并自动打开报告 (本地调试用)
    # os.system("allure serve ./allure-results")

    # 执行完后，如果是本地开发环境，自动启动报告
    results_dir = os.path.join(os.getcwd(), "allure-results")
    if not os.path.exists(results_dir):
        logger.error("❌ 错误：找不到 allure-results 文件夹，无法生成报告")
        return

    logger.info("📊 正在启动 Allure 服务...")

    # 使用 subprocess.Popen 异步启动，不会阻塞当前 Python 进程
    # windows 下需要 shell=True
    try:
        subprocess.Popen("allure serve ./allure-results", shell=True)
        logger.info("✅ 服务启动成功，请在弹出的浏览器中查看报告。")
        # 给服务一点启动时间，防止 Python 进程立刻结束导致服务挂掉
        time.sleep(10)
    except Exception as e:
        logger.error(f"❌ 启动失败，请检查是否配置了 Allure 环境变量: {e}")
    sys.exit(exit_code)

    # 3. 统计结果
    stats = get_allure_stats(results_dir)

    # 4. 发送通知
    # webhook = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=KEY"
    # send_wechat_notification(webhook, stats)


if __name__ == "__main__":
    run()

