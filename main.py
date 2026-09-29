# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/6 17:21 
@Author  : bo_god
@File    : main.py
@Project : smart_auto_interface 
@Depict    : 总入口

执行链路：跑用例 -> 统计结果 -> 与上次快照对比 -> 按策略推送企微 -> 更新快照 -> 展示/打开报告 -> 退出

修复说明：
  原代码 sys.exit(exit_code) 写在了「统计 + 推送」之前，导致推送逻辑是从未被执行过的死代码。
  现在推送与快照更新都在 sys.exit 之前完成。
  报告展示（report.mode=serve 时会启动常驻服务）放在最末位，避免常驻进程挡住推送逻辑。
'''
import pytest
import os
import argparse
import sys
import subprocess
from base.log import logger
from base.allure_parser import get_allure_stats
from base.wechat_reporter import send_wechat_notification
from base.notify_config import load_notify_config, get_webhook, validate_webhook
from base.result_store import load_snapshot, save_snapshot, diff_failures


def show_report(results_dir, notify_cfg, open_browser_override=None):
    """
    按配置展示报告（conf/notify.yaml -> report.mode）：
      serve    = 启动 allure 服务并自动打开浏览器（本地查看最方便，报告地址会打到日志里）
      generate = 只生成静态报告到 output_dir（适合定时任务/CI，不弹窗、不阻塞）
      none     = 都不做，只保留 allure-results 原始数据

    说明：serve 模式会启动一个常驻服务（进程靠它活着），
          因此所有推送/快照逻辑都必须在调用本函数**之前**完成，
          否则会像旧代码那样出现「报告服务起来了，推送还没跑」的问题。
    """
    rpt = notify_cfg.get("report") or {}
    mode = (rpt.get("mode") or "serve").lower()

    if mode == "none":
        logger.info("ℹ️ report.mode=none，跳过报告展示")
        return None

    if mode == "generate":
        out_dir = rpt.get("output_dir", "./allure-report")
        try:
            subprocess.run(
                f'allure generate "{results_dir}" -o "{out_dir}" --clean',
                shell=True, timeout=180,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
            )
            logger.info(f"✅ 静态报告已生成: {out_dir}")
            report_path = os.path.join(os.getcwd(), out_dir, "index.html")
            logger.info(f"📄 报告入口: {report_path}")
            return out_dir
        except Exception as e:
            logger.warning(f"⚠️ 静态报告生成失败（不影响推送）: {e}")
            return None

    # ---------- serve 模式：启动服务 + 自动打开浏览器 ----------
    port = rpt.get("serve_port", 0) or 0
    open_browser = rpt.get("open_browser", True)
    if open_browser_override is not None:
        open_browser = open_browser_override

    cmd = f'allure serve "{results_dir}"'
    if port:
        cmd += f" --port {port}"

    try:
        if open_browser:
            # 默认行为：allure serve 启动后会自己打开浏览器
            # serve 是常驻进程，用 Popen 异步启动，不阻塞当前脚本
            subprocess.Popen(cmd, shell=True)
            logger.info(f"📊 已启动 Allure 报告服务，浏览器将自动打开")
        else:
            # 不自动打开浏览器：用 run 拿到实际访问地址打日志，方便手动点开或复制
            proc = subprocess.Popen(
                cmd, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            logger.info("📊 已启动 Allure 报告服务（未自动打开浏览器）")
            logger.info("ℹ️ 如需手动打开，请看下方输出的 Server started at 地址")
            # 另起线程读取输出，避免管道写满阻塞
            import threading

            def _drain(p):
                try:
                    for line in p.stdout:
                        line = line.strip()
                        if line:
                            logger.info(f"[allure] {line}")
                except Exception:
                    pass

            threading.Thread(target=_drain, args=(proc,), daemon=True).start()

        logger.info("ℹ️ 报告服务在独立窗口/进程运行中，关闭该窗口即停止服务")
        return "serve"
    except Exception as e:
        logger.warning(f"⚠️ Allure 服务启动失败（不影响已完成的推送）: {e}")
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

    policy = (ncfg.get("policy") or "on_new_failure").lower()

    # 判定是否推送
    if force:
        should_notify = stats["failed"] > 0
        reason = "--force-notify 强制推送（仅在有失败时生效）"
    elif policy == "never":
        should_notify = False
        reason = "policy=never，从不推送"
    elif policy == "always":
        should_notify = True
        reason = "policy=always，每次运行都推送" + ("（本次全绿）" if stats["failed"] == 0 else f"（失败 {stats['failed']} 条）")
    elif not diff["has_baseline"]:
        should_notify = bool(ncfg.get("first_run_as_new", True)) and stats["failed"] > 0
        reason = "首次运行无历史基线" + ("，有失败 -> 推送" if should_notify else "，无失败 -> 不推送")
    else:
        # on_new_failure：仅新增失败才推
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

    # 推送前先校验地址格式：企微地址错误时 HTTP 仍是 200，
    # 只有响应体里的 errcode 才反映真实结果，提前拦截可省去一次无效请求。
    valid, problem = validate_webhook(webhook)
    if not valid:
        logger.error(f"❌ 企微 webhook 格式有问题，跳过推送：{problem}")
        logger.error("   请检查 conf/config.local.yaml 的 wechat.webhook_url（key 应只是那串密钥，不是整条URL）")
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
    parser.add_argument("--open-report", action="store_true", help="本次运行后自动打开 Allure 报告（覆盖配置）")
    parser.add_argument("--no-open-report", action="store_true", help="本次运行后不打开 Allure 报告（覆盖配置）")

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

    # 6. 与上次快照对比并决定是否推送（必须在启动报告服务之前完成）
    snapshot_path = (notify_cfg.get("notify") or {}).get("snapshot_path", "logs/last_result.json")
    previous = load_snapshot(snapshot_path)

    if args.no_notify:
        logger.info("ℹ️ --no-notify 已指定，本次不推送（仍会更新基线快照）")
        diff_failures(stats, previous)
    else:
        decide_and_notify(stats, notify_cfg, previous, force=args.force_notify)

    # 7. 更新快照，作为下次对比的基线
    save_snapshot(snapshot_path, stats)

    # 8. 最后展示报告（serve 模式会启动常驻服务，必须放在所有推送/快照之后）
    open_override = True if args.open_report else (False if args.no_open_report else None)
    show_report(results_dir, notify_cfg, open_browser_override=open_override)

    sys.exit(exit_code)


if __name__ == "__main__":
    run()
