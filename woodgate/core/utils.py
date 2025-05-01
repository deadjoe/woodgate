"""
工具函数模块 - 提供各种辅助功能
"""

import logging
import time
from typing import Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)


def setup_logging(level=logging.INFO):
    """
    设置日志配置

    Args:
        level: 日志级别，默认为INFO
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def log_step(message: str):
    """
    打印带时间戳的日志信息

    Args:
        message (str): 要打印的信息
    """
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logger.info(f"[{current_time}] {message}")


def print_cookies(driver: webdriver.Chrome, step_name: str = ""):
    """
    打印当前浏览器中的所有Cookie信息

    Args:
        driver (WebDriver): Selenium WebDriver实例
        step_name (str): 当前步骤名称，用于日志
    """
    log_step(f"===== Cookie诊断信息 ({step_name}) =====")
    cookies = driver.get_cookies()
    log_step(f"共有 {len(cookies)} 个Cookie")

    auth_cookies = []
    session_cookies = []
    other_cookies = []

    for cookie in cookies:
        cookie_info = f"名称: {cookie.get('name')}, 值: {cookie.get('value')[:10] if cookie.get('value') and len(cookie.get('value')) > 10 else cookie.get('value')}, 域: {cookie.get('domain')}"

        # 根据Cookie名称分类，便于诊断会话状态和认证问题
        if "auth" in cookie.get("name", "").lower() or "token" in cookie.get("name", "").lower():
            auth_cookies.append(cookie_info)
        elif "session" in cookie.get("name", "").lower():
            session_cookies.append(cookie_info)
        else:
            other_cookies.append(cookie_info)

    if auth_cookies:
        log_step("认证相关Cookie:")
        for cookie in auth_cookies:
            log_step(f"  - {cookie}")

    if session_cookies:
        log_step("会话相关Cookie:")
        for cookie in session_cookies:
            log_step(f"  - {cookie}")

    log_step("其他Cookie数量: " + str(len(other_cookies)))
    log_step("============================")


async def handle_cookie_popup(driver: webdriver.Chrome, timeout: float = 0.5) -> bool:
    """
    处理网页上出现的cookie或隐私弹窗

    Args:
        driver (WebDriver): Selenium WebDriver实例
        timeout (float, optional): 等待弹窗出现的超时时间. Defaults to 0.5.

    Returns:
        bool: 如果成功处理了弹窗返回True，否则返回False
    """
    log_step("检查是否存在cookie通知...")

    try:
        # 优化：使用更高效的CSS选择器，减少DOM查询次数
        popup_selectors = [
            "#onetrust-banner-sdk",  # 最常见的
            ".pf-c-modal-box",  # Red Hat特有的
            "[role='dialog'][aria-modal='true']",  # 通用备选
        ]

        cookie_notice = None
        for selector in popup_selectors:
            try:
                cookie_notice = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                log_step(f"发现cookie通知，使用选择器: {selector}")
                break
            except Exception:
                continue

        if not cookie_notice:
            log_step("未发现cookie通知")
            return False

        # 优化：减少选择器数量，优先使用更常见的按钮选择器
        close_buttons = [
            "button.pf-c-button[aria-label='Close']",
            "#onetrust-accept-btn-handler",
            "button.pf-c-button.pf-m-primary",
            ".close-button",
            "button[aria-label='Close']",
        ]

        # 先尝试在cookie通知元素内查找关闭按钮
        for selector in close_buttons:
            try:
                close_button = cookie_notice.find_element(By.CSS_SELECTOR, selector)
                log_step(f"在cookie通知中找到关闭按钮，使用选择器: {selector}")
                # 使用JavaScript点击避免元素被拦截问题
                driver.execute_script("arguments[0].click();", close_button)
                log_step("已使用JavaScript点击关闭按钮")
                return True
            except Exception:
                continue

        # 尝试通过文本内容查找按钮
        for button_text in ["Accept", "I agree", "Close", "OK", "接受", "同意", "关闭"]:
            try:
                button = driver.find_element(
                    By.XPATH, f"//button[contains(text(), '{button_text}')]"
                )
                log_step(f"找到文本为'{button_text}'的按钮")
                driver.execute_script("arguments[0].click();", button)
                log_step("已使用JavaScript点击按钮")
                return True
            except Exception:
                continue

        log_step("无法找到关闭按钮，可能需要手动关闭")
        return False

    except Exception as e:
        log_step(f"处理cookie通知时出错: {e}")
        return False


def format_alert(feature: Dict[str, Any]) -> str:
    """
    格式化警报特性为可读字符串

    Args:
        feature (dict): 警报特性数据

    Returns:
        str: 格式化后的警报信息
    """
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""
