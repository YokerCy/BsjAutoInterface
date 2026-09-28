# -*- coding: UTF-8 -*-
'''
运行结果快照存取 + 增量失败对比。

用途：实现「相比上次新增失败才推送」。
历史已存在的失败（persistent）只计数、不打扰人，
避免出现「每天一条永远没人看的告警」这种告警疲劳。
'''
import os
import json
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_path(path):
    """快照路径按项目根目录解析，避免工作目录不同导致快照写丢。"""
    if os.path.isabs(path):
        return path
    return os.path.join(PROJECT_ROOT, path)


def load_snapshot(path):
    """读取上次运行结果；首次运行（无快照）返回 None。"""
    abs_path = resolve_path(path)
    if not os.path.exists(abs_path):
        return None
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        # 快照损坏不能影响主流程，按「首次运行」处理
        print(f"⚠️ 快照读取失败（按首次运行处理）: {e}")
        return None


def save_snapshot(path, stats):
    """保存本次运行结果，作为下次对比的基线。"""
    abs_path = resolve_path(path)
    try:
        os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
        data = {
            "timestamp": stats.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": stats.get("total", 0),
            "passed": stats.get("passed", 0),
            "failed": stats.get("failed", 0),
            "skipped": stats.get("skipped", 0),
            "pass_rate": stats.get("pass_rate", "0%"),
            "failures": [
                {
                    "id": f.get("id"),
                    "name": f.get("name"),
                    "message": (f.get("message") or "")[:300],
                }
                for f in stats.get("failures", [])
            ],
        }
        with open(abs_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ 快照保存失败: {e}")
        return False


def diff_failures(current_stats, previous):
    """
    对比本次与上次运行。

    对比键用 allure 的 fullName（形如 test_case.test_user#test_user_tree），
    它是跨运行稳定的用例标识；不能用 name（那是 dynamic.title 设的动态标题，会变）。

    返回：
      new        -> 新增失败（上次没有 / 上次通过）
      resolved   -> 本次已恢复（上次失败、本次消失）
      persistent -> 持续失败（上次也在失败）—— 只计数不推送
      has_baseline -> 是否有历史基线可比
    """
    cur_fail = {f["id"]: f for f in current_stats.get("failures", []) if f.get("id")}

    if previous is None:
        return {"new": list(cur_fail.values()), "resolved": [], "persistent": [], "has_baseline": False}

    prev_fail = {f["id"]: f for f in (previous.get("failures") or []) if f.get("id")}

    new = [f for i, f in cur_fail.items() if i not in prev_fail]
    persistent = [f for i, f in cur_fail.items() if i in prev_fail]
    resolved = [prev_fail[i] for i in prev_fail if i not in cur_fail]

    return {"new": new, "resolved": resolved, "persistent": persistent, "has_baseline": True}
