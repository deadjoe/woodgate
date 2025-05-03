"""
浏览器管理模块 - 负责初始化和管理浏览器实例
"""

import asyncio
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


async def initialize_browser():
    """
    初始化并配置Chrome浏览器

    Returns:
        WebDriver: 配置好的Chrome WebDriver实例
    """
    logger.info("初始化Chrome浏览器...")

    try:
        # 配置Chrome选项 - 优化浏览器性能
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 启用无头模式，不显示浏览器窗口，提高运行效率
        chrome_options.add_argument("--no-sandbox")  # 禁用沙箱，解决某些环境下的权限问题
        chrome_options.add_argument("--disable-dev-shm-usage")  # 解决在低内存环境中的崩溃问题
        chrome_options.add_argument("--window-size=1920,1080")  # 设置窗口大小，模拟标准显示器分辨率

        # 优化：添加性能优化选项
        chrome_options.add_argument("--disable-extensions")  # 禁用扩展，减少资源占用和干扰
        chrome_options.add_argument("--disable-gpu")  # 禁用GPU加速，提高在服务器环境下的兼容性
        chrome_options.add_argument("--disable-infobars")  # 禁用信息栏，避免干扰自动化操作
        chrome_options.add_argument("--disable-notifications")  # 禁用通知，避免弹窗干扰
        chrome_options.add_argument(
            "--blink-settings=imagesEnabled=false"
        )  # 禁用图片加载，加快页面处理速度
        chrome_options.page_load_strategy = (
            "eager"  # 使用eager加载策略，DOM就绪后立即返回，不等待所有资源
        )

        # 安全地获取事件循环并创建浏览器
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，使用run_in_executor
                driver = await loop.run_in_executor(
                    None,
                    lambda: webdriver.Chrome(
                        service=Service(ChromeDriverManager().install()), options=chrome_options
                    ),
                )
            else:
                # 如果事件循环未运行，直接创建浏览器
                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()), options=chrome_options
                )
        except RuntimeError:
            # 如果无法获取事件循环，创建一个新的
            logger.warning("无法获取事件循环，创建新的浏览器实例")
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), options=chrome_options
            )

        # 设置页面加载超时时间
        driver.set_page_load_timeout(20)
        # 设置脚本执行超时时间
        driver.set_script_timeout(10)

        logger.info("浏览器初始化完成")
        return driver
    except Exception as e:
        logger.error(f"浏览器初始化失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        raise
