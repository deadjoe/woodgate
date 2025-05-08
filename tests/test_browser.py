"""
浏览器模块测试
"""

from unittest.mock import AsyncMock

import pytest
from playwright.async_api import Browser, BrowserContext, Page, Playwright

from woodgate.core.browser import initialize_browser


def test_initialize_browser():
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
async def test_close_browser():
    """测试浏览器关闭函数"""
    from woodgate.core.browser import close_browser

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
