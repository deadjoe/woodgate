"""
Pytest配置文件
"""

import asyncio
import os
from typing import Any, Dict, Generator

import pytest
from playwright.sync_api import BrowserContext, Page

# 导入异步API
from playwright.async_api import async_playwright


# 自定义命令行选项
def pytest_addoption(parser):
    """添加自定义命令行选项"""
    parser.addoption(
        "--headless", action="store_true", default=True, help="是否使用无头模式运行浏览器"
    )
    parser.addoption("--slow-mo", default="0", help="减慢浏览器操作的毫秒数")


# 自定义浏览器固件
@pytest.fixture(scope="session")
def browser_type_launch_args(pytestconfig) -> Dict[str, Any]:
    """浏览器启动参数"""
    return {
        "headless": pytestconfig.getoption("--headless"),
        "slow_mo": int(pytestconfig.getoption("--slow-mo")),
        "channel": pytestconfig.getoption("--browser-channel"),
        "args": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--disable-gpu",
            "--disable-notifications",
        ],
    }


# 自定义浏览器上下文固件
@pytest.fixture(scope="function")
def browser_context_args() -> Dict[str, Any]:
    """浏览器上下文参数"""
    return {
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "ignore_https_errors": True,
        "java_script_enabled": True,
        "has_touch": False,
    }


# 自定义页面固件
@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """创建页面并配置 - 同步版本"""
    page = context.new_page()

    # 配置页面选项
    page.route("**/*.{png,jpg,jpeg,gif,svg}", lambda route: route.abort())  # 阻止加载图片，提高性能
    page.set_default_timeout(20000)  # 设置默认超时时间为20秒
    page.set_default_navigation_timeout(30000)  # 设置导航超时时间为30秒

    yield page

    # 测试结束后关闭页面
    page.close()


# 自定义事件循环固件
@pytest.fixture(scope="function")
def event_loop():
    """创建事件循环 - 每个测试函数一个新的事件循环"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # 确保所有待处理的任务都已完成
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()
    # 运行直到所有任务完成
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    loop.close()


# 自定义登录固件
@pytest.fixture(scope="function")
def authenticated_page(page: Page) -> Generator[Page, None, None]:
    """创建已登录的页面"""
    # 从环境变量获取凭据
    username = os.environ.get("REDHAT_USERNAME", "")
    password = os.environ.get("REDHAT_PASSWORD", "")

    if not username or not password:
        pytest.skip("未设置REDHAT_USERNAME或REDHAT_PASSWORD环境变量")

    # 访问登录页面
    page.goto("https://access.redhat.com/login", wait_until="networkidle")

    # 处理Cookie弹窗
    try:
        cookie_notice = page.wait_for_selector(
            "#truste-consent-button, #onetrust-banner-sdk, .pf-c-modal-box, [role='dialog'][aria-modal='true'], .cookie-banner, #cookie-notice",
            state="visible",
            timeout=3000,
        )
        if cookie_notice:
            cookie_notice.click()
    except Exception:
        pass

    # 输入用户名
    username_field = page.wait_for_selector("#username", state="visible", timeout=10000)
    if username_field:
        username_field.fill("")  # 清空
        username_field.fill(username)  # 输入

    # 点击下一步按钮（如果存在）
    try:
        next_button = page.wait_for_selector("#login-show-step2", state="visible", timeout=3000)
        if next_button:
            next_button.click()
    except Exception:
        pass

    # 输入密码
    password_field = page.wait_for_selector("#password", state="visible", timeout=10000)
    if password_field:
        password_field.fill("")  # 清空
        password_field.fill(password)  # 输入

    # 点击登录按钮
    login_button = page.wait_for_selector("#kc-login", state="visible", timeout=5000)
    if login_button:
        login_button.click()

    # 等待登录完成
    page.wait_for_selector(".pf-c-page__header", state="visible", timeout=20000)

    yield page
