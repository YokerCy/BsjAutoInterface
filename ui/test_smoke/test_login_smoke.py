# -*- coding: UTF-8 -*-
"""
登录冒烟用例（UI 层示范）。

约定：
  - 每条用例带 @allure.id，直接对应手工用例编号，报告里能反查覆盖情况
  - 断言一律用 Playwright 的 expect（自带重试），禁止 time.sleep
  - locator 只在 pages/ 里出现，这里只调业务方法
"""
import allure
import pytest

from ui.pages.login_page import LoginPage


@allure.epic("UI 冒烟")
@allure.feature("登录模块")
@allure.story("正向登录")
@allure.id("UI001")
@allure.title("UI001 正确账号密码可登录并离开登录页")
@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.p0
def test_login_success(anon_page, ui_cfg, account):
    page = LoginPage(anon_page)
    page.login(
        username=account["username"],
        password=account["password"],
        login_path=ui_cfg["login_path"],
    )
    page.expect_login_success()
    assert "login" not in anon_page.url.lower(), f"登录后仍在登录页: {anon_page.url}"


@allure.epic("UI 冒烟")
@allure.feature("登录模块")
@allure.story("异常登录")
@allure.id("UI002")
@allure.title("UI002 错误密码登录失败，停留在登录页并提示错误")
@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.p1
def test_login_wrong_password(anon_page, ui_cfg, account):
    page = LoginPage(anon_page)
    page.login(
        username=account["username"],
        password="wrong_password_123",
        login_path=ui_cfg["login_path"],
    )
    message = page.expect_login_failed()
    assert message and message.strip(), "未捕获到错误提示"
    assert "login" in anon_page.url.lower(), f"登录失败却离开了登录页: {anon_page.url}"


@allure.epic("UI 冒烟")
@allure.feature("登录模块")
@allure.story("登录态复用")
@allure.id("UI003")
@allure.title("UI003 已登录态直接访问首页，不被踢回登录页")
@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.p1
def test_reuse_login_state(app_page, ui_cfg):
    app_page.goto("/")
    app_page.wait_for_load_state("domcontentloaded")
    # 有登录态时路由守卫不应把人送回登录页
    app_page.wait_for_timeout(2000)
    assert "login" not in app_page.url.lower(), f"登录态失效，被重定向到: {app_page.url}"
