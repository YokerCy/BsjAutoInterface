# -*- coding: UTF-8 -*-
'''
接口请求节流器（全局限流保护）

为什么需要它：
  平台接口对调用频率有限制（实测 /alarm/recentlyAdasList 等报表接口会返回
  {"code":503,"msg":"Rate limit exceeded. Please retry in 120 seconds."}）。
  仅靠「撞上限流后重试」是被动补救：一轮全量用例有十几个请求，
  每个都可能触发限流，累计很容易超出重试预算，最终仍是假失败。

  这里做「主动节流」：对命中限流规则的接口，保证两次调用之间至少间隔 N 秒，
  从源头降低触发限流的概率。撞上限流时仍由 conftest 的重试逻辑兜底。

设计：
  - 按 endpoint 分别计时（接口之间的限额通常互不影响）
  - 使用单调时钟 time.monotonic()，不受系统时间调整影响
  - 线程安全（pytest 未来启用并发时也不会失效）
'''
import threading
import time

from base.log import logger

# 需要节流的接口 key -> 最小调用间隔（秒）
# 依据：服务端限流提示为 120 秒，这里按接口保守设置。
THROTTLE_RULES = {
    # 报表类接口：服务端对同一用户的查询频率限制较严
    "alarm_info": 3,
    "ai_event_alarm_info": 35,      # 实测触发过 503，保守设为 35s
    "get_general_alarm": 3,
    "alarm_report": 3,
    "mileage_report": 3,
    "parking_record": 3,
    "oil_vehicle_fuel": 3,          # 同属报表类查询，与里程/停车保持一致的保守间隔
    "temp_humidity_report": 3,
    # 历史轨迹：官方文档明确「单用户每分钟最多 2 次」
    "historical_trajectory": 35,
}

_lock = threading.Lock()
_last_call = {}


def throttle(endpoint_key, min_interval=None):
    """
    在真正发请求前调用。必要时 sleep，保证距上次同接口调用至少间隔 min_interval 秒。

    :param endpoint_key: config.yaml 里的端点 key
    :param min_interval: 覆盖规则表里的间隔；None 表示查表，未配置则节流间隔为 0
    """
    interval = THROTTLE_RULES.get(endpoint_key, 0) if min_interval is None else min_interval
    if interval <= 0:
        return 0.0

    with _lock:
        last = _last_call.get(endpoint_key)
        now = time.monotonic()
        wait = 0.0
        if last is not None:
            elapsed = now - last
            if elapsed < interval:
                wait = interval - elapsed

        if wait > 0:
            logger.info(f"⏱️ 接口节流：{endpoint_key} 距上次调用不足 {interval}s，等待 {wait:.1f}s")
            time.sleep(wait)

        _last_call[endpoint_key] = time.monotonic()
        return wait


def reset():
    """清空计时（便于测试）。"""
    with _lock:
        _last_call.clear()
