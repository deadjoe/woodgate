"""
MCP服务器模块 - 实现Model Context Protocol服务器
使用Playwright替代Selenium实现更高效的浏览器自动化
"""

import os
import sys
import time
import logging
import asyncio
import subprocess
import importlib.util
import traceback
import urllib.parse
import json
from typing import List, Dict, Any, Optional, Tuple

# 环境变量应该在运行时设置，而不是硬编码在代码中
# 例如: export REDHAT_USERNAME="your_username" && export REDHAT_PASSWORD="your_password"

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 检查并安装必要的依赖
required_packages = ["playwright", "httpx"]

for package in required_packages:
    if importlib.util.find_spec(package) is None:
        logger.info(f"正在安装 {package}...")
        try:
            # 尝试使用uv安装
            try:
                subprocess.check_call(["uv", "pip", "install", package])
                logger.info(f"{package} 使用uv安装成功")

                # 如果是playwright，还需要安装浏览器
                if package == "playwright":
                    logger.info("安装Playwright浏览器...")
                    try:
                        subprocess.check_call(["playwright", "install", "chromium"])
                        logger.info("Playwright浏览器安装成功")
                    except Exception as e:
                        logger.warning(f"安装Playwright浏览器失败: {e}")
                        logger.warning("尝试使用Python模块安装浏览器...")
                        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
                        logger.info("Playwright浏览器安装成功")
            except Exception as e1:
                logger.warning(f"使用uv安装 {package} 失败: {e1}")
                # 尝试使用pip安装
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    logger.info(f"{package} 使用pip安装成功")

                    # 如果是playwright，还需要安装浏览器
                    if package == "playwright":
                        logger.info("安装Playwright浏览器...")
                        try:
                            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
                            logger.info("Playwright浏览器安装成功")
                        except Exception as e:
                            logger.warning(f"安装Playwright浏览器失败: {e}")
                except Exception as e2:
                    logger.warning(f"使用pip安装 {package} 失败: {e2}")
                    # 尝试使用系统pip安装
                    subprocess.check_call(["pip", "install", package])
                    logger.info(f"{package} 使用系统pip安装成功")

                    # 如果是playwright，还需要安装浏览器
                    if package == "playwright":
                        logger.info("安装Playwright浏览器...")
                        try:
                            subprocess.check_call(["playwright", "install", "chromium"])
                            logger.info("Playwright浏览器安装成功")
                        except Exception as e:
                            logger.warning(f"安装Playwright浏览器失败: {e}")
        except Exception as e:
            logger.error(f"安装 {package} 失败: {e}")
            logger.error("继续执行，但可能会导致功能不正常")

# 导入必要的模块
try:
    from mcp.server.fastmcp import FastMCP
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext, Playwright
except ImportError as e:
    logger.error(f"导入错误: {e}")
    raise

# 创建MCP服务器
mcp = FastMCP(
    name="Woodgate",
    instructions="Red Hat客户门户搜索工具，提供登录、搜索和文档获取功能。",
    log_level="DEBUG"  # 设置日志级别为DEBUG
)

# 添加自定义日志记录
logger.info("MCP服务器已创建: Woodgate - Red Hat客户门户搜索工具")

# 配置
REDHAT_PORTAL_URL = "https://access.redhat.com"
REDHAT_LOGIN_URL = "https://sso.redhat.com/auth/realms/redhat-external/login-actions/authenticate"
REDHAT_SEARCH_URL = "https://access.redhat.com/search"
REDHAT_DIRECT_LOGIN_URL = "https://access.redhat.com/login"
ALERTS_BASE_URL = "https://access.redhat.com/security/security-updates/"

# 可用产品列表
def available_products():
    """
    获取可用的产品列表

    Returns:
        List[str]: 产品名称列表
    """
    return [
        "Red Hat Enterprise Linux",
        "Red Hat OpenShift Container Platform",
        "Red Hat OpenStack Platform",
        "Red Hat Virtualization",
        "Red Hat Satellite",
        "Red Hat Ansible Automation Platform",
        "Red Hat JBoss Enterprise Application Platform",
        "Red Hat JBoss Web Server",
        "Red Hat Decision Manager",
        "Red Hat Process Automation Manager",
        "Red Hat Fuse",
        "Red Hat AMQ",
        "Red Hat Data Grid",
        "Red Hat Single Sign-On",
        "Red Hat OpenShift Dedicated",
        "Red Hat OpenShift Online",
        "Red Hat OpenShift Service on AWS",
        "Red Hat OpenShift Container Storage",
        "Red Hat Ceph Storage",
        "Red Hat Gluster Storage",
        "Red Hat Insights",
        "Red Hat CloudForms",
        "Red Hat Directory Server",
        "Red Hat Certificate System",
        "Red Hat Identity Management",
    ]

# 文档类型列表
def document_types():
    """
    获取可用的文档类型列表

    Returns:
        List[str]: 文档类型列表
    """
    return [
        "Solution",
        "Article",
        "Documentation",
        "Product Documentation",
        "Knowledgebase",
        "Blog",
        "Video",
        "Case",
        "Security Advisory",
        "Bug Fix",
        "Enhancement",
    ]

# 搜索参数配置
def search_params():
    """
    获取搜索参数配置

    Returns:
        Dict[str, Any]: 搜索参数配置
    """
    return {
        "sort_options": ["relevant", "newest", "oldest", "views"],
        "products": available_products(),
        "doc_types": document_types(),
        "default_rows": 20,
        "max_rows": 100,
    }


# 获取凭据
def get_credentials():
    """获取Red Hat客户门户凭据，优先使用环境变量，否则使用固定凭据"""
    logger.debug("获取凭据...")

    # 尝试从环境变量获取凭据
    username = os.environ.get("REDHAT_USERNAME")
    password = os.environ.get("REDHAT_PASSWORD")

    # 如果环境变量未设置，使用固定凭据
    if not username or not password:
        # 固定凭据，用于生产环境
        username = "smartjoe@gmail.com"
        password = "***REMOVED***"
        logger.info("使用固定凭据")
    else:
        logger.info("使用环境变量中的凭据")

    logger.debug(f"凭据获取成功: username='{username}'")
    return username, password


