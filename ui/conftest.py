# -*- coding: UTF-8 -*-
"""
UI 层 fixtures。

两个页面 fixture 的区别（很重要，混用会导致登录用例假绿）：
  anon_page —— 无登录态。用于登录页自身（登录成功/失败、表单校验）。
  app_page  —— 带登录态。用于业务页面，避免每条用例都点一次登录（慢且脆）。

登录态首次运行时真实登录一次并落盘 logs/ui_state.json，
后续 12 小时内直接复用；过期自动重登。
"""
import pytest

from base.log import logger
from base.redConfig import Config
from base.ui.browser import (
    artifact_dir,
    build_context,
    load_ui_config,
    resolve_channel,
    state_is_fresh,
    state_path,
)
from ui.pages.login_page import LoginPage


@pytest.fixture(scope="session")
def ui_cfg():
    return load_ui_config()


@pytest.fixture(scope="session")
def account(env):
    """
    取当前环境的账号。

    注意：base/redConfig.py 的 Config.__init__ 目前忽略传入的 env（始终用 default），
    所以这里按 --env 显式从 data 里取，不依赖 Config 的 env 属性。
    """
    cfg = Config()
    envs = cfg.data.get("environments", {})
    env_name = env if env in envs else cfg.data.get("default", "test")
    acc = envs[env_name].get("accounts", {}).get("admin", {})
    if not acc.get("username"):
        raise RuntimeError(f"环境 {env_name} 未配置账号（conf/config.yaml -> accounts.admin）")
    return acc


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, browser_name, ui_cfg):
    """
    浏览器渠道决策：命令行 --browser-channel > conf/ui.yaml > 自动探测。

    默认走 chrome（与平台绝大多数真实用户一致），本机没装则回退 msedge，
    都没有才用 Playwright 自带 chromium（需先 playwright install）。
    """
    args = dict(browser_type_launch_args)

    # 命令行已显式指定渠道时不覆盖；只有 firefox/webkit 不做渠道解析
    if browser_name == "chromium" and not args.get("channel"):
        channel = resolve_channel(ui_cfg)
        if channel:
            args["channel"] = channel
            logger.info(f"🌐 UI 浏览器渠道: {channel}")
        else:
            logger.warning(
                "⚠️ 未找到 chrome/msedge，回退 Playwright 自带 chromium。"
                "若启动失败请执行: python -m playwright install chromium"
            )
    return args


@pytest.fixture(scope="session")
def auth_state(browser, ui_cfg, account):
    """登录态快照：有效则复用，否则真实登录一次生成。"""
    if state_is_fresh(ui_cfg):
        return state_path(ui_cfg)

    context = build_context(browser, ui_cfg)
    page = context.new_page()
    try:
        login_page = LoginPage(page)
        login_page.login(
            username=account["username"],
            password=account["password"],
            login_path=ui_cfg["login_path"],
        )
        login_page.expect_login_success()
        state_path(ui_cfg).parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(state_path(ui_cfg)))
    finally:
        context.close()
    return state_path(ui_cfg)


@pytest.fixture
def anon_page(browser, ui_cfg, request):
    """无登录态页面：测登录页用。"""
    context = build_context(browser, ui_cfg)
    context.tracing.start(screenshots=True, snapshots=True, sources=False)
    page = context.new_page()
    yield page
    _teardown(context, page, ui_cfg, request)


@pytest.fixture
def app_page(browser, ui_cfg, auth_state, request):
    """带登录态页面：测业务页用。"""
    context = build_context(browser, ui_cfg, storage_state=auth_state)
    context.tracing.start(screenshots=True, snapshots=True, sources=False)
    page = context.new_page()
    yield page
    _teardown(context, page, ui_cfg, request)


def _teardown(context, page, cfg, request):
    """
    统一收尾：失败时保留 trace + 全页截图。
    trace 用 `playwright show-trace logs/ui_artifacts/xxx.zip` 可完整回放现场。
    """
    rep = getattr(request.node, "rep_call", None)
    failed = bool(rep is not None and rep.failed)
    out = artifact_dir(cfg)

    if failed:
        try:
            context.tracing.stop(path=str(out / f"{request.node.name}.zip"))
        except Exception:
            pass
        try:
            page.screenshot(path=str(out / f"{request.node.name}.png"), full_page=True)
        except Exception:
            pass
    else:
        try:
            context.tracing.stop()
        except Exception:
            pass
    context.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
