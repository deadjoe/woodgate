"""
工具模块测试
"""

import logging
import pytest
from unittest.mock import patch, MagicMock
from selenium.common.exceptions import TimeoutException

from woodgate.core.utils import setup_logging, handle_cookie_popup, print_cookies


def test_setup_logging():
    """测试日志设置"""
    with patch("logging.basicConfig") as mock_basic_config:
        setup_logging(level=logging.DEBUG)
        mock_basic_config.assert_called_once()
        args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.DEBUG

        # 测试默认级别
        setup_logging()
        assert mock_basic_config.call_args[1]["level"] == logging.INFO


# 移除get_credentials测试，因为该函数在config.py中


@pytest.mark.asyncio
async def test_handle_cookie_popup_found():
    """测试处理Cookie弹窗 - 找到弹窗"""
    mock_driver = MagicMock()
    mock_wait = MagicMock()
    mock_cookie_notice = MagicMock()
    mock_button = MagicMock()

    # 模拟WebDriverWait
    with patch("woodgate.core.utils.WebDriverWait", return_value=mock_wait):
        # 模拟找到Cookie弹窗
        mock_wait.until.return_value = mock_cookie_notice
        # 模拟找到关闭按钮
        mock_cookie_notice.find_element.return_value = mock_button

        with patch("woodgate.core.utils.log_step") as mock_log:
            result = await handle_cookie_popup(mock_driver)

            assert result is True
            assert mock_wait.until.called
            assert mock_cookie_notice.find_element.called
            assert mock_log.called


@pytest.mark.asyncio
async def test_handle_cookie_popup_not_found():
    """测试处理Cookie弹窗 - 未找到弹窗"""
    mock_driver = MagicMock()
    mock_wait = MagicMock()

    # 模拟WebDriverWait
    with patch("woodgate.core.utils.WebDriverWait", return_value=mock_wait):
        # 模拟未找到Cookie弹窗
        mock_wait.until.side_effect = TimeoutException("Timeout")

        with patch("woodgate.core.utils.log_step") as mock_log:
            result = await handle_cookie_popup(mock_driver)

            assert result is False
            assert mock_wait.until.called
            assert mock_log.called


@pytest.mark.asyncio
async def test_handle_cookie_popup_error():
    """测试处理Cookie弹窗 - 发生错误"""
    mock_driver = MagicMock()

    # 模拟WebDriverWait抛出异常
    with patch("woodgate.core.utils.WebDriverWait", side_effect=Exception("Test error")):
        with patch("woodgate.core.utils.log_step") as mock_log:
            result = await handle_cookie_popup(mock_driver)

            assert result is False
            assert mock_log.called


# 移除wait_for_element和retry_on_exception测试，因为这些函数不在utils.py中


def test_print_cookies():
    """测试打印cookies"""
    mock_driver = MagicMock()
    mock_cookies = [
        {"name": "cookie1", "value": "value1", "domain": "example.com"},
        {"name": "cookie2", "value": "value2", "domain": "example.org"},
        {"name": "auth_token", "value": "token123", "domain": "example.com"},
        {"name": "session_id", "value": "session123", "domain": "example.org"},
    ]
    mock_driver.get_cookies.return_value = mock_cookies

    with patch("woodgate.core.utils.log_step") as mock_log:
        print_cookies(mock_driver)

        mock_driver.get_cookies.assert_called_once()
        assert mock_log.called
