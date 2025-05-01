"""
认证模块测试
"""

import pytest
from unittest.mock import patch, MagicMock
from selenium.common.exceptions import TimeoutException

from woodgate.core.auth import login_to_redhat_portal, check_login_status


@pytest.mark.asyncio
async def test_login_to_redhat_portal_success():
    """测试成功登录到Red Hat客户门户"""
    # 模拟Selenium WebDriver和元素
    mock_driver = MagicMock()
    mock_username_field = MagicMock()
    mock_password_field = MagicMock()
    mock_login_button = MagicMock()
    mock_user_menu = MagicMock()

    # 模拟WebDriverWait和expected_conditions
    with patch("woodgate.core.auth.WebDriverWait") as mock_wait:
        with patch(
            "woodgate.core.auth.handle_cookie_popup", return_value=True
        ) as mock_handle_cookie:
            # 设置模拟行为
            mock_wait.return_value.until.side_effect = [
                mock_username_field,  # 用户名字段
                mock_password_field,  # 密码字段
                mock_login_button,  # 登录按钮
                mock_user_menu,  # 用户菜单（登录成功标志）
            ]

            # 调用被测试的函数
            result = await login_to_redhat_portal(mock_driver, "test_user", "test_pass")

            # 验证结果
            assert result is True
            mock_driver.get.assert_called_once_with("https://access.redhat.com/login")
            mock_username_field.send_keys.assert_called_once_with("test_user")
            mock_password_field.send_keys.assert_called_once_with("test_pass")
            mock_login_button.click.assert_called_once()
            assert mock_handle_cookie.called


@pytest.mark.asyncio
async def test_login_to_redhat_portal_failure():
    """测试登录失败的情况"""
    # 模拟Selenium WebDriver和元素
    mock_driver = MagicMock()
    mock_username_field = MagicMock()
    mock_password_field = MagicMock()
    mock_login_button = MagicMock()
    mock_error_message = MagicMock()
    mock_error_message.text = "Invalid username or password"

    # 模拟WebDriverWait和expected_conditions
    with patch("woodgate.core.auth.WebDriverWait") as mock_wait:
        with patch("woodgate.core.auth.handle_cookie_popup", return_value=True):
            with patch("woodgate.core.auth.asyncio.sleep"):
                # 设置模拟行为 - 用户名和密码字段正常，但登录后超时
                mock_wait.return_value.until.side_effect = [
                    mock_username_field,  # 用户名字段
                    mock_password_field,  # 密码字段
                    mock_login_button,  # 登录按钮
                    TimeoutException("Timeout"),  # 登录超时
                ]

                # 模拟找到错误消息
                mock_driver.find_element.return_value = mock_error_message

                # 调用被测试的函数
                result = await login_to_redhat_portal(mock_driver, "test_user", "test_pass")

                # 验证结果
                assert result is False
                mock_driver.get.assert_called_once_with("https://access.redhat.com/login")
                mock_username_field.send_keys.assert_called_once_with("test_user")
                mock_password_field.send_keys.assert_called_once_with("test_pass")
                mock_login_button.click.assert_called_once()


@pytest.mark.asyncio
async def test_check_login_status_logged_in():
    """测试已登录状态检查"""
    # 模拟Selenium WebDriver和元素
    mock_driver = MagicMock()
    mock_user_menu = MagicMock()

    # 模拟WebDriverWait和expected_conditions
    with patch("woodgate.core.auth.WebDriverWait") as mock_wait:
        # 设置模拟行为 - 找到用户菜单元素
        mock_wait.return_value.until.return_value = mock_user_menu

        # 调用被测试的函数
        result = await check_login_status(mock_driver)

        # 验证结果
        assert result is True
        mock_driver.get.assert_called_once_with("https://access.redhat.com/management")


@pytest.mark.asyncio
async def test_check_login_status_not_logged_in():
    """测试未登录状态检查"""
    # 模拟Selenium WebDriver
    mock_driver = MagicMock()
    mock_driver.current_url = "https://access.redhat.com/login"

    # 模拟WebDriverWait抛出超时异常
    with patch("woodgate.core.auth.WebDriverWait") as mock_wait:
        # 设置模拟行为 - 超时异常
        mock_wait.return_value.until.side_effect = Exception("Timeout")

        # 调用被测试的函数
        result = await check_login_status(mock_driver)

        # 验证结果
        assert result is False
        mock_driver.get.assert_called_once_with("https://access.redhat.com/management")
