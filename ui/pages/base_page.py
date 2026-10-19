# -*- coding: UTF-8 -*-
"""页面对象基类：统一等待策略与常用动作，禁止在测试里写裸 locator。"""
from playwright.sync_api import Page, expect


class BasePage:
    """所有 Page Object 的父类。

    约定：
      - locator 只写在子类的 __init__ 或 property 里
      - 测试方法只调这里的业务方法，不直接 page.click("xxx")
    """

    # 子类覆盖：用于等待页面就绪的关键元素 locator
    ready_marker = None

    def __init__(self, page: Page):
        self.page = page

    def open(self, path: str = "/"):
        """打开相对路径（base_url 已在 context 里设置）。"""
        self.page.goto(path)
        return self

    def wait_ready(self, timeout: int = None):
        """等页面关键元素出现，替代 sleep。"""
        if self.ready_marker is not None:
            expect(self.ready_marker).to_be_visible(timeout=timeout)
        return self

    def url(self) -> str:
        return self.page.url

    def title(self) -> str:
        return self.page.title()

    def screenshot(self, name: str):
        """中途留证：只在需要人工核对的节点手工调用。"""
        self.page.screenshot(path=name, full_page=True)
        return name
