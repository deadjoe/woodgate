"""
浏览器管理模块 - 负责初始化和管理浏览器实例
使用Playwright替代Selenium实现更高效的浏览器自动化
"""

import asyncio
import logging
import traceback
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page, BrowserContext, Playwright

logger = logging.getLogger(__name__)


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
            ]
        )

        # 创建浏览器上下文，配置视口大小和其他选项
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},  # 设置窗口大小，模拟标准显示器分辨率
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",  # 设置用户代理
            ignore_https_errors=True,  # 忽略HTTPS错误，提高兼容性
            java_script_enabled=True,  # 启用JavaScript
            has_touch=False,  # 禁用触摸，模拟桌面环境
        )

        # 创建页面
        page = await context.new_page()

        # 配置页面选项
        await page.route("**/*.{png,jpg,jpeg,gif,svg}", lambda route: route.abort())  # 阻止加载图片，提高性能
        await page.set_default_timeout(20000)  # 设置默认超时时间为20秒
        await page.set_default_navigation_timeout(30000)  # 设置导航超时时间为30秒

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
