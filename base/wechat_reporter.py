# -*- coding: UTF-8 -*-
'''
@Time    : 2026/2/6 19:59 
@Author  : bo_god
@File    : wechat_reporter.py
@Project : smart_auto_interface 
@Depict    : 推送

已知的两个坑（保留注释，别改回去）：
  1) 企微推送失败时 HTTP 状态码依然是 200，真正结果在响应体的 errcode 里；
     只看 status_code 会把「发送失败」误判成「发送成功」。=> 必须校验 errcode == 0。
  2) markdown 类型不支持 mentioned_list/@ 人；
     要 @ 人必须另发一条 msgtype=text 的消息。
'''
import json
import requests


def _post(webhook_url, payload):
    """统一发送，成功与否以响应体 errcode 为准（不看 status_code）。"""
    try:
        res = requests.post(webhook_url, json=payload, timeout=10)
    except Exception as e:
        return False, {"error": f"请求异常: {e}"}

    try:
        data = res.json()
    except Exception:
        data = {}

    if data.get("errcode") == 0:
        return True, data
    return False, {
        "status_code": res.status_code,
        "errcode": data.get("errcode"),
        "errmsg": data.get("errmsg"),
        "text": res.text[:300],
    }


def _overview_lines(stats):
    """用例概况（所有消息模板共用）。"""
    total = stats.get("total", 0)
    passed = stats.get("passed", 0)
    failed = stats.get("failed", 0)
    skipped = stats.get("skipped", 0)
    return [
        f"> **执行时间**: {stats.get('timestamp', '')}",
        f"> **用例概况**: 总数 {total} / 通过 {passed} / 失败 {failed} / 跳过 {skipped}",
        f"> **通过率**: {stats.get('pass_rate', '0%')}",
    ]


def _fail_detail_lines(failures, title):
    lines = [f"**{title} {len(failures)} 条**:"]
    for i, f in enumerate(failures, 1):
        lines.append(f"> {i}. {f.get('name')}")
        lines.append(f'> <font color="comment">{f.get("id")}</font>')
        if f.get("message"):
            lines.append(f"> 原因：{f['message'][:200]}")
        lines.append(">")
    return lines


def build_all_pass_content(stats):
    """全绿消息：每次运行都推送时使用，让人确认「巡检跑过了且正常」。"""
    lines = [
        '## <font color="info">接口自动化巡检 · 全部通过</font>',
        *_overview_lines(stats),
        "",
        "> ✅ 本次运行未发现任何失败用例。",
    ]
    return "\n".join(lines)


def build_new_failure_content(stats, diff):
    """构造「新增失败」摘要（纯文字，不依赖任何报告托管地址）。"""
    new = diff.get("new", [])
    persistent = diff.get("persistent", [])
    resolved = diff.get("resolved", [])

    lines = [
        '## <font color="warning">接口自动化巡检 · 新增失败</font>',
        *_overview_lines(stats),
        "",
        *_fail_detail_lines(new, "新增失败"),
    ]

    if persistent:
        lines.append(f"> 另有 **{len(persistent)} 条**为历史已存在的失败，本次不重复打扰。")
    if resolved:
        names = "、".join(x.get("name", "") for x in resolved)
        lines.append(f"> 本次已恢复 {len(resolved)} 条：{names}")

    return "\n".join(lines)


def build_content(stats, diff):
    """
    按运行结果自动选择消息模板：
      - 无失败           -> 全绿模板
      - 有新增失败       -> 新增失败模板
      - 只有历史旧失败   -> 沿用「新增失败」模板（会写明新增0条、其余为历史失败）
    """
    if stats.get("failed", 0) == 0:
        return build_all_pass_content(stats)
    return build_new_failure_content(stats, diff)


def send_markdown(webhook_url, content):
    ok, info = _post(webhook_url, {"msgtype": "markdown", "markdown": {"content": content}})
    if ok:
        print("✅ 企业微信推送成功")
    else:
        print(f"❌ 企业微信推送失败: {json.dumps(info, ensure_ascii=False)[:400]}")
    return ok


def send_mention(webhook_url, userids, content=None):
    """@ 提醒必须用 text 类型单独发一条（markdown 不支持 mentioned_list）。"""
    payload = {
        "msgtype": "text",
        "text": {
            "content": content or "接口巡检发现新增失败，请及时查看。",
            "mentioned_list": userids or [],
        },
    }
    ok, info = _post(webhook_url, payload)
    if ok:
        print(f"✅ @ 提醒已发送给 {len(userids or [])} 人")
    else:
        print(f"❌ @ 提醒发送失败: {json.dumps(info, ensure_ascii=False)[:400]}")
    return ok


def send_wechat_notification(webhook_url, stats, diff, mention_userids=None, report_dir=None):
    """
    统一推送入口：先发 markdown 摘要，需要时再单独发一条 text 做 @ 提醒。

    消息模板由 build_content() 依据运行结果自动选择（全绿 / 新增失败）。
    注意：只有「有失败」时才 @ 人 —— 全绿也 @ 会变成打扰。
    """
    if not webhook_url or not webhook_url.startswith("http"):
        print("❌ 未配置有效的企微 webhook，跳过推送")
        return False

    content = build_content(stats, diff)
    ok = send_markdown(webhook_url, content)

    # 全绿时不 @ 人，避免无意义打扰
    if ok and mention_userids and stats.get("failed", 0) > 0:
        send_mention(webhook_url, mention_userids)

    return ok
