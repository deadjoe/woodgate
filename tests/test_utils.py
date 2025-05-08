"""
工具模块测试
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from playwright.async_api import Error, TimeoutError

from woodgate.core.utils import handle_cookie_popup, print_cookies, setup_logging


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


def test_log_step():
    """测试日志步骤函数"""
    from woodgate.core.utils import log_step

    with patch("woodgate.core.utils.logger") as mock_logger:
        with patch("woodgate.core.utils.time") as mock_time:
            # 模拟时间
            mock_time.strftime.return_value = "2023-01-01 12:00:00"
            mock_time.localtime.return_value = "mocked_time"

            # 调用被测试的函数
            log_step("Test message")

            # 验证结果
            mock_time.strftime.assert_called_once_with("%Y-%m-%d %H:%M:%S", "mocked_time")
            mock_logger.info.assert_called_once_with("[2023-01-01 12:00:00] Test message")


@pytest.mark.asyncio
async def test_handle_cookie_popup_found():
    """测试处理Cookie弹窗 - 找到弹窗"""
    mock_page = AsyncMock()
    mock_cookie_notice = AsyncMock()
    mock_button = AsyncMock()

    # 模拟找到Cookie弹窗
    mock_page.wait_for_selector.return_value = mock_cookie_notice
    # 模拟找到关闭按钮
    mock_cookie_notice.query_selector.return_value = mock_button

    with patch("woodgate.core.utils.log_step") as mock_log:
        result = await handle_cookie_popup(mock_page)

        assert result is True
        assert mock_page.wait_for_selector.called
        assert mock_cookie_notice.query_selector.called
        assert mock_button.click.called
        assert mock_log.called


@pytest.mark.asyncio
async def test_handle_cookie_popup_not_found():
    """测试处理Cookie弹窗 - 未找到弹窗"""
    mock_page = AsyncMock()

    # 模拟未找到Cookie弹窗
    mock_page.wait_for_selector.side_effect = TimeoutError("Timeout")

    with patch("woodgate.core.utils.log_step") as mock_log:
        result = await handle_cookie_popup(mock_page)

        assert result is False
        assert mock_page.wait_for_selector.called
        assert mock_log.called


@pytest.mark.asyncio
async def test_handle_cookie_popup_error():
    """测试处理Cookie弹窗 - 发生错误"""
    mock_page = AsyncMock()

    # 模拟页面操作抛出异常
    mock_page.wait_for_selector.side_effect = Exception("Test error")

    with patch("woodgate.core.utils.log_step") as mock_log:
        result = await handle_cookie_popup(mock_page)

        assert result is False
        assert mock_log.called


# 移除wait_for_element和retry_on_exception测试，因为这些函数不在utils.py中


@pytest.mark.asyncio
async def test_print_cookies():
    """测试打印cookies"""
    mock_context = AsyncMock()
    mock_cookies = [
        {"name": "cookie1", "value": "value1", "domain": "example.com"},
        {"name": "cookie2", "value": "value2", "domain": "example.org"},
        {"name": "auth_token", "value": "token123", "domain": "example.com"},
        {"name": "session_id", "value": "session123", "domain": "example.org"},
    ]
    mock_context.cookies.return_value = mock_cookies

    with patch("woodgate.core.utils.log_step") as mock_log:
        await print_cookies(mock_context)

        mock_context.cookies.assert_called_once()
        assert mock_log.called


def test_format_alert():
    """测试格式化警报信息"""
    from woodgate.core.utils import format_alert

    # 测试完整的警报数据
    alert_data = {
        "properties": {
            "event": "Test Event",
            "areaDesc": "Test Area",
            "severity": "High",
            "description": "Test Description",
            "instruction": "Test Instructions"
        }
    }

    formatted = format_alert(alert_data)

    assert "Event: Test Event" in formatted
    assert "Area: Test Area" in formatted
    assert "Severity: High" in formatted
    assert "Description: Test Description" in formatted
    assert "Instructions: Test Instructions" in formatted

    # 测试缺少某些字段的警报数据
    incomplete_alert = {
        "properties": {
            "event": "Test Event",
            "severity": "High"
        }
    }

    formatted = format_alert(incomplete_alert)

    assert "Event: Test Event" in formatted
    assert "Area: Unknown" in formatted
    assert "Severity: High" in formatted
    assert "Description: No description available" in formatted
    assert "Instructions: No specific instructions provided" in formatted
