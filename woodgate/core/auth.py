"""
认证模块 - 处理Red Hat客户门户的登录和会话管理
使用Playwright替代Selenium实现更高效的浏览器自动化
"""

import asyncio
import logging
import traceback

from playwright.async_api import BrowserContext, Page

from .utils import log_step

logger = logging.getLogger(__name__)

# Red Hat客户门户登录URL
LOGIN_URL = "https://sso.redhat.com/auth/realms/redhat-external/login-actions/authenticate"
MANAGEMENT_URL = "https://access.redhat.com/management"


async def login_to_redhat_portal(
    page: Page,
    context: BrowserContext,
    username: str,
    password: str,
    max_retries: int = 3,
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
    # 参数验证
    if not username or not password:
        logger.error("用户名和密码都必须提供")
        return False

    if max_retries < 1:
        logger.error("最大重试次数必须大于0")
        return False

    log_step(f"开始登录Red Hat客户门户 (用户: {username})")

    # 访问登录页面
    try:
        # 使用networkidle而不是domcontentloaded，确保页面完全加载
        await page.goto("https://access.redhat.com/login", wait_until="networkidle", timeout=30000)
        log_step("已加载登录页面")

        # 等待额外的时间，确保页面完全加载和渲染
        await asyncio.sleep(2)

        # 检查页面是否已经准备好
        is_ready = await page.evaluate(
            """
            () => {
                return document.readyState === 'complete' &&
                       !!document.querySelector('form') &&
                       (!!document.querySelector('#username') ||
                        !!document.querySelector('input[type="text"]') ||
                        !!document.querySelector('input[name="username"]'));
            }
        """
        )

        if is_ready:
            log_step("登录页面已完全加载并准备好")
        else:
            log_step("登录页面可能未完全准备好，但将继续尝试")
    except Exception as e:
        logger.error("加载登录页面失败: %s", e)
        logger.debug("错误堆栈: %s", traceback.format_exc())
        return False

    # 注意：cookie横幅处理现在由browser.py中的setup_cookie_banner_handlers函数处理
    # 这里不再需要显式处理cookie弹窗

    # 重试登录，处理可能的网络问题或页面加载延迟
    for attempt in range(max_retries):
        try:
            log_step(f"登录尝试 {attempt + 1}/{max_retries}")

            # 使用JavaScript直接操作登录表单，绕过Playwright的可见性检查
            log_step("使用JavaScript直接操作登录表单")
            login_result = await page.evaluate(
                f"""
                async () => {{
                    try {{
                        // 查找用户名输入框
                        const usernameInput = document.querySelector('#username');
                        if (!usernameInput) {{
                            console.error('未找到用户名输入框');
                            return {{'success': false, 'error': '未找到用户名输入框'}};
                        }}

                        // 输入用户名
                        usernameInput.value = '{username}';
                        console.log('已输入用户名');

                        // 触发输入事件
                        const inputEvent = new Event('input', {{ bubbles: true }});
                        usernameInput.dispatchEvent(inputEvent);

                        // 查找下一步按钮
                        const nextButton = document.querySelector('#login-show-step2');
                        if (!nextButton) {{
                            console.error('未找到下一步按钮');
                            return {{'success': false, 'error': '未找到下一步按钮'}};
                        }}

                        // 点击下一步按钮
                        nextButton.click();
                        console.log('已点击下一步按钮');

                        // 等待密码输入框出现，使用更短的等待时间
                        await new Promise(resolve => setTimeout(resolve, 1000));

                        // 查找密码输入框
                        const passwordInput = document.querySelector('#password');
                        if (!passwordInput) {{
                            console.error('未找到密码输入框');
                            return {{'success': false, 'error': '未找到密码输入框'}};
                        }}

                        // 输入密码
                        passwordInput.value = '{password}';
                        console.log('已输入密码');

                        // 触发输入事件
                        passwordInput.dispatchEvent(inputEvent);

                        // 查找登录按钮
                        const loginButton = document.querySelector('#rh-password-verification-submit-button');
                        if (!loginButton) {{
                            console.error('未找到登录按钮');
                            return {{'success': false, 'error': '未找到登录按钮'}};
                        }}

                        // 点击登录按钮
                        loginButton.click();
                        console.log('已点击登录按钮');

                        // 等待页面加载完成
                        await new Promise(resolve => setTimeout(resolve, 3000));

                        // 检查是否成功
                        const success = document.querySelector('.pf-c-dropdown__toggle-text, .user-name, .pf-c-nav__link, .rh-header-logo, .pf-c-page__header, a:has-text("My account")');
                        if (success) {{
                            console.log('检测到用户菜单元素，登录成功');
                            return {{'success': true, 'user_menu': true}};
                        }}

                        // 检查是否有错误消息
                        const error = document.querySelector('.kc-feedback-text, .alert-error, .pf-c-alert__title');
                        if (error) {{
                            console.error('登录失败:', error.textContent);
                            return {{'success': false, 'error': error.textContent}};
                        }}

                        // 如果没有错误消息且没有用户菜单，检查URL
                        const currentUrl = window.location.href;
                        if (currentUrl.includes('login') || !currentUrl.includes('redhat')) {{
                            return {{'success': false, 'error': '登录后URL异常'}};
                        }}

                        // 如果没有错误消息且没有用户菜单，检查页面元素
                        const pageElements = document.querySelectorAll('.pf-c-dropdown__toggle-text, .user-name, .pf-c-nav__link, .rh-header-logo, .pf-c-page__header, a:has-text("My account")');
                        if (pageElements.length > 0) {{
                            console.log('检测到页面元素，登录成功');
                            return {{'success': true, 'user_menu': true}};
                        }}

                        return {{'success': true, 'user_menu': false, 'url': currentUrl}};
                    }} catch (error) {{
                        console.error('JavaScript登录过程中出错:', error);
                        return {{'success': false, 'error': error.toString()}};
                    }}
                }}
                """
            )

            # 确保返回值是字典类型
            if not isinstance(login_result, dict):
                login_result = {"success": False, "error": "Invalid response format"}

            logger.info("JavaScript登录结果: %s", login_result)

            # 如果JavaScript检测到用户菜单，直接返回成功
            if login_result.get("user_menu"):
                logger.info("JavaScript检测到用户菜单，登录成功")
                return True

            # 等待页面加载完成
            try:
                await page.wait_for_load_state("networkidle", timeout=30000)
            except Exception as e:
                logger.warning("等待页面加载完成时出错: %s", e)

            # 如果JavaScript登录成功但未检测到用户菜单，继续检查页面状态
            if login_result.get("success"):
                # 检查URL
                current_url = page.url
                logger.debug("当前URL: %s", current_url)

                # 如果已离开登录页面，可能登录成功
                if "login" not in current_url or "customer-portal" in current_url:
                    log_step("已离开登录页面，可能登录成功")
                    # 检查是否有用户菜单元素
                    try:
                        user_menu_selector = ".pf-c-dropdown__toggle-text, .user-name, .pf-c-nav__link, .rh-header-logo, .pf-c-page__header, a:has-text('My account')"
                        user_menu = await page.query_selector(user_menu_selector)
                        if user_menu:
                            log_step("检测到用户菜单元素，登录成功")
                            return True

                        logger.warning("未找到用户菜单元素")
                        # 如果未找到用户菜单但已离开登录页面，也认为登录成功
                        return True
                    except Exception as e:
                        logger.warning("检查用户菜单元素时出错: %s", e)
                        # 如果检查用户菜单出错但已离开登录页面，也认为登录成功
                        return True

            # 检查是否有错误消息
            try:
                error_selector = ".kc-feedback-text, .alert-error, .pf-c-alert__title"
                error_elements = await page.query_selector_all(error_selector)
                for error in error_elements:
                    error_text = await error.text_content()
                    logger.error("登录失败: %s", error_text)

                    # 如果是凭据错误，不再重试
                    if error_text and (
                        "invalid" in error_text.lower() or "incorrect" in error_text.lower()
                    ):
                        logger.error("凭据无效，停止重试")
                        return False
            except Exception:
                logger.warning("未找到错误消息元素")

            # 如果JavaScript登录失败，尝试截图以便调试
            try:
                screenshot_path = f"login_error_{attempt}.png"
                await page.screenshot(path=screenshot_path)
                logger.info("已保存错误截图到 %s", screenshot_path)
            except Exception as screenshot_error:
                logger.error("保存截图时出错: %s", screenshot_error)

            # 如果不是最后一次尝试，则重试
            if attempt < max_retries - 1:
                log_step("登录未成功，将在3秒后重试...")
                await asyncio.sleep(3)
                await page.reload()
                continue

            logger.error("已达到最大重试次数，登录失败")
            return False

        except Exception as e:
            logger.error("登录过程中出错: %s", e)
            logger.debug("错误堆栈: %s", traceback.format_exc())

            # 如果不是最后一次尝试，则重试
            if attempt < max_retries - 1:
                log_step("将在3秒后重试...")
                await asyncio.sleep(3)
                await page.reload()
                continue

            logger.error("已达到最大重试次数，登录失败")
            return False

    logger.error("登录失败，已尝试 %d 次", max_retries)
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
        await page.goto(MANAGEMENT_URL, wait_until="networkidle", timeout=30000)

        # 等待页面加载，检查是否有用户菜单或个人资料元素
        try:
            user_menu = await page.wait_for_selector(
                ".pf-c-dropdown__toggle-text, .user-name, .pf-c-nav__link",
                state="visible",
                timeout=10000,
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
        logger.error("检查登录状态时出错: %s", e)
        logger.debug("错误堆栈: %s", traceback.format_exc())
        return False

    # 默认返回值，确保所有路径都有返回值
    return False
