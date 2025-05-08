"""
工具函数模块 - 提供各种辅助功能
使用Playwright替代Selenium实现更高效的浏览器自动化
"""

import logging
import time
from typing import Any, Dict

from playwright.async_api import BrowserContext, Page

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


async def print_cookies(context: BrowserContext, step_name: str = ""):
    """
    打印当前浏览器中的所有Cookie信息

    Args:
        context (BrowserContext): Playwright浏览器上下文
        step_name (str): 当前步骤名称，用于日志
    """
    log_step(f"===== Cookie诊断信息 ({step_name}) =====")

    # 获取所有cookies
    cookies = await context.cookies()
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


async def handle_cookie_popup(page: Page, timeout: float = 1.0) -> bool:
    """
    处理网页上出现的cookie或隐私弹窗

    Args:
        page (Page): Playwright页面实例
        timeout (float, optional): 等待弹窗出现的超时时间(秒). Defaults to 1.0.

    Returns:
        bool: 如果成功处理了弹窗返回True，否则返回False
    """
    log_step("检查是否存在cookie通知...")

    try:
        # 设置较短的超时时间，避免在没有弹窗的情况下等待太久
        page.set_default_timeout(timeout * 1000)  # 转换为毫秒

        # 优化：使用更高效的CSS选择器，减少DOM查询次数
        popup_selectors = [
            "#onetrust-banner-sdk",  # 最常见的
            ".pf-c-modal-box",  # Red Hat特有的
            "[role='dialog'][aria-modal='true']",  # 通用备选
            ".cookie-banner",  # 通用cookie横幅
            "#cookie-notice",  # 另一种常见的cookie通知
            "#truste-consent-track",  # Red Hat使用的TrustArc cookie通知
            ".truste_box_overlay",  # TrustArc弹窗
            ".truste_overlay",  # TrustArc弹窗
            "#consent_blackbar",  # 另一种常见的cookie通知
            ".evidon-banner",  # Evidon cookie通知
            ".cookie-consent-banner",  # 通用cookie横幅
            "#gdpr-cookie-message",  # GDPR cookie消息
            "#cookiebanner",  # 通用cookie横幅
            "#cookie-law-info-bar",  # Cookie Law Info插件
            ".cc-window",  # Cookie Consent插件
        ]

        # 检查是否存在cookie通知
        for selector in popup_selectors:
            try:
                # 使用waitForSelector而不是等待元素可见，提高效率
                cookie_notice = await page.wait_for_selector(
                    selector, timeout=timeout * 1000, state="attached"
                )
                if cookie_notice:
                    log_step(f"发现cookie通知，使用选择器: {selector}")

                    # 优化：减少选择器数量，优先使用更常见的按钮选择器
                    close_buttons = [
                        "button.pf-c-button[aria-label='Close']",
                        "#onetrust-accept-btn-handler",
                        "button.pf-c-button.pf-m-primary",
                        ".close-button",
                        "button[aria-label='Close']",
                        "#truste-consent-button",  # TrustArc同意按钮
                        ".truste_popclose",  # TrustArc关闭按钮
                        ".trustarc-agree-btn",  # TrustArc同意按钮
                        ".evidon-banner-acceptbutton",  # Evidon接受按钮
                        ".cc-dismiss",  # Cookie Consent关闭按钮
                        ".cc-accept-all",  # Cookie Consent接受所有按钮
                        "#cookie-notice-accept-button",  # Cookie Notice接受按钮
                        ".cookie-consent-button",  # 通用cookie同意按钮
                        "button:has-text('Accept All')",  # 接受所有按钮
                        "button:has-text('Accept Cookies')",  # 接受cookies按钮
                    ]

                    # 先尝试在cookie通知元素内查找关闭按钮
                    for btn_selector in close_buttons:
                        try:
                            # 在cookie通知内查找按钮
                            close_button = await cookie_notice.query_selector(btn_selector)
                            if close_button:
                                log_step(f"在cookie通知中找到关闭按钮，使用选择器: {btn_selector}")
                                await close_button.click()
                                log_step("已点击关闭按钮")
                                # 恢复默认超时时间
                                page.set_default_timeout(30000)
                                return True
                        except Exception:
                            continue

                    # 尝试通过文本内容查找按钮
                    for button_text in ["Accept", "I agree", "Close", "OK", "Accept All", "Accept Cookies", "Agree", "Continue", "Got it", "I understand", "接受", "同意", "关闭", "继续", "我同意", "我理解"]:
                        try:
                            # 使用text=按钮文本定位
                            button = await page.get_by_text(button_text, exact=False).first()
                            if button:
                                await button.click(timeout=1000)
                                log_step(f"找到并点击了文本为'{button_text}'的按钮")
                            # 恢复默认超时时间
                            page.set_default_timeout(30000)
                            return True
                        except Exception:
                            continue

                    # 如果上述方法都失败，尝试使用JavaScript点击
                    try:
                        await page.evaluate(
                            """
                            const buttons = Array.from(document.querySelectorAll('button, a.button, input[type="button"], input[type="submit"]'));
                            const acceptButton = buttons.find(button =>
                                button.textContent.toLowerCase().includes('accept') ||
                                button.textContent.toLowerCase().includes('agree') ||
                                button.textContent.toLowerCase().includes('close') ||
                                button.textContent.toLowerCase().includes('ok') ||
                                button.textContent.toLowerCase().includes('got it') ||
                                button.textContent.toLowerCase().includes('continue') ||
                                button.textContent.toLowerCase().includes('understand') ||
                                button.textContent.toLowerCase().includes('接受') ||
                                button.textContent.toLowerCase().includes('同意') ||
                                button.textContent.toLowerCase().includes('关闭') ||
                                button.textContent.toLowerCase().includes('继续') ||
                                button.textContent.toLowerCase().includes('理解')
                            );
                            if (acceptButton) acceptButton.click();

                            // 尝试点击特定ID的按钮
                            const specificButtons = [
                                document.querySelector('#truste-consent-button'),
                                document.querySelector('#onetrust-accept-btn-handler'),
                                document.querySelector('.trustarc-agree-btn'),
                                document.querySelector('.evidon-banner-acceptbutton'),
                                document.querySelector('.cc-accept-all'),
                                document.querySelector('#cookie-notice-accept-button')
                            ];

                            for (const btn of specificButtons) {
                                if (btn) {
                                    btn.click();
                                    break;
                                }
                            }
                        """
                        )
                        log_step("已使用JavaScript尝试点击按钮")
                        # 恢复默认超时时间
                        page.set_default_timeout(30000)
                        return True
                    except Exception:
                        pass
            except Exception:
                continue

        # 恢复默认超时时间
        page.set_default_timeout(30000)
        log_step("未发现cookie通知")
        return False

    except Exception as e:
        # 恢复默认超时时间
        page.set_default_timeout(30000)
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
