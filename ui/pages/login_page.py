# -*- coding: UTF-8 -*-
"""登录页 Page Object（/#/loginv2）。

实测结构（2026-10-19 抓取）：
  1. 打开 /#/loginv2 后，页面是宣传页 + 导航，登录表单默认隐藏
  2. 必须先点右上角「Sign In」按钮，才会弹出登录表单
  3. 表单内：input[type=text]（用户名）、input[type=password]（密码）、
     底部「Sign In」按钮提交；密码由前端自动加密，填明文即可

定位一律用「结构（form 内的 input 类型）+ role」，不依赖文案，
语言切中英文都不会失效。
"""
from playwright.sync_api import expect

from ui.pages.base_page import BasePage


class LoginPage(BasePage):

    def __init__(self, page):
        super().__init__(page)
        # 导航栏上的「Sign In」：用于唤出登录表单
        self.open_form_button = page.get_by_role("button", name="Sign In").first
        # 表单内账号框
        self.username_input = page.locator("form input[type='text']").first
        # 表单内密码框（show-password 切换后 type 才变 text，初始为 password）
        self.password_input = page.locator("form input[type='password']").first
        # 表单内提交按钮（表单里最后一个按钮）
        self.submit_button = page.locator("form button").last

    def goto_login(self, login_path: str):
        """打开登录页并确保登录表单已展开。"""
        self.open(login_path)
        self.open_form_button.wait_for(state="visible", timeout=30000)
        if not self.username_input.is_visible():
            self.open_form_button.click()
        self.username_input.wait_for(state="visible", timeout=15000)
        return self

    def fill_account(self, username: str, password: str):
        self.username_input.fill(str(username))
        self.password_input.fill(str(password))
        return self

    def submit(self):
        self.submit_button.click()
        return self

    def login(self, username: str, password: str, login_path: str = "/#/loginv2"):
        """完整登录：展开表单 -> 填账号 -> 提交。密码交给前端加密。"""
        self.goto_login(login_path)
        self.fill_account(username, password)
        self.submit()
        return self

    def expect_login_success(self, timeout: int = 30000):
        """
        登录成功判定：URL 真正离开 login 页。

        坑点：平台是 hash 路由（/#/loginv2），不能用 glob "**/login**" 去断言，
        那种写法永远不匹配、永远"通过"，会把登录失败伪装成成功（假绿）。
        这里用谓词等待，直到 URL 里不再包含 login。
        """
        self.page.wait_for_url(lambda url: "login" not in url.lower(), timeout=timeout)
        return self

    def expect_login_failed(self) -> str:
        """登录失败判定：出现错误提示。Element Plus 的 message 会自动消失，需立即取文本。"""
        msg = self.page.locator(".el-message, .el-form-item__error")
        expect(msg.first).to_be_visible(timeout=10000)
        return msg.first.inner_text()
