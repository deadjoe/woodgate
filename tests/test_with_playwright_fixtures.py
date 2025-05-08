"""
使用pytest-playwright固件的测试
"""

import pytest
from playwright.sync_api import Page, expect

# 这些测试需要安装pytest-playwright
# pip install pytest-playwright

# 这些测试使用pytest-playwright提供的固件
# 运行方式: pytest tests/test_with_playwright_fixtures.py --browser chromium


def test_redhat_portal_title(page: Page):
    """测试Red Hat门户网站标题"""
    # 访问Red Hat门户网站
    page.goto("https://access.redhat.com/", wait_until="networkidle")

    # 验证页面标题包含"Red Hat"
    expect(page).to_have_title(title_or_reg_exp="Red Hat")


def test_redhat_search_page(page: Page):
    """测试Red Hat搜索页面"""
    # 访问Red Hat搜索页面
    page.goto("https://access.redhat.com/search", wait_until="networkidle")

    # 验证搜索框存在
    search_box = page.locator("input[name='q']")
    expect(search_box).to_be_visible()

    # 在搜索框中输入关键词
    search_box.fill("kubernetes")

    # 点击搜索按钮
    page.locator("button[type='submit']").click()

    # 等待搜索结果加载
    page.wait_for_load_state("networkidle")

    # 验证搜索结果页面包含搜索关键词
    expect(page.locator("body")).to_contain_text("kubernetes")


def test_redhat_products_page(page: Page):
    """测试Red Hat产品页面"""
    # 访问Red Hat产品页面
    page.goto("https://access.redhat.com/products", wait_until="networkidle")

    # 验证页面包含产品列表
    product_list = page.locator(".product-listing")
    expect(product_list).to_be_visible()

    # 验证页面包含常见产品
    expect(page.locator("body")).to_contain_text("Red Hat Enterprise Linux")
    expect(page.locator("body")).to_contain_text("Red Hat OpenShift")


@pytest.mark.skip(reason="需要登录凭据")
def test_redhat_login_page(page: Page):
    """测试Red Hat登录页面"""
    # 访问Red Hat登录页面
    page.goto("https://access.redhat.com/login", wait_until="networkidle")

    # 验证登录表单存在
    login_form = page.locator("#kc-form-login")
    expect(login_form).to_be_visible()

    # 验证用户名输入框存在
    username_input = page.locator("#username")
    expect(username_input).to_be_visible()

    # 验证密码输入框存在
    password_input = page.locator("#password")
    expect(password_input).to_be_visible()

    # 验证登录按钮存在
    login_button = page.locator("#kc-login")
    expect(login_button).to_be_visible()


@pytest.mark.skip(reason="需要登录凭据")
def test_search_with_tracing(page: Page, browser_context_args, browser_context):
    """使用跟踪功能测试搜索"""
    # 启用跟踪
    browser_context.tracing.start(screenshots=True, snapshots=True)

    # 访问Red Hat搜索页面
    page.goto("https://access.redhat.com/search", wait_until="networkidle")

    # 在搜索框中输入关键词
    search_box = page.locator("input[name='q']")
    search_box.fill("openshift troubleshooting")

    # 点击搜索按钮
    page.locator("button[type='submit']").click()

    # 等待搜索结果加载
    page.wait_for_load_state("networkidle")

    # 验证搜索结果页面包含搜索关键词
    expect(page.locator("body")).to_contain_text("openshift")

    # 停止跟踪并保存
    browser_context.tracing.stop(path="trace.zip")


# 使用自定义浏览器选项的测试
@pytest.fixture(scope="function")
def browser_context_args():
    """自定义浏览器上下文参数"""
    return {
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "ignore_https_errors": True,
        "java_script_enabled": True,
        "has_touch": False,
    }


@pytest.fixture(scope="function")
def context(browser, browser_context_args):
    """创建自定义浏览器上下文"""
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context):
    """创建页面"""
    page = context.new_page()
    # 配置页面选项
    page.route("**/*.{png,jpg,jpeg,gif,svg}", lambda route: route.abort())  # 阻止加载图片，提高性能
    page.set_default_timeout(20000)  # 设置默认超时时间为20秒
    page.set_default_navigation_timeout(30000)  # 设置导航超时时间为30秒
    yield page
    page.close()
