"""
浏览器管理模块 - 负责初始化和管理浏览器实例
使用Playwright替代Selenium实现更高效的浏览器自动化
"""

import logging
import traceback
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Locator,
    Page,
    Playwright,
    async_playwright,
)

logger = logging.getLogger(__name__)


async def setup_cookie_banner_handlers(page: Page) -> None:
    """
    设置处理cookie横幅的处理程序
    使用Playwright v1.42+引入的add_locator_handler方法

    Args:
        page: Playwright页面实例
    """
    logger.info("设置cookie横幅处理程序...")

    # 常见的cookie横幅选择器，优化为只包含最常用和Red Hat特有的选择器
    cookie_banner_selectors = [
        "#truste-consent-track",  # Red Hat使用的TrustArc cookie通知（最重要）
        "#onetrust-banner-sdk",  # 最常见的
        ".pf-c-modal-box",  # Red Hat特有的
        ".cookie-banner",  # 通用cookie横幅
        "#cookie-notice",  # 另一种常见的cookie通知
        ".truste_box_overlay",  # TrustArc弹窗
        ".truste_popframe",  # TrustArc弹窗框架
        "#teconsent",  # TrustArc同意元素
    ]

    # 常见的接受按钮选择器，优化为只包含最常用和Red Hat特有的选择器
    accept_button_selectors = [
        "#truste-consent-button",  # TrustArc同意按钮（Red Hat使用）
        ".truste_popclose",  # TrustArc关闭按钮
        "button.pf-c-button[aria-label='Close']",  # Red Hat特有
        "button.pf-c-button.pf-m-primary",  # Red Hat特有
        "#onetrust-accept-btn-handler",  # 常见的
        "button:has-text('Accept')",  # 通用接受按钮
        "button:has-text('I agree')",  # 通用同意按钮
        "button:has-text('Close')",  # 通用关闭按钮
    ]

    # 为每个cookie横幅选择器添加处理程序
    for selector in cookie_banner_selectors:
        try:
            banner_locator = page.locator(selector)

            # 定义处理函数
            async def handle_cookie_banner(banner: Locator) -> None:
                if await banner.is_visible():
                    logger.info(f"检测到cookie横幅: {selector}")

                    # 尝试点击接受按钮
                    for btn_selector in accept_button_selectors:
                        try:
                            button = banner.locator(btn_selector)
                            if await button.is_visible():
                                logger.info(f"点击cookie横幅按钮: {btn_selector}")
                                await button.click()
                                return
                        except Exception as e:
                            logger.debug(f"尝试点击按钮 {btn_selector} 失败: {e}")

                    # 如果没有找到特定按钮，尝试通过文本查找
                    for text in [
                        "Accept",
                        "Accept All",
                        "I agree",
                        "Agree",
                        "Close",
                        "OK",
                        "Continue",
                        "Got it",
                    ]:
                        try:
                            button = banner.get_by_text(text, exact=False)
                            if await button.is_visible():
                                logger.info(f"点击文本为 '{text}' 的按钮")
                                await button.click()
                                return
                        except Exception as e:
                            logger.debug(f"尝试点击文本为 '{text}' 的按钮失败: {e}")

                    # 如果上述方法都失败，尝试使用JavaScript点击
                    try:
                        logger.info("使用JavaScript尝试点击cookie横幅按钮")
                        await page.evaluate(
                            """
                            (banner) => {
                                const buttons = Array.from(banner.querySelectorAll('button, a.button, input[type="button"], input[type="submit"]'));
                                const acceptButton = buttons.find(button =>
                                    button.textContent.toLowerCase().includes('accept') ||
                                    button.textContent.toLowerCase().includes('agree') ||
                                    button.textContent.toLowerCase().includes('close') ||
                                    button.textContent.toLowerCase().includes('ok') ||
                                    button.textContent.toLowerCase().includes('got it') ||
                                    button.textContent.toLowerCase().includes('continue')
                                );
                                if (acceptButton) acceptButton.click();
                            }
                            """,
                            await banner.element_handle(),
                        )
                    except Exception as e:
                        logger.debug(f"使用JavaScript点击失败: {e}")

            # 添加处理程序
            handler = page.add_locator_handler(banner_locator, handle_cookie_banner)
            # 确保异步处理程序被正确等待
            await handler
            logger.debug(f"已添加cookie横幅处理程序: {selector}")
        except Exception as e:
            logger.debug(f"为选择器 {selector} 添加处理程序失败: {e}")

    # 添加一个通用的cookie横幅处理程序，用于处理可能的iframe内的cookie横幅
    try:
        # 使用JavaScript处理可能的iframe内的cookie横幅
        async def handle_all_cookie_banners(page_obj: Page) -> None:
            try:
                # 使用简化的JavaScript代码处理Red Hat特定的cookie通知
                await page_obj.evaluate(
                    """
                    () => {
                        // 设置Red Hat特定的cookie接受标志
                        document.cookie = "redhat_cookie_notice_accepted=true; path=/; expires=Fri, 31 Dec 9999 23:59:59 GMT";
                        document.cookie = "redhat_privacy_accepted=true; path=/; expires=Fri, 31 Dec 9999 23:59:59 GMT";
                        document.cookie = "redhat_gdpr_accepted=true; path=/; expires=Fri, 31 Dec 9999 23:59:59 GMT";
                        document.cookie = "OptanonAlertBoxClosed=2023-01-01T12:00:00.000Z; path=/; expires=Fri, 31 Dec 9999 23:59:59 GMT";

                        // 直接处理Red Hat特定的cookie通知
                        const redhatCookieSelectors = [
                            '#truste-consent-track',
                            '#truste-consent-button',
                            '.truste_popframe',
                            '#teconsent'
                        ];

                        // 尝试点击接受按钮
                        const buttonSelectors = [
                            '#truste-consent-button',
                            'button:contains("Accept")',
                            'button:contains("I agree")',
                            'button:contains("Close")'
                        ];

                        // 点击按钮
                        buttonSelectors.forEach(selector => {
                            try {
                                const button = document.querySelector(selector);
                                if (button && button.offsetParent !== null) {
                                    console.log('点击按钮:', selector);
                                    button.click();
                                }
                            } catch (e) {
                                console.error('点击按钮失败:', e);
                            }
                        });

                        // 隐藏横幅
                        redhatCookieSelectors.forEach(selector => {
                            try {
                                const banner = document.querySelector(selector);
                                if (banner) {
                                    console.log('隐藏横幅:', selector);
                                    banner.style.display = 'none';
                                }
                            } catch (e) {
                                console.error('隐藏横幅失败:', e);
                            }
                        });

                        // 特别处理：查找包含"How we use cookies"文本的元素
                        const cookieElements = Array.from(document.querySelectorAll('*')).filter(el =>
                            el.textContent &&
                            (el.textContent.includes('How we use cookies') ||
                             el.textContent.includes('By using this website you agree to our use of cookies'))
                        );

                        cookieElements.forEach(el => {
                            // 向上查找5层父元素，尝试找到并隐藏整个横幅
                            let element = el;
                            for (let i = 0; i < 5 && element; i++) {
                                if (element.style) {
                                    element.style.display = 'none';
                                }
                                element = element.parentElement;
                            }
                        });
                    }
                    """
                )

                # 特别处理：尝试直接点击包含特定文本的按钮
                try:
                    # 只检查最常用的接受文本
                    for text in ["Accept", "I agree"]:
                        button = page_obj.get_by_text(text, exact=False)
                        if await button.count() > 0:
                            logger.info(f"找到文本为 '{text}' 的按钮，尝试点击")
                            await button.first.click(timeout=1000, force=True)
                            break
                except Exception as e:
                    logger.debug(f"点击文本按钮失败: {e}")

            except Exception as e:
                logger.debug(f"通用cookie横幅处理失败: {e}")

        # 只在页面加载后执行一次，避免重复执行
        # 使用正确的异步回调函数
        async def on_load_handler(page_obj: Page) -> None:
            await handle_all_cookie_banners(page_obj)

        # 注意：page.on()是同步方法，不需要await
        # 在测试中，我们使用MagicMock模拟这个方法，避免协程警告
        page.on("load", on_load_handler)

        logger.debug("已添加通用cookie横幅处理程序")
    except Exception as e:
        logger.debug(f"添加通用cookie横幅处理程序失败: {e}")

    # 添加特定的Red Hat cookie处理
    try:
        # 在页面加载前设置最关键的cookie
        await page.context.add_cookies(
            [
                {
                    "name": "redhat_cookie_notice_accepted",
                    "value": "true",
                    "domain": ".redhat.com",
                    "path": "/",
                },
                {
                    "name": "OptanonAlertBoxClosed",
                    "value": "2023-01-01T12:00:00.000Z",
                    "domain": ".redhat.com",
                    "path": "/",
                },
            ]
        )
        logger.info("已预设Red Hat cookie接受标志")
    except Exception as e:
        logger.debug(f"预设cookie失败: {e}")

    logger.info("cookie横幅处理程序设置完成")


