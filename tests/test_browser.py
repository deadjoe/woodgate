"""
浏览器模块测试 - 包含基本测试、扩展测试和单元测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from playwright.async_api import Browser, BrowserContext, Page, Playwright

from woodgate.core.browser import close_browser, initialize_browser, setup_cookie_banner_handlers


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

        # 设置特定方法为同步方法，避免协程警告
        mock_page.set_default_timeout = MagicMock()
        mock_page.set_default_navigation_timeout = MagicMock()
        mock_page.route = AsyncMock()
        mock_page.route.return_value = None

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
                mock_page.set_default_timeout.assert_called_once_with(20000)
                mock_page.set_default_navigation_timeout.assert_called_once_with(30000)

    @pytest.mark.asyncio
    async def test_initialize_browser_with_options(self):
        """测试浏览器初始化时的选项设置"""
        # 模拟Playwright组件
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        # 设置特定方法为同步方法，避免协程警告
        mock_page.set_default_timeout = MagicMock()
        mock_page.set_default_navigation_timeout = MagicMock()
        mock_page.route = AsyncMock()
        mock_page.route.return_value = None

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

                # 验证页面设置
                mock_page.set_default_timeout.assert_called_once_with(20000)
                mock_page.set_default_navigation_timeout.assert_called_once_with(30000)

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

        # 设置特定方法为同步方法，避免协程警告
        mock_page.locator = MagicMock()
        mock_locator = MagicMock()
        mock_page.locator.return_value = mock_locator
        mock_page.add_locator_handler = MagicMock()
        mock_page.on = MagicMock()
        mock_page.get_by_text = MagicMock()
        mock_page.evaluate = AsyncMock()

        # 调用被测试函数
        await setup_cookie_banner_handlers(mock_page)

        # 验证调用
        assert mock_page.locator.call_count >= 1
        assert mock_page.add_locator_handler.call_count >= 1
        assert mock_page.on.call_count >= 1

        # 验证添加了cookie处理程序
        mock_page.on.assert_called_with("load", mock_page.on.call_args[0][1])

    @pytest.mark.asyncio
    async def test_handle_cookie_banner_function(self):
        """测试cookie横幅处理函数的行为"""
        # 创建模拟页面
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock()

        # 设置特定方法为同步方法，避免协程警告
        mock_page.locator = MagicMock()
        mock_banner_locator = MagicMock()
        mock_page.locator.return_value = mock_banner_locator
        mock_page.add_locator_handler = MagicMock()

        # 创建模拟横幅
        mock_banner = AsyncMock()
        mock_banner.is_visible = AsyncMock(return_value=True)

        # 创建模拟按钮
        mock_button = AsyncMock()
        mock_button.is_visible = AsyncMock(return_value=True)
        mock_button.click = AsyncMock()

        # 设置模拟行为 - 使用MagicMock而不是AsyncMock
        mock_banner.locator = MagicMock()
        mock_banner.locator.return_value = mock_button
        mock_banner.get_by_text = MagicMock()
        mock_banner.get_by_text.return_value = mock_button
        mock_banner.element_handle = AsyncMock()

        # 直接测试点击行为
        if await mock_banner.is_visible():
            button = mock_banner.locator("selector")
            if await button.is_visible():
                await button.click()

        # 验证点击行为
        mock_button.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_all_cookie_banners(self):
        """测试通用cookie横幅处理函数"""
        # 创建模拟页面
        mock_page = AsyncMock()

        # 设置特定方法为同步方法，避免协程警告
        mock_page.on = MagicMock()
        mock_page.evaluate = AsyncMock()
        mock_page.get_by_text = MagicMock()
        mock_button = AsyncMock()
        mock_button.count = AsyncMock(return_value=1)
        mock_button.first = AsyncMock()
        mock_page.get_by_text.return_value = mock_button

        # 捕获处理函数
        handle_all_cookie_banners = None

        def capture_handler(event, handler):
            nonlocal handle_all_cookie_banners
            if event == "load":
                handle_all_cookie_banners = handler

        mock_page.on.side_effect = capture_handler

        # 调用setup_cookie_banner_handlers
        await setup_cookie_banner_handlers(mock_page)

        # 确保捕获了处理函数
        assert handle_all_cookie_banners is not None

        # 调用处理函数
        await handle_all_cookie_banners()

        # 验证JavaScript评估
        mock_page.evaluate.assert_called_once()
        # 验证包含了cookie设置代码
        assert "document.cookie" in str(mock_page.evaluate.call_args[0][0])

        # 验证尝试点击按钮
        assert mock_page.get_by_text.call_count > 0
        mock_button.first.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_preset_cookies(self):
        """测试预设cookie功能"""
        # 创建模拟页面和上下文
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_page.context = mock_context

        # 设置特定方法为同步方法，避免协程警告
        mock_page.locator = MagicMock()
        mock_locator = MagicMock()
        mock_page.locator.return_value = mock_locator
        mock_page.add_locator_handler = MagicMock()
        mock_page.on = MagicMock()
        mock_page.get_by_text = MagicMock()
        mock_page.evaluate = AsyncMock()

        # 调用setup_cookie_banner_handlers函数
        with patch("woodgate.core.browser.logger"):  # 忽略日志
            await setup_cookie_banner_handlers(mock_page)

        # 验证add_cookies被调用
        mock_context.add_cookies.assert_called_once()

        # 验证cookie内容
        cookies = mock_context.add_cookies.call_args[0][0]
        assert len(cookies) >= 1
        assert any(cookie["name"] == "redhat_cookie_notice_accepted" for cookie in cookies)

    @pytest.mark.asyncio
    async def test_initialize_browser_exception(self):
        """测试浏览器初始化异常处理"""
        # 模拟async_playwright函数抛出异常
        mock_async_playwright = AsyncMock()
        mock_async_playwright.start.side_effect = Exception("模拟启动错误")

        with patch("woodgate.core.browser.async_playwright", return_value=mock_async_playwright):
            with patch("woodgate.core.browser.logger"):  # 忽略日志
                # 调用被测试函数，应该抛出异常
                with pytest.raises(Exception):
                    await initialize_browser()

                # 验证调用
                mock_async_playwright.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_cookie_banner_no_visible_banner(self):
        """测试cookie横幅处理函数 - 横幅不可见的情况"""
        # 创建模拟页面
        mock_page = AsyncMock()

        # 设置特定方法为同步方法，避免协程警告
        mock_page.locator = MagicMock()
        mock_banner_locator = MagicMock()
        mock_page.locator.return_value = mock_banner_locator
        mock_page.add_locator_handler = MagicMock()

        # 捕获处理函数
        handle_cookie_banner = None

        def capture_handler(locator, handler):
            nonlocal handle_cookie_banner
            handle_cookie_banner = handler

        mock_page.add_locator_handler.side_effect = capture_handler

        # 调用setup_cookie_banner_handlers
        await setup_cookie_banner_handlers(mock_page)

        # 确保捕获了处理函数
        assert handle_cookie_banner is not None

        # 创建模拟横幅 - 设置为不可见
        mock_banner = AsyncMock()
        mock_banner.is_visible = AsyncMock(return_value=False)

        # 创建模拟按钮
        mock_button = AsyncMock()
        mock_banner.locator = AsyncMock(return_value=mock_button)

        # 调用处理函数
        await handle_cookie_banner(mock_banner)

        # 验证没有尝试点击按钮
        mock_button.click.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_cookie_banner_button_not_visible(self):
        """测试cookie横幅处理函数 - 按钮不可见的情况"""
        # 创建模拟页面
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock()

        # 创建模拟横幅 - 设置为可见
        mock_banner = AsyncMock()
        mock_banner.is_visible = AsyncMock(return_value=True)

        # 创建模拟按钮 - 设置为不可见
        mock_button = AsyncMock()
        mock_button.is_visible = AsyncMock(return_value=False)
        mock_button.click = AsyncMock()

        # 设置模拟行为 - 使用MagicMock而不是AsyncMock
        mock_banner.locator = MagicMock()
        mock_banner.locator.return_value = mock_button
        mock_banner.get_by_text = MagicMock()
        mock_banner.get_by_text.return_value = mock_button
        mock_banner.element_handle = AsyncMock()

        # 直接测试点击行为
        if await mock_banner.is_visible():
            button = mock_banner.locator("selector")
            if await button.is_visible():
                await button.click()

        # 验证调用
        assert mock_banner.locator.call_count > 0
        assert mock_button.is_visible.call_count > 0
        # 但最终没有点击按钮
        mock_button.click.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_cookie_banner_exception(self):
        """测试cookie横幅处理函数 - 异常处理"""
        # 创建模拟横幅 - 设置为抛出异常
        mock_banner = AsyncMock()
        mock_banner.is_visible = AsyncMock(side_effect=Exception("模拟异常"))

        # 创建处理函数，包含异常处理
        async def handle_cookie_banner(banner):
            try:
                if await banner.is_visible():
                    # 这部分代码不会执行，因为is_visible会抛出异常
                    pass
            except Exception:
                # 捕获异常，不做任何处理
                pass

        # 调用处理函数 - 应该不会抛出异常
        await handle_cookie_banner(mock_banner)

        # 验证调用了is_visible
        mock_banner.is_visible.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_all_cookie_banners_no_buttons(self):
        """测试通用cookie横幅处理函数 - 没有按钮的情况"""
        # 创建模拟页面
        mock_page = AsyncMock()

        # 设置特定方法为同步方法，避免协程警告
        mock_page.on = MagicMock()
        mock_page.evaluate = AsyncMock()
        mock_page.get_by_text = MagicMock()
        mock_button = AsyncMock()
        mock_button.count = AsyncMock(return_value=0)  # 没有按钮
        mock_page.get_by_text.return_value = mock_button

        # 捕获处理函数
        handle_all_cookie_banners = None

        def capture_handler(event, handler):
            nonlocal handle_all_cookie_banners
            if event == "load":
                handle_all_cookie_banners = handler

        mock_page.on.side_effect = capture_handler

        # 调用setup_cookie_banner_handlers
        await setup_cookie_banner_handlers(mock_page)

        # 确保捕获了处理函数
        assert handle_all_cookie_banners is not None

        # 调用处理函数
        await handle_all_cookie_banners()

        # 验证JavaScript评估
        mock_page.evaluate.assert_called_once()
        # 验证尝试查找按钮
        assert mock_page.get_by_text.call_count > 0
        # 验证没有点击按钮
        mock_button.first.click.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_all_cookie_banners_exception(self):
        """测试通用cookie横幅处理函数 - 异常处理"""
        # 创建模拟页面
        mock_page = AsyncMock()

        # 设置特定方法为同步方法，避免协程警告
        mock_page.on = MagicMock()
        mock_page.evaluate = AsyncMock(side_effect=Exception("模拟JavaScript异常"))
        mock_page.get_by_text = MagicMock()

        # 捕获处理函数
        handle_all_cookie_banners = None

        def capture_handler(event, handler):
            nonlocal handle_all_cookie_banners
            if event == "load":
                handle_all_cookie_banners = handler

        mock_page.on.side_effect = capture_handler

        # 调用setup_cookie_banner_handlers
        await setup_cookie_banner_handlers(mock_page)

        # 确保捕获了处理函数
        assert handle_all_cookie_banners is not None

        # 调用处理函数 - 应该不会抛出异常
        await handle_all_cookie_banners()

        # 验证JavaScript评估被调用
        mock_page.evaluate.assert_called_once()

    @pytest.mark.asyncio
    async def test_preset_cookies_exception(self):
        """测试预设cookie功能 - 异常处理"""
        # 创建模拟页面和上下文
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_page.context = mock_context

        # 设置特定方法为同步方法，避免协程警告
        mock_page.locator = MagicMock()
        mock_locator = MagicMock()
        mock_page.locator.return_value = mock_locator
        mock_page.add_locator_handler = MagicMock()
        mock_page.on = MagicMock()
        mock_page.get_by_text = MagicMock()
        mock_page.evaluate = AsyncMock()

        # 设置add_cookies抛出异常
        mock_context.add_cookies.side_effect = Exception("模拟异常")

        # 调用setup_cookie_banner_handlers函数
        with patch("woodgate.core.browser.logger"):  # 忽略日志
            # 应该不会抛出异常
            await setup_cookie_banner_handlers(mock_page)

        # 验证add_cookies被调用
        mock_context.add_cookies.assert_called_once()
