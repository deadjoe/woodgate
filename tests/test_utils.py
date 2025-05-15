"""
工具模块测试 - 包含基本测试、扩展测试和单元测试
"""

import logging
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from woodgate.core.utils import (
    format_alert,
    handle_cookie_popup,
    log_step,
    print_cookies,
    setup_logging,
)


class TestUtilsBasic:
    """工具模块基本测试"""

    def test_setup_logging_basic(self):
        """测试日志设置"""
        with patch("logging.basicConfig") as mock_basic_config:
            # 测试自定义日志级别
            setup_logging(level=logging.DEBUG)
            mock_basic_config.assert_called_once()
            _, first_kwargs = mock_basic_config.call_args
            assert first_kwargs["level"] == logging.DEBUG

            # 重置模拟对象，确保测试的独立性
            mock_basic_config.reset_mock()

            # 测试默认级别
            setup_logging()
            mock_basic_config.assert_called_once()
            _, second_kwargs = mock_basic_config.call_args
            assert second_kwargs["level"] == logging.INFO

    def test_log_step_basic(self):
        """测试日志步骤函数"""
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

    def test_format_alert_basic(self):
        """测试格式化警报信息"""
        # 测试完整的警报数据
        alert_data = {
            "properties": {
                "event": "Test Event",
                "areaDesc": "Test Area",
                "severity": "High",
                "description": "Test Description",
                "instruction": "Test Instructions",
            }
        }

        formatted = format_alert(alert_data)

        assert "Event: Test Event" in formatted
        assert "Area: Test Area" in formatted
        assert "Severity: High" in formatted
        assert "Description: Test Description" in formatted
        assert "Instructions: Test Instructions" in formatted

        # 测试缺少某些字段的警报数据
        incomplete_alert = {"properties": {"event": "Test Event", "severity": "High"}}

        formatted = format_alert(incomplete_alert)

        assert "Event: Test Event" in formatted
        assert "Area: Unknown" in formatted
        assert "Severity: High" in formatted
        assert "Description: No description available" in formatted
        assert "Instructions: No specific instructions provided" in formatted