async def initialize_browser() -> tuple[Playwright, Browser, BrowserContext, Page]:
    """
    初始化并配置Chromium浏览器

    Returns:
        tuple: (playwright实例, 浏览器实例, 浏览器上下文, 页面实例)
    """
    logger.info("初始化Chromium浏览器...")

    try:
        # 启动Playwright
        playwright = await async_playwright().start()

        # 启动浏览器，配置优化选项
        browser = await playwright.chromium.launch(
            headless=True,  # 启用无头模式，不显示浏览器窗口，提高运行效率
            args=[
                "--no-sandbox",  # 禁用沙箱，解决某些环境下的权限问题
                "--disable-dev-shm-usage",  # 解决在低内存环境中的崩溃问题
                "--disable-extensions",  # 禁用扩展，减少资源占用和干扰
                "--disable-gpu",  # 禁用GPU加速，提高在服务器环境下的兼容性
                "--disable-notifications",  # 禁用通知，避免弹窗干扰
            ],
        )

        # 创建浏览器上下文，配置视口大小和其他选项
        context = await browser.new_context(
            viewport={
                "width": 1920,
                "height": 1080,
            },  # 设置窗口大小，模拟标准显示器分辨率
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",  # 设置用户代理
            ignore_https_errors=True,  # 忽略HTTPS错误，提高兼容性
            java_script_enabled=True,  # 启用JavaScript
            has_touch=False,  # 禁用触摸，模拟桌面环境
        )

        # 创建页面
        page = await context.new_page()

        # 配置页面选项
        await page.route(
            "**/*.{png,jpg,jpeg,gif,svg}", lambda route: route.abort()
        )  # 阻止加载图片，提高性能
        page.set_default_timeout(20000)  # 设置默认超时时间为20秒
        page.set_default_navigation_timeout(30000)  # 设置导航超时时间为30秒

        # 添加cookie横幅处理程序
        await setup_cookie_banner_handlers(page)

        logger.info("浏览器初始化完成")
        return playwright, browser, context, page
    except Exception as e:
        logger.error(f"浏览器初始化失败: {e}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        raise


async def close_browser(
    playwright: Optional[Playwright] = None,
    browser: Optional[Browser] = None,
    context: Optional[BrowserContext] = None,
    page: Optional[Page] = None,
) -> None:
    """
    安全关闭浏览器及相关资源

    Args:
        playwright: Playwright实例
        browser: 浏览器实例
        context: 浏览器上下文
        page: 页面实例
    """
    try:
        if page:
            await page.close()
            logger.debug("页面已关闭")

        if context:
            await context.close()
            logger.debug("浏览器上下文已关闭")

        if browser:
            await browser.close()
            logger.debug("浏览器已关闭")

        if playwright:
            await playwright.stop()
            logger.debug("Playwright已停止")

        logger.info("浏览器资源已完全释放")
    except Exception as e:
        logger.warning(f"关闭浏览器时出错: {e}")
        logger.debug(f"错误堆栈: {traceback.format_exc()}")