# 初始化浏览器
async def initialize_browser() -> Tuple[Optional[Playwright], Optional[Browser], Optional[BrowserContext], Optional[Page]]:
    """
    初始化Playwright浏览器

    Returns:
        Tuple[Optional[Playwright], Optional[Browser], Optional[BrowserContext], Optional[Page]]: 包含Playwright实例、浏览器实例、浏览器上下文和页面的元组
    """
    logger.debug("初始化Playwright浏览器...")

    playwright = None
    browser = None
    context = None
    page = None

    try:
        # 启动Playwright
        playwright = await async_playwright().start()
        if playwright is None:
            logger.error("Playwright启动失败，返回了None")
            return None, None, None, None

        # 启动浏览器，配置优化选项
        browser = await playwright.chromium.launch(
            headless=True,  # 启用无头模式，不显示浏览器窗口，提高运行效率
            args=[
                "--no-sandbox",  # 禁用沙箱，解决某些环境下的权限问题
                "--disable-dev-shm-usage",  # 解决在低内存环境中的崩溃问题
                "--disable-extensions",  # 禁用扩展，减少资源占用和干扰
                "--disable-gpu",  # 禁用GPU加速，提高在服务器环境下的兼容性
                "--disable-notifications",  # 禁用通知，避免弹窗干扰
            ]
        )
        if browser is None:
            logger.error("浏览器启动失败，返回了None")
            if playwright:
                await playwright.stop()
            return None, None, None, None

        # 创建浏览器上下文，配置视口大小和其他选项
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},  # 设置窗口大小，模拟标准显示器分辨率
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",  # 设置用户代理
            ignore_https_errors=True,  # 忽略HTTPS错误，提高兼容性
            java_script_enabled=True,  # 启用JavaScript
            has_touch=False,  # 禁用触摸，模拟桌面环境
        )
        if context is None:
            logger.error("浏览器上下文创建失败，返回了None")
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
            return None, None, None, None

        # 创建页面
        page = await context.new_page()
        if page is None:
            logger.error("页面创建失败，返回了None")
            if context:
                await context.close()
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
            return None, None, None, None

        # 配置页面选项
        try:
            # 使用同步方法设置超时，不使用await
            page.set_default_timeout(20000)  # 设置默认超时时间为20秒
            page.set_default_navigation_timeout(30000)  # 设置导航超时时间为30秒

            # 阻止加载图片，提高性能
            try:
                await page.route("**/*.{png,jpg,jpeg,gif,svg}", lambda route: route.abort())
            except Exception as e:
                logger.warning(f"设置路由时出错: {e}")
        except Exception as e:
            logger.warning(f"配置页面选项时出错: {e}")
            # 继续执行，不中断初始化过程

        logger.debug("浏览器初始化完成")
        return playwright, browser, context, page
    except Exception as e:
        logger.error(f"浏览器初始化失败: {e}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")

        # 安全关闭已创建的资源
        try:
            if page:
                await page.close()
        except Exception:
            pass

        try:
            if context:
                await context.close()
        except Exception:
            pass

        try:
            if browser:
                await browser.close()
        except Exception:
            pass

        try:
            if playwright:
                await playwright.stop()
        except Exception:
            pass

        return None, None, None, None


# 关闭浏览器
async def close_browser(
    playwright: Optional[Playwright] = None,
    browser: Optional[Browser] = None,
    context: Optional[BrowserContext] = None,
    page: Optional[Page] = None
) -> None:
    """
    安全关闭浏览器及相关资源

    Args:
        playwright: Playwright实例
        browser: 浏览器实例
        context: 浏览器上下文
        page: 页面实例
    """
    # 如果所有参数都是None，直接返回
    if playwright is None and browser is None and context is None and page is None:
        logger.debug("没有浏览器资源需要关闭")
        return

    try:
        # 关闭页面
        if page is not None:
            try:
                await page.close()
                logger.debug("页面已关闭")
            except Exception as e:
                logger.warning(f"关闭页面时出错: {e}")

        # 关闭浏览器上下文
        if context is not None:
            try:
                await context.close()
                logger.debug("浏览器上下文已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器上下文时出错: {e}")

        # 关闭浏览器
        if browser is not None:
            try:
                await browser.close()
                logger.debug("浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")

        # 停止Playwright
        if playwright is not None:
            try:
                await playwright.stop()
                logger.debug("Playwright已停止")
            except Exception as e:
                logger.warning(f"停止Playwright时出错: {e}")

        logger.debug("浏览器资源已完全释放")
    except Exception as e:
        logger.warning(f"关闭浏览器时出错: {e}")
        logger.debug(f"错误堆栈: {traceback.format_exc()}")


# 处理Cookie弹窗
async def handle_cookie_popup(page: Page, timeout: float = 1.0) -> bool:
    """
    处理网页上出现的cookie或隐私弹窗

    Args:
        page (Page): Playwright页面实例
        timeout (float, optional): 等待弹窗出现的超时时间(秒). Defaults to 1.0.

    Returns:
        bool: 如果成功处理了弹窗返回True，否则返回False
    """
    logger.debug("检查是否存在cookie通知...")

    try:
        # 设置较短的超时时间，避免在没有弹窗的情况下等待太久
        # 不使用get_default_timeout，因为在某些环境中可能不可用
        original_timeout = 30000  # 默认30秒
        try:
            page.set_default_timeout(timeout * 1000)  # 转换为毫秒
        except Exception:
            # 如果设置超时失败，继续执行
            pass

        # 优化：使用更高效的CSS选择器，减少DOM查询次数
        popup_selectors = [
            "#truste-consent-button",  # Red Hat特有的
            "#onetrust-banner-sdk",  # 最常见的
            ".pf-c-modal-box",  # Red Hat特有的
            "[role='dialog'][aria-modal='true']",  # 通用备选
            ".cookie-banner",  # 通用cookie横幅
            "#cookie-notice",  # 另一种常见的cookie通知
        ]

        # 检查是否存在cookie通知
        for selector in popup_selectors:
            try:
                # 使用waitForSelector而不是等待元素可见，提高效率
                cookie_notice = await page.wait_for_selector(selector, timeout=timeout * 1000, state="attached")
                if cookie_notice:
                    logger.debug(f"发现cookie通知，使用选择器: {selector}")
                    await cookie_notice.click()
                    logger.debug("已点击关闭按钮")
                    # 恢复默认超时时间
                    try:
                        page.set_default_timeout(original_timeout)
                    except Exception:
                        pass
                    return True
            except Exception:
                continue

        # 尝试通过文本内容查找按钮
        for button_text in ["Accept", "I agree", "Close", "OK", "接受", "同意", "关闭"]:
            try:
                # 使用text=按钮文本定位
                button = page.get_by_text(button_text, exact=False).first
                if button:
                    await button.click(timeout=1000)
                    logger.debug(f"找到并点击了文本为'{button_text}'的按钮")
                    # 恢复默认超时时间
                    try:
                        page.set_default_timeout(original_timeout)
                    except Exception:
                        pass
                    return True
            except Exception:
                continue

        # 恢复默认超时时间
        try:
            page.set_default_timeout(original_timeout)
        except Exception:
            pass
        logger.debug("未发现cookie通知")
        return False

    except Exception as e:
        # 恢复默认超时时间
        try:
            page.set_default_timeout(30000)
        except Exception:
            pass
        logger.debug(f"处理cookie通知时出错: {e}")
        return False


