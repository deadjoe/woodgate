"""
认证模块扩展测试
"""

from unittest.mock import MagicMock, patch

import pytest
from selenium.common.exceptions import TimeoutException

from woodgate.core.auth import check_login_status, handle_cookie_popup, login_to_redhat_portal


@pytest.mark.asyncio
async def test_login_to_redhat_portal_cookie_popup_error():
    """测试登录 - Cookie弹窗处理错误"""
    mock_driver = MagicMock()

    # 模拟handle_cookie_popup函数返回False
    with patch("woodgate.core.auth.handle_cookie_popup", return_value=False):
        # 模拟登录过程中的异常
        mock_driver.get.side_effect = Exception("Connection error")

        with patch("woodgate.core.auth.logger.error") as mock_error:
            with patch("woodgate.core.auth.log_step"):
                result = await login_to_redhat_portal(mock_driver, "test_user", "test_pass")

                assert result is False
                assert mock_error.called


@pytest.mark.asyncio
async def test_login_to_redhat_portal_username_field_not_found():
    """测试登录 - 用户名字段未找到"""
    mock_driver = MagicMock()

    with patch("woodgate.core.auth.handle_cookie_popup", return_value=True):
        with patch("woodgate.core.auth.WebDriverWait") as mock_wait:
            # 模拟等待用户名字段超时
            mock_wait.return_value.until.side_effect = TimeoutException(
                "Timeout waiting for username field"
            )

            with patch("woodgate.core.auth.logger.error") as mock_error:
                with patch("woodgate.core.auth.log_step"):
                    with patch("woodgate.core.auth.asyncio.sleep"):
                        result = await login_to_redhat_portal(
                            mock_driver, "test_user", "test_pass", max_retries=1
                        )

                        assert result is False
                        assert mock_error.called


@pytest.mark.asyncio
async def test_login_to_redhat_portal_password_field_not_found():
    """测试登录 - 密码字段未找到"""
    mock_driver = MagicMock()
    mock_username_field = MagicMock()

    with patch("woodgate.core.auth.handle_cookie_popup", return_value=True):
        with patch("woodgate.core.auth.WebDriverWait") as mock_wait:
            # 模拟找到用户名字段但密码字段超时
            mock_wait.return_value.until.side_effect = [
                mock_username_field,  # 用户名字段
                TimeoutException("Timeout waiting for password field"),  # 密码字段超时
            ]

            with patch("woodgate.core.auth.logger.error") as mock_error:
                with patch("woodgate.core.auth.log_step"):
                    with patch("woodgate.core.auth.asyncio.sleep"):
                        result = await login_to_redhat_portal(
                            mock_driver, "test_user", "test_pass", max_retries=1
                        )

                        assert result is False
                        assert mock_error.called


@pytest.mark.asyncio
async def test_login_to_redhat_portal_login_button_not_found():
    """测试登录 - 登录按钮未找到"""
    mock_driver = MagicMock()
    mock_username_field = MagicMock()
    mock_password_field = MagicMock()

    with patch("woodgate.core.auth.handle_cookie_popup", return_value=True):
        with patch("woodgate.core.auth.WebDriverWait") as mock_wait:
            # 模拟找到用户名和密码字段但登录按钮超时
            mock_wait.return_value.until.side_effect = [
                mock_username_field,  # 用户名字段
                mock_password_field,  # 密码字段
                TimeoutException("Timeout waiting for login button"),  # 登录按钮超时
            ]

            with patch("woodgate.core.auth.logger.error") as mock_error:
                with patch("woodgate.core.auth.log_step"):
                    with patch("woodgate.core.auth.asyncio.sleep"):
                        result = await login_to_redhat_portal(
                            mock_driver, "test_user", "test_pass", max_retries=1
                        )

                        assert result is False
                        assert mock_error.called


@pytest.mark.asyncio
async def test_check_login_status_error():
    """测试检查登录状态 - 发生错误"""
    mock_driver = MagicMock()
    mock_driver.get.side_effect = Exception("Test error")

    with patch("woodgate.core.auth.logger.error") as mock_error:
        with patch("woodgate.core.auth.log_step"):
            result = await check_login_status(mock_driver)

            assert result is False
            assert mock_error.called


@pytest.mark.asyncio
async def test_handle_cookie_popup_detailed():
    """测试处理Cookie弹窗 - 详细测试"""
    mock_driver = MagicMock()
    mock_wait = MagicMock()
    mock_cookie_notice = MagicMock()
    mock_button = MagicMock()

    # 测试场景1: 找到弹窗和按钮
    with patch("woodgate.core.utils.WebDriverWait", return_value=mock_wait):
        with patch("woodgate.core.utils.log_step"):
            # 模拟找到Cookie弹窗
            mock_wait.until.return_value = mock_cookie_notice
            # 模拟找到关闭按钮
            mock_cookie_notice.find_element.return_value = mock_button

            result = await handle_cookie_popup(mock_driver)
            assert result is True
            assert mock_wait.until.called
            assert mock_cookie_notice.find_element.called

    # 测试场景2: 找到弹窗但按钮点击失败
    with patch("woodgate.core.utils.WebDriverWait", return_value=mock_wait):
        with patch("woodgate.core.utils.log_step"):
            # 模拟找到Cookie弹窗
            mock_wait.until.return_value = mock_cookie_notice
            # 模拟找到关闭按钮但点击失败
            mock_cookie_notice.find_element.side_effect = Exception("Element not found")
            # 模拟driver.find_element也失败
            mock_driver.find_element.side_effect = Exception("Element not found")

            result = await handle_cookie_popup(mock_driver)
            assert result is False

    # 测试场景3: 未找到弹窗
    with patch("woodgate.core.utils.WebDriverWait", return_value=mock_wait):
        with patch("woodgate.core.utils.log_step"):
            # 模拟未找到Cookie弹窗
            mock_wait.until.side_effect = TimeoutException("Timeout")

            result = await handle_cookie_popup(mock_driver)
            assert result is False
