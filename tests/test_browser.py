"""
浏览器模块测试
"""

import pytest
from unittest.mock import patch, MagicMock

from woodgate.core.browser import initialize_browser


@pytest.mark.asyncio
async def test_initialize_browser():
    """测试浏览器初始化函数"""
    # 模拟Selenium WebDriver
    mock_driver = MagicMock()

    # 模拟ChromeDriverManager和Service
    with patch("woodgate.core.browser.webdriver.Chrome", return_value=mock_driver) as mock_chrome:
        with patch("woodgate.core.browser.Service") as mock_service:
            with patch("woodgate.core.browser.ChromeDriverManager") as mock_manager:
                # 模拟ChromeDriverManager().install()返回路径
                mock_manager.return_value.install.return_value = "/path/to/chromedriver"

                # 调用被测试的函数
                driver = await initialize_browser()

                # 验证结果
                assert driver == mock_driver
                mock_chrome.assert_called_once()
                mock_service.assert_called_once_with("/path/to/chromedriver")

                # 验证设置了超时
                mock_driver.set_page_load_timeout.assert_called_once_with(20)
                mock_driver.set_script_timeout.assert_called_once_with(10)
