# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/6 17:21 
@Author  : bo_god
@File    : main.py
@Project : smart_auto_interface 
@Depict    : 总入口

执行链路：跑用例 -> 统计结果 -> 生成静态报告 -> 与上次快照对比 -> 按策略推送企微 -> 更新快照 -> 退出

修复说明：
  原代码 sys.exit(exit_code) 写在了「统计 + 推送」之前，导致推送逻辑是从未被执行过的死代码。
  现在推送与快照更新都在 sys.exit 之前完成。
'''
import pytest
import os
import argparse
import sys
import subprocess
from base.log import logger
from base.allure_parser import get_allure_stats
from base.wechat_reporter import send_wechat_notification
from base.notify_config import load_notify_config, get_webhook
from base.result_store import load_snapshot, save_snapshot, diff_failures


def generate_static_report(results_dir, notify_cfg):
    """
    用 allure generate 生成静态报告，替代原来的 allure serve。

    原方案的问题：allure serve 会弹浏览器、占端口、且不退出，
    放在定时任务里会让进程挂死，报告地址还是 localhost，别人打不开。
    这里生成失败也只告警不中断，确保不会影响后续推送。
    """
    rpt = notify_cfg.get("report") or {}
    if not rpt.get("generate", True):
        return None

    out_dir = rpt.get("output_dir", "./allure-report")
    try:
        subprocess.run(
            f'allure generate "{results_dir}" -o "{out_dir}" --clean',
            shell=True, timeout=180,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
        logger.info(f"✅ 静态报告已生成: {out_dir}")
        return out_dir
    except Exception as e:
        logger.warning(f"⚠️ 静态报告生成失败（不影响推送）: {e}")
        return None


def decide_and_notify(stats, notify_cfg, previous, force=False):
    """
    按策略决定是否推送企微。
    策略默认 on_new_failure：仅当「相比上次出现新增失败」才推送。
    """
    ncfg = notify_cfg.get("notify") or {}
    diff = diff_failures(stats, previous)
    new_cnt = len(diff["new"])

    logger.info(
        f"📊 用例总数 {stats['total']} / 通过 {stats['passed']} / "
        f"失败 {stats['failed']} / 跳过 {stats['skipped']} / 通过率 {stats['pass_rate']}"
    )

    if not ncfg.get("enabled", True):
        logger.info("ℹ️ notify.enabled=false，已跳过推送")
        return diff, False

    # 判定是否推送
    if not diff["has_baseline"]:
        should_notify = bool(ncfg.get("first_run_as_new", True)) and stats["failed"] > 0
        reason = "首次运行无历史基线" + ("，有失败 -> 推送" if should_notify else "，无失败 -> 不推送")
    elif force and stats["failed"] > 0:
        should_notify = True
        reason = "--force-notify 强制推送"
    else:
        should_notify = new_cnt > 0
        reason = f"新增失败 {new_cnt} 条" + (
            f"（另有 {len(diff['persistent'])} 条为历史已存在失败，不重复打扰）" if diff["persistent"] else ""
        )

    logger.info(f"🔔 推送判定: {'推送' if should_notify else '跳过'} —— {reason}")

    if not should_notify:
        return diff, False

    webhook = get_webhook(notify_cfg)
    if not webhook:
        logger.warning("⚠️ 未配置企微 webhook（conf/config.local.yaml -> wechat.webhook_url），跳过推送")
        return diff, False

    mention_ids = (ncfg.get("mention_userids") or []) if ncfg.get("mention_on_push") else []
    ok = send_wechat_notification(webhook, stats, diff, mention_userids=mention_ids)
    return diff, ok


def run():
    # 1. 创建参数解析器，方便在命令行通过 -m 或 -f 传参
    parser = argparse.ArgumentParser(description="接口自动化巡检执行入口")

    parser.add_argument("-env", default="test", help="运行环境: test 或 prod")
    parser.add_argument("-f", "--file", help="指定运行的测试文件路径, 例如: test_case/test_vehicle.py")
    parser.add_argument("-m", "--module", help="运行指定的模块标签, 例如: smoke")
    parser.add_argument("-d", "--dir", help="指定运行的目录, 例如: test_case/")
    parser.add_argument("--no-notify", action="store_true", help="本次运行不推送企微")
    parser.add_argument("--force-notify", action="store_true", help="忽略「仅新增失败」策略，只要失败就推")

    args = parser.parse_args()

    notify_cfg = load_notify_config()

    # 2. 构建 pytest 执行参数列表
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
        pytest_args.append("test_case/")

    logger.info(f"🚀 开始执行巡检...")
    logger.info(f"📂 执行参数: {pytest_args}")

    # 4. 调用 pytest
    exit_code = pytest.main(pytest_args)

    results_dir = os.path.join(os.getcwd(), "allure-results")
    if not os.path.exists(results_dir):
        logger.error("❌ 错误：找不到 allure-results 文件夹，无法统计结果")
        sys.exit(exit_code)

    # 5. 统计结果
    stats = get_allure_stats(results_dir)
    if not stats:
        logger.error("❌ 用例统计失败（未解析到任何 result 文件）")
        sys.exit(exit_code)

    # 6. 生成静态报告（失败不影响推送）
    generate_static_report(results_dir, notify_cfg)

    # 7. 与上次快照对比并决定是否推送
    snapshot_path = (notify_cfg.get("notify") or {}).get("snapshot_path", "logs/last_result.json")
    previous = load_snapshot(snapshot_path)

    if args.no_notify:
        logger.info("ℹ️ --no-notify 已指定，本次不推送（仍会更新基线快照）")
        diff_failures(stats, previous)
    else:
        decide_and_notify(stats, notify_cfg, previous, force=args.force_notify)

    # 8. 更新快照，作为下次对比的基线
    save_snapshot(snapshot_path, stats)

    sys.exit(exit_code)


if __name__ == "__main__":
    run()
