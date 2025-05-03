"""
认证模块 - 处理Red Hat客户门户的登录和会话管理
使用Playwright替代Selenium实现更高效的浏览器自动化
"""

import asyncio
import logging
import traceback
from typing import Optional
from playwright.async_api import Page, BrowserContext

from .utils import log_step, print_cookies, handle_cookie_popup

logger = logging.getLogger(__name__)

# Red Hat客户门户登录URL
LOGIN_URL = "https://sso.redhat.com/auth/realms/redhat-external/login-actions/authenticate"
MANAGEMENT_URL = "https://access.redhat.com/management"


async def login_to_redhat_portal(
    page: Page, context: BrowserContext, username: str, password: str, max_retries: int = 3
) -> bool:
    """
    登录到Red Hat客户门户

    Args:
        page (Page): Playwright页面实例
        context (BrowserContext): Playwright浏览器上下文
        username (str): Red Hat账号用户名
        password (str): Red Hat账号密码
        max_retries (int, optional): 最大重试次数. Defaults to 3.

    Returns:
        bool: 登录成功返回True，否则返回False
    """
    log_step(f"开始登录Red Hat客户门户 (用户: {username})")

    # 访问登录页面
    try:
        await page.goto("https://access.redhat.com/login", wait_until="domcontentloaded")
        log_step("已加载登录页面")
    except Exception as e:
        logger.error(f"加载登录页面失败: {e}")
        logger.debug(f"错误堆栈: {traceback.format_exc()}")
        return False

    # 处理可能出现的Cookie弹窗
    await handle_cookie_popup(page, timeout=2)

    # 重试登录，处理可能的网络问题或页面加载延迟
    for attempt in range(max_retries):
        try:
            log_step(f"登录尝试 {attempt + 1}/{max_retries}")

            # 等待用户名输入框出现
            username_field = await page.wait_for_selector("#username", state="visible", timeout=10000)
            if username_field:
                # 清空并输入用户名
                await username_field.fill("")  # 清空
                await username_field.fill(username)  # 输入
                log_step("已输入用户名")
            else:
                logger.warning("未找到用户名输入框")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    await page.reload()
                    continue
                else:
                    return False

            # 等待密码输入框出现
            password_field = await page.wait_for_selector("#password", state="visible", timeout=5000)
            if password_field:
                # 清空并输入密码
                await password_field.fill("")  # 清空
                await password_field.fill(password)  # 输入
                log_step("已输入密码")
            else:
                logger.warning("未找到密码输入框")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    await page.reload()
                    continue
                else:
                    return False

            # 点击登录按钮
            login_button = await page.wait_for_selector("#kc-login", state="visible", timeout=5000)
            if login_button:
                await login_button.click()
                log_step("已点击登录按钮")
            else:
                logger.warning("未找到登录按钮")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    await page.reload()
                    continue
                else:
                    return False

            # 等待登录完成，检查是否成功
            try:
                # 等待页面加载完成，检查是否有用户菜单或个人资料元素
                success_selector = ".pf-c-dropdown__toggle-text, .user-name, .pf-c-nav__link"
                await page.wait_for_selector(success_selector, state="visible", timeout=15000)
                log_step("登录成功！已检测到用户菜单元素")

                # 打印Cookie信息，用于诊断
                await print_cookies(context, "登录成功后")

                return True
            except Exception:
                # 检查是否有错误消息
                try:
                    error_selector = ".kc-feedback-text, .alert-error, .pf-c-alert__title"
                    error_element = await page.wait_for_selector(error_selector, state="visible", timeout=3000)
                    if error_element:
                        error_text = await error_element.text_content()
                        logger.error(f"登录失败: {error_text}")

                        # 如果是凭据错误，不再重试
                        if error_text and ("invalid" in error_text.lower() or "incorrect" in error_text.lower()):
                            logger.error("凭据无效，停止重试")
                            return False
                except Exception:
                    logger.warning("未找到错误消息元素，但登录似乎失败了")

                if attempt < max_retries - 1:
                    log_step("登录未成功，将在3秒后重试...")
                    await asyncio.sleep(3)
                    await page.reload()
                    continue

        except Exception as e:
            logger.error(f"登录过程中出错: {e}")
            logger.debug(f"错误堆栈: {traceback.format_exc()}")
            if attempt < max_retries - 1:
                log_step("将在3秒后重试...")
                await asyncio.sleep(3)
                await page.reload()
                continue

    logger.error(f"登录失败，已尝试 {max_retries} 次")
    return False


async def check_login_status(page: Page) -> bool:
    """
    检查当前是否已登录到Red Hat客户门户

    Args:
        page (Page): Playwright页面实例

    Returns:
        bool: 如果已登录返回True，否则返回False
    """
    log_step("检查登录状态...")

    try:
        # 访问需要登录的页面
        await page.goto(MANAGEMENT_URL, wait_until="domcontentloaded")

        # 等待页面加载，检查是否有用户菜单或个人资料元素
        try:
            user_menu = await page.wait_for_selector(
                ".pf-c-dropdown__toggle-text, .user-name, .pf-c-nav__link",
                state="visible",
                timeout=10000
            )
            if user_menu:
                log_step("已登录状态")
                return True
        except Exception:
            # 检查是否被重定向到登录页面
            if "login" in page.url:
                log_step("未登录状态，当前在登录页面")
                return False

            # 尝试查找登录按钮
            try:
                login_button = await page.query_selector("a[href*='login']")
                if login_button:
                    log_step("未登录状态，发现登录按钮")
                    return False

                # 尝试通过文本查找登录按钮
                login_text = await page.get_by_text("Log in", exact=False).count()
                if login_text > 0:
                    log_step("未登录状态，发现登录文本")
                    return False

                log_step("登录状态不明确，假定为未登录")
                return False
            except Exception:
                log_step("登录状态不明确，假定为未登录")
                return False

    except Exception as e:
        logger.error(f"检查登录状态时出错: {e}")
        logger.debug(f"错误堆栈: {traceback.format_exc()}")
        return False
