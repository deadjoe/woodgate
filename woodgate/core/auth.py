"""
认证模块 - 处理Red Hat客户门户的登录和会话管理
"""

import asyncio
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .utils import log_step, print_cookies, handle_cookie_popup

logger = logging.getLogger(__name__)

# Red Hat客户门户登录URL
LOGIN_URL = "https://sso.redhat.com/auth/realms/redhat-external/login-actions/authenticate"


async def login_to_redhat_portal(
    driver: webdriver.Chrome, username: str, password: str, max_retries: int = 3
) -> bool:
    """
    登录到Red Hat客户门户

    Args:
        driver (WebDriver): Selenium WebDriver实例
        username (str): Red Hat账号用户名
        password (str): Red Hat账号密码
        max_retries (int, optional): 最大重试次数. Defaults to 3.

    Returns:
        bool: 登录成功返回True，否则返回False
    """
    log_step(f"开始登录Red Hat客户门户 (用户: {username})")

    # 访问登录页面
    try:
        driver.get("https://access.redhat.com/login")
        log_step("已加载登录页面")
    except Exception as e:
        logger.error(f"加载登录页面失败: {e}")
        return False

    # 处理可能出现的Cookie弹窗
    await handle_cookie_popup(driver, timeout=2)

    # 重试登录，处理可能的网络问题或页面加载延迟
    for attempt in range(max_retries):
        try:
            log_step(f"登录尝试 {attempt + 1}/{max_retries}")

            # 等待用户名输入框出现
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.clear()
            username_field.send_keys(username)
            log_step("已输入用户名")

            # 等待密码输入框出现
            password_field = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_field.clear()
            password_field.send_keys(password)
            log_step("已输入密码")

            # 点击登录按钮
            login_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "kc-login"))
            )
            login_button.click()
            log_step("已点击登录按钮")

            # 等待登录完成，检查是否成功
            try:
                # 等待页面加载完成，检查是否有用户菜单或个人资料元素
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            ".pf-c-dropdown__toggle-text, .user-name, .pf-c-nav__link",
                        )
                    )
                )
                log_step("登录成功！已检测到用户菜单元素")

                # 打印Cookie信息，用于诊断
                print_cookies(driver, "登录成功后")

                return True
            except TimeoutException:
                # 检查是否有错误消息
                try:
                    error_message = driver.find_element(
                        By.CSS_SELECTOR, ".kc-feedback-text, .alert-error, .pf-c-alert__title"
                    )
                    logger.error(f"登录失败: {error_message.text}")

                    # 如果是凭据错误，不再重试
                    if (
                        "invalid" in error_message.text.lower()
                        or "incorrect" in error_message.text.lower()
                    ):
                        logger.error("凭据无效，停止重试")
                        return False
                except NoSuchElementException:
                    logger.warning("未找到错误消息元素，但登录似乎失败了")

                if attempt < max_retries - 1:
                    log_step("登录未成功，将在3秒后重试...")
                    await asyncio.sleep(3)
                    driver.refresh()

        except Exception as e:
            logger.error(f"登录过程中出错: {e}")
            if attempt < max_retries - 1:
                log_step("将在3秒后重试...")
                await asyncio.sleep(3)
                driver.refresh()

    logger.error(f"登录失败，已尝试 {max_retries} 次")
    return False


async def check_login_status(driver: webdriver.Chrome) -> bool:
    """
    检查当前是否已登录到Red Hat客户门户

    Args:
        driver (WebDriver): Selenium WebDriver实例

    Returns:
        bool: 如果已登录返回True，否则返回False
    """
    log_step("检查登录状态...")

    try:
        # 访问需要登录的页面
        driver.get("https://access.redhat.com/management")

        # 等待页面加载，检查是否有用户菜单或个人资料元素
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".pf-c-dropdown__toggle-text, .user-name, .pf-c-nav__link")
                )
            )
            log_step("已登录状态")
            return True
        except TimeoutException:
            # 检查是否被重定向到登录页面
            if "login" in driver.current_url:
                log_step("未登录状态，当前在登录页面")
                return False

            # 尝试查找登录按钮
            try:
                driver.find_element(By.CSS_SELECTOR, "a[href*='login'], button:contains('Log in')")
                log_step("未登录状态，发现登录按钮")
                return False
            except NoSuchElementException:
                log_step("登录状态不明确，假定为未登录")
                return False

    except Exception as e:
        logger.error(f"检查登录状态时出错: {e}")
        return False