# 登录到Red Hat客户门户
async def take_screenshot(page: Page, name: str) -> None:
    """
    截图功能已禁用

    Args:
        page (Page): Playwright页面实例
        name (str): 截图名称
    """
    # 截图功能已禁用
    logger.debug(f"截图功能已禁用: {name}")
    pass

async def login_to_redhat_portal(page: Page, context: BrowserContext, username: str, password: str) -> bool:
    """
    登录到Red Hat客户门户

    Args:
        page (Page): Playwright页面实例
        context (BrowserContext): Playwright浏览器上下文
        username (str): Red Hat账号用户名
        password (str): Red Hat账号密码

    Returns:
        bool: 登录成功返回True，否则返回False
    """
    logger.info("=== 开始登录到Red Hat客户门户 ===")
    logger.info(f"使用凭据: username='{username}'")

    try:
        # 直接访问登录页面
        logger.info(f"直接访问登录页面: {REDHAT_DIRECT_LOGIN_URL}")
        print(f"直接访问登录页面: {REDHAT_DIRECT_LOGIN_URL}")

        try:
            # 设置更长的超时时间
            await page.set_default_navigation_timeout(60000)

            # 使用不同的等待策略
            await page.goto(REDHAT_DIRECT_LOGIN_URL, wait_until="domcontentloaded")
            logger.info("已加载登录页面")
            print("已加载登录页面")
            await take_screenshot(page, "login_page")
        except Exception as e:
            logger.error(f"访问登录页面时出错: {e}")
            print(f"访问登录页面时出错: {e}")

            # 尝试使用备用URL
            try:
                logger.info("尝试使用备用URL: https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/auth")
                print("尝试使用备用URL: https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/auth")
                await page.goto("https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/auth", wait_until="domcontentloaded")
                logger.info("已加载备用登录页面")
                print("已加载备用登录页面")
                await take_screenshot(page, "alternate_login_page")
            except Exception as e2:
                logger.error(f"访问备用登录页面时出错: {e2}")
                print(f"访问备用登录页面时出错: {e2}")
                await take_screenshot(page, "login_page_error")
                return False

        # 处理Cookie弹窗
        logger.info("处理Cookie弹窗...")
        cookie_handled = await handle_cookie_popup(page)
        logger.info(f"Cookie弹窗处理结果: {cookie_handled}")
        await take_screenshot(page, "after_cookie_popup")

        # 点击登录按钮
        logger.info("尝试点击登录按钮...")
        try:
            login_button = await page.get_by_text("Log In", exact=True).first()
            if login_button:
                logger.info("找到'Log In'按钮")
                await login_button.click()
                logger.info("已点击登录按钮")
                await take_screenshot(page, "after_login_button_click")
            else:
                # 尝试使用链接选择器
                logger.info("未找到'Log In'按钮，尝试使用链接选择器")
                login_locator = page.locator("a[href*='login']")
                count = await login_locator.count()
                logger.info(f"找到 {count} 个登录链接")
                if count > 0:
                    await login_locator.first().click()
                    logger.info("已点击登录链接")
                    await take_screenshot(page, "after_login_link_click")
                else:
                    logger.warning("未找到任何登录按钮或链接")
                    await take_screenshot(page, "no_login_button_found")
        except Exception as e:
            logger.warning(f"点击登录按钮时出错: {e}，可能已经在登录页面")
            # 可能已经在登录页面，尝试直接访问登录页面
            logger.info(f"直接访问登录页面: {REDHAT_DIRECT_LOGIN_URL}")
            await page.goto(REDHAT_DIRECT_LOGIN_URL, wait_until="networkidle")
            await take_screenshot(page, "direct_login_page")

        # 输入用户名
        logger.info("等待用户名输入框...")
        try:
            # 尝试多种选择器
            username_selectors = [
                "#username",
                "input[name='username']",
                "input[id='username']",
                "input[type='text'][name='username']",
                "input[placeholder*='username' i]",
                "input[placeholder*='email' i]"
            ]

            username_field = None
            for selector in username_selectors:
                try:
                    logger.info(f"尝试选择器: {selector}")
                    print(f"尝试选择器: {selector}")
                    username_field = await page.wait_for_selector(selector, state="visible", timeout=3000)
                    if username_field:
                        logger.info(f"找到用户名输入框，使用选择器: {selector}")
                        print(f"找到用户名输入框，使用选择器: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"选择器 {selector} 失败: {e}")
                    continue

            if username_field:
                logger.info("找到用户名输入框")
                await username_field.fill("")  # 清空
                await username_field.fill(username)  # 输入
                logger.info("已输入用户名")
                await take_screenshot(page, "after_username_input")
            else:
                # 尝试使用页面内容查找表单元素
                logger.info("尝试通过页面内容查找表单元素")
                print("尝试通过页面内容查找表单元素")

                # 获取页面内容
                page_content = await page.content()
                logger.debug(f"页面内容片段: {page_content[:500]}...")

                # 尝试使用JavaScript填充表单
                try:
                    logger.info("尝试使用JavaScript填充用户名")
                    print("尝试使用JavaScript填充用户名")
                    await page.evaluate(f'document.querySelector("input[type=text]").value = "{username}"')
                    logger.info("已使用JavaScript输入用户名")
                    await take_screenshot(page, "after_js_username_input")
                except Exception as e:
                    logger.error(f"使用JavaScript填充用户名失败: {e}")
                    await take_screenshot(page, "username_field_not_found")
                    return False
        except Exception as e:
            logger.error(f"等待用户名输入框时出错: {e}")
            await take_screenshot(page, "username_field_error")
            return False

        # 点击下一步按钮（如果存在）
        logger.info("检查是否存在下一步按钮...")
        try:
            next_button = await page.wait_for_selector("#login-show-step2", state="visible", timeout=3000)
            if next_button:
                logger.info("找到下一步按钮")
                await next_button.click()
                logger.info("已点击下一步按钮")
                await take_screenshot(page, "after_next_button_click")
            else:
                logger.info("未找到下一步按钮，可能是单步登录页面")
        except Exception as e:
            logger.info(f"检查下一步按钮时出错: {e}，可能是单步登录页面")

        # 输入密码
        logger.info("等待密码输入框...")
        try:
            password_field = await page.wait_for_selector("#password", state="visible", timeout=10000)
            if password_field:
                logger.info("找到密码输入框")
                await password_field.fill("")  # 清空
                await password_field.fill(password)  # 输入
                logger.info("已输入密码")
                await take_screenshot(page, "after_password_input")
            else:
                logger.error("未找到密码输入框")
                await take_screenshot(page, "password_field_not_found")
                return False
        except Exception as e:
            logger.error(f"等待密码输入框时出错: {e}")
            await take_screenshot(page, "password_field_error")
            return False

        # 点击登录按钮
        logger.info("等待登录按钮...")
        print("等待登录按钮...")
        try:
            # 尝试多种选择器
            login_button_selectors = [
                "#kc-login",
                "input[type='submit']",
                "button[type='submit']",
                "button.pf-c-button.pf-m-primary",
                "button:has-text('Log in')",
                "button:has-text('Sign in')",
                "button:has-text('Login')",
                "button:has-text('Submit')"
            ]

            login_button = None
            for selector in login_button_selectors:
                try:
                    logger.info(f"尝试登录按钮选择器: {selector}")
                    print(f"尝试登录按钮选择器: {selector}")
                    login_button = await page.wait_for_selector(selector, state="visible", timeout=2000)
                    if login_button:
                        logger.info(f"找到登录按钮，使用选择器: {selector}")
                        print(f"找到登录按钮，使用选择器: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"登录按钮选择器 {selector} 失败: {e}")
                    continue

            if login_button:
                logger.info("找到登录按钮")
                await login_button.click()
                logger.info("已点击登录按钮")
                await take_screenshot(page, "after_login_button_click")
            else:
                # 尝试使用JavaScript点击登录按钮
                logger.info("尝试使用JavaScript点击登录按钮")
                print("尝试使用JavaScript点击登录按钮")

                try:
                    # 尝试多种JavaScript方法
                    js_methods = [
                        "document.querySelector('input[type=\"submit\"]').click()",
                        "document.querySelector('button[type=\"submit\"]').click()",
                        "document.querySelector('button.pf-c-button.pf-m-primary').click()",
                        "Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('Log in') || el.textContent.includes('Sign in') || el.textContent.includes('Login')).click()",
                        "document.forms[0].submit()"
                    ]

                    for js_method in js_methods:
                        try:
                            logger.info(f"尝试JavaScript方法: {js_method}")
                            print(f"尝试JavaScript方法: {js_method}")
                            await page.evaluate(js_method)
                            logger.info("已使用JavaScript点击登录按钮")
                            print("已使用JavaScript点击登录按钮")
                            await take_screenshot(page, "after_js_login_button_click")
                            break
                        except Exception as e:
                            logger.debug(f"JavaScript方法 {js_method} 失败: {e}")
                            continue
                except Exception as e:
                    logger.error(f"使用JavaScript点击登录按钮失败: {e}")
                    print(f"使用JavaScript点击登录按钮失败: {e}")
                    await take_screenshot(page, "login_button_not_found")
                    return False
        except Exception as e:
            logger.error(f"等待登录按钮时出错: {e}")
            print(f"等待登录按钮时出错: {e}")
            await take_screenshot(page, "login_button_error")
            return False

        # 等待登录完成
        logger.info("等待登录完成...")
        try:
            # 使用更灵活的选择器组合，任何一个匹配就表示登录成功
            success_selectors = [
                ".pf-c-page__header",
                ".rh-header-logo",
                ".pf-c-nav__link",
                ".user-name",
                ".pf-c-dropdown__toggle-text",
                "a:has-text('My account')",
                ".pf-c-page",
                "#rh-header",
                ".pf-c-masthead",
                ".pf-c-toolbar",
                ".pf-c-content"
            ]

            # 尝试每个选择器
            for selector in success_selectors:
                try:
                    logger.info(f"尝试登录成功选择器: {selector}")
                    await page.wait_for_selector(selector, state="visible", timeout=5000)
                    logger.info(f"登录成功！已检测到元素: {selector}")

                    # 获取并打印cookies
                    cookies = await context.cookies()
                    logger.info(f"登录后的cookies数量: {len(cookies)}")
                    for cookie in cookies:
                        if cookie.get('name') in ['JSESSIONID', 'rh_sso_session', 'rh_user']:
                            logger.info(f"重要Cookie: {cookie.get('name')}={cookie.get('value')[:10]}...")

                    return True
                except Exception:
                    continue

            # 检查URL是否表明登录成功
            current_url = page.url
            logger.info(f"当前URL: {current_url}")
            if "login" not in current_url and ("access.redhat.com" in current_url or "customer-portal" in current_url):
                logger.info("基于URL判断登录成功")

                # 获取并打印cookies
                cookies = await context.cookies()
                logger.info(f"登录后的cookies数量: {len(cookies)}")
                for cookie in cookies:
                    if cookie.get('name') in ['JSESSIONID', 'rh_sso_session', 'rh_user']:
                        logger.info(f"重要Cookie: {cookie.get('name')}={cookie.get('value')[:10]}...")

                return True

            # 如果所有选择器都失败，则检查页面内容
            logger.warning("所有登录成功选择器都未找到，检查页面内容")

            # 检查页面内容是否表明登录成功
            page_content = await page.content()
            success_indicators = ["My account", "Log out", "Sign out", "Customer Portal", "Red Hat Customer Portal"]
            for indicator in success_indicators:
                if indicator in page_content:
                    logger.info(f"基于页面内容判断登录成功，找到文本: {indicator}")

                    # 获取并打印cookies
                    cookies = await context.cookies()
                    logger.info(f"登录后的cookies数量: {len(cookies)}")
                    for cookie in cookies:
                        if cookie.get('name') in ['JSESSIONID', 'rh_sso_session', 'rh_user']:
                            logger.info(f"重要Cookie: {cookie.get('name')}={cookie.get('value')[:10]}...")

                    return True

            logger.error("无法确认登录成功")
            return False
        except Exception as e:
            logger.error(f"等待登录完成时出错: {e}")

            # 检查是否有错误消息
            try:
                error_selector = ".kc-feedback-text, .alert-error, .pf-c-alert__title"
                error_element = await page.wait_for_selector(error_selector, state="visible", timeout=3000)
                if error_element:
                    error_text = await error_element.text_content()
                    logger.error(f"登录失败: {error_text}")
            except Exception as e2:
                logger.warning(f"检查错误消息时出错: {e2}")

            # 尝试获取页面内容
            try:
                page_content = await page.content()
                logger.debug(f"页面内容片段: {page_content[:500]}...")
            except Exception as e3:
                logger.warning(f"获取页面内容时出错: {e3}")

            return False

    except Exception as e:
        logger.error(f"登录过程中出错: {e}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        await take_screenshot(page, "login_exception")
        return False


# 执行搜索
async def perform_search(
    page: Page, query: str, products=None, doc_types=None, page_num: int = 1, rows: int = 20, sort_by: str = "relevant"
) -> List[Dict[str, Any]]:
    """
    在Red Hat客户门户执行搜索

    Args:
        page (Page): Playwright页面实例
        query (str): 搜索关键词
        products (List[str], optional): 要搜索的产品列表. Defaults to None.
        doc_types (List[str], optional): 文档类型列表. Defaults to None.
        page_num (int, optional): 页码. Defaults to 1.
        rows (int, optional): 每页结果数. Defaults to 20.
        sort_by (str, optional): 排序方式. Defaults to "relevant".

    Returns:
        List[Dict[str, Any]]: 搜索结果列表
    """
    try:
        # 构建搜索URL
        encoded_query = urllib.parse.quote(query)
        search_url = f"{REDHAT_SEARCH_URL}?q={encoded_query}&p={page_num}&rows={rows}&sort={sort_by}"

        # 添加产品过滤
        if products:
            for product in products:
                encoded_product = urllib.parse.quote(product)
                search_url += f"&product={encoded_product}"

        # 添加文档类型过滤
        if doc_types:
            for doc_type in doc_types:
                encoded_doc_type = urllib.parse.quote(doc_type)
                search_url += f"&documentKind={encoded_doc_type}"

        logger.debug(f"搜索URL: {search_url}")

        # 访问搜索页面
        await page.goto(search_url, wait_until="networkidle")
        logger.debug("已加载搜索页面")

        # 处理可能出现的Cookie弹窗
        await handle_cookie_popup(page)

        # 等待搜索结果加载
        try:
            # 尝试多个选择器，任何一个匹配就表示页面已加载
            selectors = [
                ".pf-c-page__main-section",
                ".pf-c-content",
                ".pf-c-page",
                ".search-result",
                ".pf-c-card",
                "main",
                "#rh-main",
                "article"
            ]

            page_loaded = False
            for selector in selectors:
                try:
                    logger.debug(f"尝试等待选择器: {selector}")
                    await page.wait_for_selector(selector, state="visible", timeout=5000)
                    logger.debug(f"页面已加载，找到选择器: {selector}")
                    page_loaded = True
                    break
                except Exception:
                    continue

            if not page_loaded:
                # 如果所有选择器都失败，检查URL是否表明页面已加载
                current_url = page.url
                logger.debug(f"当前URL: {current_url}")
                if "search" in current_url and "redhat.com" in current_url:
                    logger.debug("基于URL判断页面已加载")
                    page_loaded = True
                else:
                    # 等待一段时间，然后继续
                    logger.debug("等待5秒后继续")
                    await asyncio.sleep(5)

            if not page_loaded:
                logger.warning("无法确认页面已加载，但将继续尝试提取结果")
        except Exception as e:
            logger.error(f"等待页面加载时出错: {e}")
            # 继续尝试提取结果，而不是立即返回空列表

        # 检查是否有搜索结果
        search_elements = []
        results = []

        try:
            # 使用更多的选择器来查找搜索结果
            selectors = [
                ".pf-c-card",
                ".search-result",
                ".co-search-result",
                "article",
                ".pf-c-content article",
                "div[data-testid='search-result']",
                ".pf-c-card__body",
                "main .pf-l-grid__item"
            ]

            # 尝试使用各种选择器查找结果元素
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        logger.debug(f"使用选择器 {selector} 找到 {len(elements)} 个结果")
                        search_elements = elements
                        break
                except Exception:
                    continue

            # 如果找到了结果元素
            if search_elements and len(search_elements) > 0:
                logger.debug(f"找到 {len(search_elements)} 个搜索结果")
            else:
                # 如果没有找到结果，尝试获取页面内容
                logger.debug("未找到搜索结果元素，尝试替代方法")

                # 尝试检查页面内容
                try:
                    page_content = await page.content()
                    logger.debug("获取到页面内容，长度: " + str(len(page_content)))

                    # 保存页面内容到日志，方便调试
                    logger.debug("页面内容前1000字符: " + page_content[:1000])

                    # 检查是否明确显示没有结果
                    if "No results found" in page_content or "没有找到结果" in page_content:
                        logger.debug("页面明确显示没有找到结果")
                        # 不要立即返回，继续尝试其他方法
                    else:
                        logger.debug("页面没有明确显示'没有找到结果'")
                except Exception as e:
                    logger.warning(f"获取页面内容时出错: {e}")

                # 尝试使用链接选择器
                search_selectors = [
                    "main .search-result a",
                    "main .pf-c-card a",
                    "main article a",
                    "main .pf-c-content a",
                    "main .co-search-result a",
                    "main div[data-testid='search-result'] a",
                    "main .pf-c-card__body a",
                    "main .pf-l-grid__item a"
                ]

                for selector in search_selectors:
                    try:
                        links = await page.query_selector_all(selector)
                        if links and len(links) > 0:
                            logger.debug(f"使用选择器 {selector} 找到 {len(links)} 个结果链接")

                            # 提取链接信息
                            for link in links:
                                try:
                                    title = await link.text_content()
                                    url = await link.get_attribute("href")
                                    if title and url and "login" not in url.lower():
                                        # 过滤掉导航链接和其他非搜索结果链接
                                        if (len(title.strip()) > 5 and
                                            ("solution" in url.lower() or
                                             "article" in url.lower() or
                                             "documentation" in url.lower() or
                                             "troubleshooting" in url.lower() or
                                             "kubernetes" in url.lower())):
                                            results.append({
                                                "title": title.strip(),
                                                "url": url,
                                                "summary": "无摘要",
                                                "doc_type": "未知类型",
                                                "last_updated": "未知日期"
                                            })
                                except Exception:
                                    continue

                            if results:
                                logger.debug(f"通过选择器 {selector} 提取找到 {len(results)} 个结果")
                                return results
                    except Exception:
                        continue

                # 如果特定选择器都失败了，尝试使用更通用的方法
                try:
                    # 尝试直接查找搜索结果容器
                    result_containers = await page.query_selector_all(".search-result, .pf-c-card, article.co-search-result")
                    if result_containers and len(result_containers) > 0:
                        logger.debug(f"找到 {len(result_containers)} 个搜索结果容器")

                        # 提取结果信息
                        for container in result_containers:
                            try:
                                # 提取标题和URL
                                title_element = await container.query_selector("h2 a, h3 a, .pf-c-title a, a.co-search-result__title")
                                if not title_element:
                                    continue

                                title = await title_element.text_content()
                                url = await title_element.get_attribute("href")

                                # 提取摘要
                                summary = "无摘要"
                                summary_element = await container.query_selector(".co-search-result__description, .search-result-content, .pf-c-card__body p")
                                if summary_element:
                                    summary_text = await summary_element.text_content()
                                    summary = summary_text.strip() if summary_text else "无摘要"

                                # 提取文档类型
                                doc_type = "未知类型"
                                doc_type_element = await container.query_selector(".co-search-result__kind, .search-result-info span, .pf-c-label")
                                if doc_type_element:
                                    doc_type_text = await doc_type_element.text_content()
                                    doc_type = doc_type_text.strip() if doc_type_text else "未知类型"

                                # 提取最后更新时间
                                last_updated = "未知日期"
                                date_element = await container.query_selector(".co-search-result__date, .search-result-info time, .pf-c-label[data-testid='date']")
                                if date_element:
                                    date_text = await date_element.text_content()
                                    last_updated = date_text.strip() if date_text else "未知日期"

                                if title and url and "login" not in url.lower():
                                    results.append({
                                        "title": title.strip(),
                                        "url": url,
                                        "summary": summary,
                                        "doc_type": doc_type,
                                        "last_updated": last_updated
                                    })
                            except Exception as e:
                                logger.warning(f"提取搜索结果容器时出错: {e}")
                                continue

                        if results:
                            logger.debug(f"通过搜索结果容器提取找到 {len(results)} 个结果")
                            return results

                    # 如果没有找到搜索结果容器，尝试提取所有链接
                    links = await page.query_selector_all("a[href*='access.redhat.com/solutions'], a[href*='access.redhat.com/articles']")
                    if links and len(links) > 0:
                        logger.debug(f"找到 {len(links)} 个可能的结果链接")

                        # 提取链接信息
                        for link in links:
                            try:
                                title = await link.text_content()
                                url = await link.get_attribute("href")
                                if title and url and "login" not in url.lower():
                                    # 过滤掉导航链接和其他非搜索结果链接
                                    if (len(title.strip()) > 5 and
                                        (url.lower().startswith("https://access.redhat.com/solutions/") or
                                         url.lower().startswith("https://access.redhat.com/articles/")) and
                                        not any(x in url.lower() for x in [
                                            "?q=*", "search/?", "downloads", "management", "support/cases",
                                            "products", "community", "security/updates",
                                            "changeLanguage", "user/edit", "groups"
                                        ])):
                                        results.append({
                                            "title": title.strip(),
                                            "url": url,
                                            "summary": "无摘要",
                                            "doc_type": "未知类型",
                                            "last_updated": "未知日期"
                                        })
                            except Exception:
                                continue

                        if results:
                            logger.debug(f"通过链接提取找到 {len(results)} 个结果")
                            return results
                except Exception as e:
                    logger.warning(f"尝试提取链接时出错: {e}")

                # 如果所有尝试都失败，返回空结果
                logger.debug("所有方法都未找到搜索结果")
                return []

        except Exception as e:
            logger.error(f"检查搜索结果时出错: {e}")
            return []

        # 如果没有找到结果元素，尝试再次查询
        if not search_elements or len(search_elements) == 0:
            try:
                search_elements = await page.query_selector_all(".pf-c-card, .search-result")
                logger.debug(f"重新查询找到 {len(search_elements)} 个搜索结果")
            except Exception as e:
                logger.error(f"重新查询搜索结果时出错: {e}")
                search_elements = []

        for element in search_elements:
            try:
                # 提取标题和URL
                title_element = await element.query_selector("h2 a, .pf-c-title a")
                if not title_element:
                    continue

                title = await title_element.text_content()
                title = title.strip() if title else "未知标题"
                url = await title_element.get_attribute("href")

                # 提取摘要
                summary = "无摘要"
                summary_element = await element.query_selector(
                    ".co-search-result__description, .search-result-content, .pf-c-card__body"
                )
                if summary_element:
                    summary_text = await summary_element.text_content()
                    summary = summary_text.strip() if summary_text else "无摘要"

                # 提取文档类型
                doc_type = "未知类型"
                doc_type_element = await element.query_selector(
                    ".co-search-result__kind, .search-result-info span, .pf-c-label"
                )
                if doc_type_element:
                    doc_type_text = await doc_type_element.text_content()
                    doc_type = doc_type_text.strip() if doc_type_text else "未知类型"

                # 提取最后更新时间
                last_updated = "未知日期"
                date_element = await element.query_selector(
                    ".co-search-result__date, .search-result-info time, .pf-c-label[data-testid='date']"
                )
                if date_element:
                    date_text = await date_element.text_content()
                    last_updated = date_text.strip() if date_text else "未知日期"

                results.append(
                    {
                        "title": title,
                        "url": url,
                        "summary": summary,
                        "doc_type": doc_type,
                        "last_updated": last_updated,
                    }
                )
            except Exception as e:
                logger.error(f"提取搜索结果时出错: {e}")
                logger.debug(f"错误堆栈: {traceback.format_exc()}")
                continue

        logger.debug(f"成功提取 {len(results)} 个搜索结果")
        return results
    except Exception as e:
        logger.error(f"执行搜索时出错: {e}")
        logger.debug(f"错误堆栈: {traceback.format_exc()}")
        return []


# 获取产品警报
async def get_product_alerts(page: Page, product: str) -> List[Dict[str, Any]]:
    """
    获取特定产品的警报信息

    Args:
        page (Page): Playwright页面实例
        product (str): 产品名称

    Returns:
        List[Dict[str, Any]]: 警报信息列表
    """
    try:
        # 构建警报URL
        encoded_product = urllib.parse.quote(product)
        alerts_url = f"{REDHAT_PORTAL_URL}/products/{encoded_product}/alerts"
        logger.debug(f"警报URL: {alerts_url}")

        # 访问警报页面
        await page.goto(alerts_url, wait_until="networkidle")
        logger.debug("已加载警报页面")

        # 处理可能出现的Cookie弹窗
        await handle_cookie_popup(page)

        # 等待警报加载
        try:
            await page.wait_for_selector(".pf-c-page__main-section", state="visible", timeout=20000)
            logger.debug("页面主体已加载")
        except Exception as e:
            logger.error(f"等待页面加载时出错: {e}")
            return []

        # 提取警报信息
        alerts = []
        alert_elements = await page.query_selector_all(".pf-c-card, .portal-advisory")
        logger.debug(f"找到 {len(alert_elements)} 个警报元素")

        for element in alert_elements:
            try:
                # 提取标题和URL
                title_element = await element.query_selector("h2 a, .pf-c-title a")
                if not title_element:
                    continue

                title = await title_element.text_content()
                title = title.strip() if title else "未知标题"
                url = await title_element.get_attribute("href")

                # 提取摘要
                summary = "无摘要"
                summary_element = await element.query_selector(
                    ".co-alert__description, .portal-advisory-synopsis, .pf-c-card__body"
                )
                if summary_element:
                    summary_text = await summary_element.text_content()
                    summary = summary_text.strip() if summary_text else "无摘要"

                # 提取严重性
                severity = "未知严重性"
                severity_element = await element.query_selector(
                    ".co-alert__severity, .security-severity, .pf-c-label"
                )
                if severity_element:
                    severity_text = await severity_element.text_content()
                    severity = severity_text.strip() if severity_text else "未知严重性"

                # 提取发布日期
                published_date = "未知日期"
                date_element = await element.query_selector(
                    ".co-alert__date, .portal-advisory-date, time"
                )
                if date_element:
                    date_text = await date_element.text_content()
                    published_date = date_text.strip() if date_text else "未知日期"

                alerts.append(
                    {
                        "title": title,
                        "url": url,
                        "summary": summary,
                        "severity": severity,
                        "published_date": published_date,
                    }
                )
            except Exception as e:
                logger.error(f"提取警报信息时出错: {e}")
                logger.debug(f"错误堆栈: {traceback.format_exc()}")
                continue

        logger.debug(f"成功提取 {len(alerts)} 个警报")
        return alerts
    except Exception as e:
        logger.error(f"获取产品警报时出错: {e}")
        logger.debug(f"错误堆栈: {traceback.format_exc()}")
        return []


# 获取文档内容
async def get_document_content(page: Page, document_url: str) -> Dict[str, Any]:
    """
    获取特定文档的详细内容

    Args:
        page (Page): Playwright页面实例
        document_url (str): 文档URL

    Returns:
        Dict[str, Any]: 文档内容
    """
    try:
        # 访问文档页面
        await page.goto(document_url, wait_until="networkidle")
        logger.debug("已加载文档页面")

        # 处理可能出现的Cookie弹窗
        await handle_cookie_popup(page)

        # 等待文档加载
        try:
            await page.wait_for_selector(".pf-c-page__main-section", state="visible", timeout=20000)
            logger.debug("页面主体已加载")
        except Exception as e:
            logger.error(f"等待页面加载时出错: {e}")
            return {"error": "无法加载文档内容"}

        # 提取文档标题
        title = "未知标题"
        title_element = await page.query_selector("h1, .pf-c-title")
        if title_element:
            title_text = await title_element.text_content()
            title = title_text.strip() if title_text else "未知标题"

        # 提取文档内容
        content = "无法提取文档内容"
        content_element = await page.query_selector(".pf-c-content, .field-item, article")
        if content_element:
            content_text = await content_element.text_content()
            content = content_text.strip() if content_text else "无法提取文档内容"

        # 提取文档元数据
        metadata = {}
        try:
            # 尝试提取各种可能的元数据字段
            metadata_fields = await page.query_selector_all(".field, .pf-c-description-list__group")

            for field in metadata_fields:
                try:
                    label_element = await field.query_selector(".field-label, .pf-c-description-list__term")
                    value_element = await field.query_selector(".field-item, .pf-c-description-list__description")

                    if label_element and value_element:
                        label_text = await label_element.text_content()
                        value_text = await value_element.text_content()

                        label = label_text.strip().rstrip(":") if label_text else ""
                        value = value_text.strip() if value_text else ""

                        if label and value:
                            metadata[label] = value
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"提取文档元数据时出错: {e}")

        return {"title": title, "url": document_url, "content": content, "metadata": metadata}
    except Exception as e:
        logger.error(f"获取文档内容时出错: {e}")
        logger.debug(f"错误堆栈: {traceback.format_exc()}")
        return {"title": "错误", "url": document_url, "content": f"获取文档内容时出错: {str(e)}"}


# 可用产品列表
def get_available_products():
    """获取可用的产品列表"""
    return [
        "Red Hat Enterprise Linux",
        "Red Hat OpenShift Container Platform",
        "Red Hat OpenStack Platform",
        "Red Hat Virtualization",
        "Red Hat Satellite",
        "Red Hat Ansible Automation Platform",
        "Red Hat JBoss Enterprise Application Platform",
        "Red Hat Ceph Storage",
        "Red Hat Gluster Storage",
        "Red Hat OpenShift Service on AWS",
        "Red Hat OpenShift Dedicated",
        "Red Hat OpenShift Online",
        "Red Hat Quay",
        "Red Hat Advanced Cluster Management",
        "Red Hat Advanced Cluster Security",
        "Red Hat Integration",
        "Red Hat Process Automation",
        "Red Hat Decision Manager",
        "Red Hat Fuse",
        "Red Hat AMQ",
    ]


# 可用文档类型
def get_document_types():
    """获取可用的文档类型"""
    return [
        "Solution",
        "Article",
        "Documentation",
        "Video",
        "Blog",
        "Book",
        "FAQ",
        "Knowledgebase",
        "Troubleshoot",
    ]


@mcp.tool()
async def search(
    query: str,
    products: Optional[List[str]] = None,
    doc_types: Optional[List[str]] = None,
    page: int = 1,
    rows: int = 20,
    sort_by: str = "relevant",
) -> List[Dict[str, Any]]:
    """
    在Red Hat客户门户中执行搜索

    Args:
        query: 搜索关键词
        products: 要搜索的产品列表，例如 ["Red Hat Enterprise Linux", "Red Hat OpenShift"]
        doc_types: 文档类型列表，例如 ["Solution", "Article"]
        page: 页码
        rows: 每页结果数
        sort_by: 排序方式，可选值: "relevant", "lastModifiedDate desc", "lastModifiedDate asc"

    Returns:
        搜索结果列表
    """
    print(f"搜索函数开始执行，参数: query='{query}', products={products}, doc_types={doc_types}, page={page}, rows={rows}, sort_by='{sort_by}'")
    logger.info(f"搜索函数开始执行，参数: query='{query}', products={products}, doc_types={doc_types}, page={page}, rows={rows}, sort_by='{sort_by}'")

    # 确保 products 和 doc_types 是列表
    if products is None:
        products = []
    elif isinstance(products, str):
        # 如果是字符串，尝试解析为列表
        try:
            import json
            products = json.loads(products)
            if not isinstance(products, list):
                products = [products]
        except Exception as e:
            print(f"解析products参数失败: {e}")
            logger.warning(f"解析products参数失败: {e}")
            # 如果解析失败，将其作为单个产品
            products = [products]

    if doc_types is None:
        doc_types = []
    elif isinstance(doc_types, str):
        # 如果是字符串，尝试解析为列表
        try:
            import json
            doc_types = json.loads(doc_types)
            if not isinstance(doc_types, list):
                doc_types = [doc_types]
        except Exception as e:
            print(f"解析doc_types参数失败: {e}")
            logger.warning(f"解析doc_types参数失败: {e}")
            # 如果解析失败，将其作为单个文档类型
            doc_types = [doc_types]

    print(f"处理后的参数: products={products}, doc_types={doc_types}")
    logger.info(f"处理后的参数: products={products}, doc_types={doc_types}")

    playwright = None
    browser = None
    context = None
    page_obj = None

    try:
        print("初始化浏览器...")
        logger.info("初始化浏览器...")
        playwright, browser, context, page_obj = await initialize_browser()
        if playwright is None or browser is None or context is None or page_obj is None:
            print("浏览器初始化失败，某些组件为None")
            logger.error("浏览器初始化失败，某些组件为None")
            return [{"error": "浏览器初始化失败，某些组件为None"}]
        print("浏览器初始化成功")
        logger.info("浏览器初始化成功")

        print("获取凭据...")
        logger.info("获取凭据...")
        try:
            username, password = get_credentials()
            print(f"凭据获取成功: username='{username}'")
            logger.info(f"凭据获取成功: username='{username}'")
        except Exception as e:
            print(f"获取凭据失败: {e}")
            logger.error(f"获取凭据失败: {e}")
            return [{"error": f"获取凭据失败: {str(e)}"}]

        print("登录到Red Hat客户门户...")
        logger.info("登录到Red Hat客户门户...")
        login_success = await login_to_redhat_portal(page_obj, context, username, password)
        print(f"登录结果: {login_success}")
        logger.info(f"登录结果: {login_success}")

        if not login_success:
            print("登录失败，请检查凭据")
            logger.error("登录失败，请检查凭据")
            return [{"error": "登录失败，请检查凭据"}]

        print("执行搜索...")
        logger.info("执行搜索...")
        results = await perform_search(
            page_obj,
            query=query,
            products=products,
            doc_types=doc_types,
            page_num=page,
            rows=rows,
            sort_by=sort_by,
        )
        print(f"搜索完成，找到 {len(results)} 条结果")
        logger.info(f"搜索完成，找到 {len(results)} 条结果")
        return results
    except Exception as e:
        print(f"搜索过程中出错: {e}")
        print(f"错误堆栈: {traceback.format_exc()}")
        logger.error(f"搜索过程中出错: {e}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return [{"error": f"搜索过程中出错: {str(e)}"}]
    finally:
        try:
            # 安全地关闭浏览器
            print("关闭浏览器...")
            logger.info("关闭浏览器...")
            await close_browser(playwright, browser, context, page_obj)
            print("浏览器已关闭")
            logger.info("浏览器已关闭")
        except Exception as e:
            print(f"关闭浏览器时出错: {e}")
            logger.warning(f"关闭浏览器时出错: {e}")


@mcp.tool()
async def get_alerts(product: str) -> List[Dict[str, Any]]:
    """
    获取特定产品的警报信息

    Args:
        product: 产品名称，例如 "Red Hat Enterprise Linux"

    Returns:
        警报信息列表
    """
    logger.info(f"获取产品警报: '{product}'")

    playwright = None
    browser = None
    context = None
    page_obj = None

    try:
        playwright, browser, context, page_obj = await initialize_browser()
        if playwright is None or browser is None or context is None or page_obj is None:
            logger.error("浏览器初始化失败，某些组件为None")
            return [{"error": "浏览器初始化失败，某些组件为None"}]

        try:
            username, password = get_credentials()
            logger.debug(f"凭据获取成功: username='{username}'")
        except Exception as e:
            logger.error(f"获取凭据失败: {e}")
            return [{"error": f"获取凭据失败: {str(e)}"}]

        login_success = await login_to_redhat_portal(page_obj, context, username, password)
        if not login_success:
            return [{"error": "登录失败，请检查凭据"}]

        alerts = await get_product_alerts(page_obj, product)
        return alerts
    except Exception as e:
        logger.error(f"获取警报过程中出错: {e}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return [{"error": f"获取警报过程中出错: {str(e)}"}]
    finally:
        try:
            # 安全地关闭浏览器
            await close_browser(playwright, browser, context, page_obj)
            logger.debug("浏览器已关闭")
        except Exception as e:
            logger.warning(f"关闭浏览器时出错: {e}")


@mcp.tool()
async def get_document(document_url: str) -> Dict[str, Any]:
    """
    获取特定文档的详细内容

    Args:
        document_url: 文档URL

    Returns:
        文档内容
    """
    logger.info(f"获取文档内容: {document_url}")

    playwright = None
    browser = None
    context = None
    page_obj = None

    try:
        playwright, browser, context, page_obj = await initialize_browser()
        if playwright is None or browser is None or context is None or page_obj is None:
            logger.error("浏览器初始化失败，某些组件为None")
            return {"error": "浏览器初始化失败，某些组件为None"}

        try:
            username, password = get_credentials()
            logger.debug(f"凭据获取成功: username='{username}'")
        except Exception as e:
            logger.error(f"获取凭据失败: {e}")
            return {"error": f"获取凭据失败: {str(e)}"}

        login_success = await login_to_redhat_portal(page_obj, context, username, password)
        if not login_success:
            return {"error": "登录失败，请检查凭据"}

        document = await get_document_content(page_obj, document_url)
        return document
    except Exception as e:
        logger.error(f"获取文档内容过程中出错: {e}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return {"error": f"获取文档内容过程中出错: {str(e)}"}
    finally:
        try:
            # 安全地关闭浏览器
            await close_browser(playwright, browser, context, page_obj)
            logger.debug("浏览器已关闭")
        except Exception as e:
            logger.warning(f"关闭浏览器时出错: {e}")


@mcp.resource("config://products")
def available_products() -> List[str]:
    """获取可用的产品列表"""
    return get_available_products()


@mcp.resource("config://doc-types")
def document_types() -> List[str]:
    """获取可用的文档类型"""
    return get_document_types()


@mcp.prompt()
def search_help() -> str:
    """提供搜索帮助信息"""
    return """
    # Red Hat 客户门户搜索帮助

    您可以使用以下参数进行搜索：

    - **query**: 搜索关键词，例如 "memory leak"
    - **products**: 要搜索的产品列表，例如 ["Red Hat Enterprise Linux", "Red Hat OpenShift"]
    - **doc_types**: 文档类型列表，例如 ["Solution", "Article"]
    - **page**: 页码，默认为1
    - **rows**: 每页结果数，默认为20
    - **sort_by**: 排序方式，可选值: "relevant", "lastModifiedDate desc", "lastModifiedDate asc"

    示例：search(query="kubernetes troubleshooting", products=["Red Hat OpenShift Container Platform"], doc_types=["Solution"])
    """


@mcp.prompt()
def search_example() -> str:
    """提供搜索示例"""
    return """
    # Red Hat 客户门户搜索示例

    ## 基本搜索
    ```python
    search(query="memory leak")
    ```

    ## 带产品过滤的搜索
    ```python
    search(
        query="kubernetes pod crash",
        products=["Red Hat OpenShift Container Platform"]
    )
    ```

    ## 带文档类型过滤的搜索
    ```python
    search(
        query="selinux permission denied",
        doc_types=["Solution", "Article"]
    )
    ```

    ## 完整搜索示例
    ```python
    search(
        query="performance tuning",
        products=["Red Hat Enterprise Linux"],
        doc_types=["Solution", "Article", "Documentation"],
        page=1,
        rows=50,
        sort_by="lastModifiedDate desc"
    )
    ```

    ## 获取产品警报
    ```python
    get_alerts(product="Red Hat Enterprise Linux")
    ```

    ## 获取文档内容
    ```python
    get_document(document_url="https://access.redhat.com/solutions/12345")
    ```
    """
