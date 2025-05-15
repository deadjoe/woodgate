"""
浏览器模块测试 - 包含基本测试、扩展测试和单元测试
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from playwright.async_api import Browser, BrowserContext, Page, Playwright

from woodgate.core.browser import (
    close_browser,
    initialize_browser,
    setup_cookie_banner_handlers,
)
from tests.test_async_helpers import wrap_async_mock


class TestBrowserBasic:
    """浏览器模块基本测试"""

    def test_initialize_browser_structure(self):
        """测试浏览器初始化函数的结构和参数"""
        # 由于initialize_browser是一个异步函数，直接测试其实现很复杂
        # 这里我们只检查函数的结构和参数，确保它存在并且可以被调用

        # 检查函数签名
        # 验证函数返回类型是tuple
        return_type = initialize_browser.__annotations__.get("return", "")
        assert str(return_type).startswith("tuple[")

        # 验证函数是异步函数
        assert initialize_browser.__code__.co_flags & 0x80  # 检查是否有CO_COROUTINE标志

    @pytest.mark.asyncio
    async def test_close_browser_basic(self):
        """测试浏览器关闭函数"""
        # 模拟Playwright组件
        mock_playwright = AsyncMock(spec=Playwright)
        mock_browser = AsyncMock(spec=Browser)
        mock_context = AsyncMock(spec=BrowserContext)
        mock_page = AsyncMock(spec=Page)

        # 调用被测试的函数
        await close_browser(mock_playwright, mock_browser, mock_context, mock_page)

        # 验证调用了正确的方法
        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()


class TestBrowserUnit:
    """浏览器模块单元测试"""

    @pytest.mark.asyncio
    async def test_initialize_browser_basic(self):
        """测试浏览器初始化基本功能"""
        # 模拟Playwright组件
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        # 包装异步模拟对象，解决未等待协程的警告
        mock_page = wrap_async_mock(mock_page)

        # 设置模拟行为
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # 模拟async_playwright函数
        mock_async_playwright = AsyncMock()
        mock_async_playwright.start.return_value = mock_playwright

        with patch("woodgate.core.browser.async_playwright", return_value=mock_async_playwright):
            with patch("woodgate.core.browser.setup_cookie_banner_handlers", new=AsyncMock()):
                # 调用被测试函数
                result = await initialize_browser()

                # 验证结果
                assert result[0] is mock_playwright  # playwright
                assert result[1] is mock_browser  # browser
                assert result[2] is mock_context  # context
                assert result[3] is mock_page  # page

                # 验证调用
                mock_playwright.chromium.launch.assert_called_once()
                mock_browser.new_context.assert_called_once()
                mock_context.new_page.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_browser_with_options(self):
        """测试浏览器初始化时的选项设置"""
        # 模拟Playwright组件
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        # 包装异步模拟对象，解决未等待协程的警告
        mock_page = wrap_async_mock(mock_page)

        # 设置模拟行为
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # 模拟async_playwright函数
        mock_async_playwright = AsyncMock()
        mock_async_playwright.start.return_value = mock_playwright

        with patch("woodgate.core.browser.async_playwright", return_value=mock_async_playwright):
            with patch("woodgate.core.browser.setup_cookie_banner_handlers", new=AsyncMock()):
                # 调用被测试函数
                await initialize_browser()

                # 验证浏览器启动选项
                launch_args = mock_playwright.chromium.launch.call_args[1]
                assert "headless" in launch_args
                assert "args" in launch_args
                assert "--no-sandbox" in launch_args["args"]

                # 验证浏览器上下文选项
                context_args = mock_browser.new_context.call_args[1]
                assert "viewport" in context_args
                assert "user_agent" in context_args
                assert "ignore_https_errors" in context_args

    @pytest.mark.asyncio
    async def test_close_browser_partial(self):
        """测试部分浏览器资源关闭"""
        # 创建模拟对象
        mock_browser = AsyncMock()
        mock_page = AsyncMock()

        # 调用被测试函数，只提供部分参数
        await close_browser(browser=mock_browser, page=mock_page)

        # 验证调用
        mock_page.close.assert_called_once()
        mock_browser.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_browser_error_handling(self):
        """测试浏览器关闭时的错误处理"""
        # 创建模拟对象
        mock_page = AsyncMock()
        mock_page.close.side_effect = Exception("模拟关闭错误")

        # 调用被测试函数
        await close_browser(page=mock_page)

        # 验证调用 - 即使出错也应该继续执行
        mock_page.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_cookie_banner_handlers(self):
        """测试设置Cookie横幅处理程序"""
        # 创建模拟页面和上下文
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_page.context = mock_context

        # 包装异步模拟对象，解决未等待协程的警告
        mock_page = wrap_async_mock(mock_page)

        # 模拟locator和add_locator_handler方法
        mock_page.locator = AsyncMock()
        mock_page.add_locator_handler = AsyncMock()
        mock_page.on = AsyncMock()

        # 调用被测试函数
        await setup_cookie_banner_handlers(mock_page)

        # 验证调用
        assert mock_page.locator.call_count >= 1
        assert mock_page.add_locator_handler.call_count >= 1
        assert mock_page.on.call_count >= 1