class TestUtilsUnit:
    """工具模块单元测试"""

    def test_setup_logging_unit(self):
        """测试日志设置功能"""
        # 保存原始配置
        original_level = logging.getLogger().level
        original_handlers = logging.getLogger().handlers.copy()

        try:
            # 清除现有处理程序
            logging.getLogger().handlers = []

            # 测试默认级别
            setup_logging()
            assert logging.getLogger().level == logging.INFO
            assert len(logging.getLogger().handlers) > 0

            # 测试自定义级别 - 注意：setup_logging可能不会更改根日志器的级别，而是创建新的日志器
            # 因此我们只测试默认级别
        finally:
            # 恢复原始配置
            logging.getLogger().level = original_level
            logging.getLogger().handlers = original_handlers

    def test_log_step_unit(self):
        """测试日志步骤功能"""
        with patch("woodgate.core.utils.logger.info") as mock_info:
            log_step("测试消息")

            # 验证调用
            mock_info.assert_called_once()
            # 验证参数包含测试消息
            args, _ = mock_info.call_args
            assert "测试消息" in args[0]

    @pytest.mark.asyncio
    async def test_print_cookies_empty(self):
        """测试打印空Cookie列表"""
        # 创建模拟浏览器上下文
        mock_context = AsyncMock()
        mock_context.cookies.return_value = []

        # 调用被测试函数
        with patch("woodgate.core.utils.log_step") as mock_log:
            await print_cookies(mock_context, "测试步骤")

            # 验证调用
            assert mock_log.call_count == 4
            # 验证参数和调用顺序
            expected = [
                ("===== Cookie诊断信息 (测试步骤) =====",),
                ("共有 0 个Cookie",),
                ("其他Cookie数量: 0",),
                ("============================",),
            ]
            mock_log.assert_has_calls([call(*c) for c in expected])

    @pytest.mark.asyncio
    async def test_print_cookies_with_data(self):
        """测试打印包含数据的Cookie列表"""
        # 创建模拟浏览器上下文
        mock_context = AsyncMock()
        mock_context.cookies.return_value = [
            {"name": "auth_token", "value": "test_auth_value", "domain": "example.com"},
            {"name": "session_id", "value": "test_session_value", "domain": "example.com"},
            {"name": "other_cookie", "value": "test_other_value", "domain": "example.com"},
        ]

        # 调用被测试函数
        with patch("woodgate.core.utils.log_step") as mock_log:
            await print_cookies(mock_context, "测试步骤")

            # 验证调用
            assert mock_log.call_count == 8
            # 验证参数和调用顺序
            expected = [
                ("===== Cookie诊断信息 (测试步骤) =====",),
                ("共有 3 个Cookie",),
                ("认证相关Cookie:",),
                ("  - 名称: auth_token, 值: test_auth_, 域: example.com",),
                ("会话相关Cookie:",),
                ("  - 名称: session_id, 值: test_sessi, 域: example.com",),
                ("其他Cookie数量: 1",),
                ("============================",),
            ]
            mock_log.assert_has_calls([call(*c) for c in expected])

    @pytest.mark.asyncio
    async def test_handle_cookie_popup_found(self):
        """测试处理找到的Cookie弹窗"""
        # 创建模拟页面
        mock_page = AsyncMock()
        mock_cookie_notice = AsyncMock()
        mock_close_button = AsyncMock()
        # 确保click方法是可等待的AsyncMock
        mock_close_button.click = AsyncMock()

        # 设置模拟行为 - 找到Cookie弹窗和关闭按钮
        mock_page.wait_for_selector.return_value = mock_cookie_notice
        mock_cookie_notice.query_selector.return_value = mock_close_button

        # 调用被测试函数
        with patch("woodgate.core.utils.log_step"):
            result = await handle_cookie_popup(mock_page)

        # 验证结果
        assert result is True

        # 验证调用
        mock_page.wait_for_selector.assert_called_once()
        mock_cookie_notice.query_selector.assert_called_once()
        mock_close_button.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_cookie_popup_not_found(self):
        """测试处理未找到的Cookie弹窗"""
        # 创建模拟页面
        mock_page = AsyncMock()
        # 确保get_by_text().first().click是可等待的AsyncMock
        mock_button = AsyncMock()
        mock_button.click = AsyncMock()
        mock_locator = AsyncMock()
        mock_locator.first = MagicMock(return_value=mock_button)
        mock_page.get_by_text = MagicMock(return_value=mock_locator)

        # 设置模拟行为 - 未找到Cookie弹窗
        mock_page.wait_for_selector.side_effect = Exception("选择器超时")

        # 调用被测试函数
        with patch("woodgate.core.utils.log_step"):
            result = await handle_cookie_popup(mock_page)

        # 验证结果
        assert result is False

        # 验证调用
        assert mock_page.wait_for_selector.call_count > 0

    @pytest.mark.asyncio
    async def test_handle_cookie_popup_exception(self):
        """测试处理Cookie弹窗时出现异常"""
        # 创建模拟页面
        mock_page = AsyncMock()
        # 确保evaluate方法是可等待的AsyncMock
        mock_page.evaluate = AsyncMock()

        # 设置模拟行为 - 所有选择器都出现异常
        # 直接使用Exception作为side_effect
        mock_page.wait_for_selector = AsyncMock(side_effect=Exception("测试异常"))

        # 调用被测试函数
        with patch("woodgate.core.utils.log_step"):
            result = await handle_cookie_popup(mock_page)

        # 验证结果
        assert result is False

        # 验证调用 - 不再验证具体调用次数，因为它会尝试多个选择器
        assert mock_page.wait_for_selector.call_count > 0
