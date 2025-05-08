"""
认证模块测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from playwright.async_api import Error, TimeoutError

from woodgate.core.auth import check_login_status, login_to_redhat_portal


@pytest.mark.asyncio
async def test_login_to_redhat_portal_success():
    """测试成功登录到Red Hat客户门户"""
    # 模拟Playwright Page和元素
    mock_page = AsyncMock()
    mock_context = AsyncMock()
    mock_username_field = AsyncMock()
    mock_password_field = AsyncMock()
    mock_login_button = AsyncMock()
    mock_user_menu = AsyncMock()

    # 设置模拟行为
    mock_page.goto.return_value = AsyncMock()
    mock_page.wait_for_selector.side_effect = [
        mock_username_field,  # 用户名字段
        mock_password_field,  # 密码字段
        mock_login_button,  # 登录按钮
        mock_user_menu,  # 用户菜单（登录成功标志）
    ]

    with patch("woodgate.core.auth.handle_cookie_popup", return_value=True) as mock_handle_cookie:
        with patch("woodgate.core.auth.print_cookies") as mock_print_cookies:
            # 调用被测试的函数
            result = await login_to_redhat_portal(mock_page, mock_context, "test_user", "test_pass")

            # 验证结果
            assert result is True
            mock_page.goto.assert_called_once_with("https://access.redhat.com/login", wait_until="domcontentloaded")
            mock_username_field.fill.assert_any_call("test_user")
            mock_password_field.fill.assert_any_call("test_pass")
            mock_login_button.click.assert_called_once()
            assert mock_handle_cookie.called
            assert mock_print_cookies.called


@pytest.mark.asyncio
async def test_login_to_redhat_portal_failure():
    """测试登录失败的情况"""
    # 模拟Playwright Page和元素
    mock_page = AsyncMock()
    mock_context = AsyncMock()
    mock_username_field = AsyncMock()
    mock_password_field = AsyncMock()
    mock_login_button = AsyncMock()
    mock_error_message = AsyncMock()

    # 设置模拟行为
    mock_page.goto.return_value = AsyncMock()
    mock_page.wait_for_selector.side_effect = [
        mock_username_field,  # 用户名字段
        mock_password_field,  # 密码字段
        mock_login_button,  # 登录按钮
        TimeoutError("Timeout"),  # 登录超时
    ]

    # 模拟找到错误消息
    mock_page.query_selector.return_value = mock_error_message
    mock_error_message.text_content.return_value = "Invalid username or password"

    with patch("woodgate.core.auth.handle_cookie_popup", return_value=True):
        with patch("woodgate.core.auth.asyncio.sleep"):
            # 调用被测试的函数
            result = await login_to_redhat_portal(mock_page, mock_context, "test_user", "test_pass")

            # 验证结果
            assert result is False
            mock_page.goto.assert_called_once_with("https://access.redhat.com/login", wait_until="domcontentloaded")
            mock_username_field.fill.assert_any_call("test_user")
            mock_password_field.fill.assert_any_call("test_pass")
            mock_login_button.click.assert_called_once()


@pytest.mark.asyncio
async def test_check_login_status_logged_in():
    """测试已登录状态检查"""
    # 模拟Playwright Page和元素
    mock_page = AsyncMock()
    mock_user_menu = AsyncMock()

    # 设置模拟行为
    mock_page.goto.return_value = AsyncMock()
    mock_page.wait_for_selector.return_value = mock_user_menu

    # 调用被测试的函数
    result = await check_login_status(mock_page)

    # 验证结果
    assert result is True
    mock_page.goto.assert_called_once_with("https://access.redhat.com/management", wait_until="domcontentloaded")


@pytest.mark.asyncio
async def test_check_login_status_not_logged_in():
    """测试未登录状态检查"""
    # 模拟Playwright Page
    mock_page = AsyncMock()
    mock_page.url = "https://access.redhat.com/login"

    # 设置模拟行为 - 超时异常
    mock_page.goto.return_value = AsyncMock()
    mock_page.wait_for_selector.side_effect = TimeoutError("Timeout")

    # 调用被测试的函数
    result = await check_login_status(mock_page)

    # 验证结果
    assert result is False
    mock_page.goto.assert_called_once_with("https://access.redhat.com/management", wait_until="domcontentloaded")
