"""
主模块测试
"""

from unittest.mock import MagicMock, patch

import pytest

from woodgate.__main__ import main, parse_args


class TestMain:
    """主模块测试"""

    def test_parse_args_default(self):
        """测试解析默认参数"""
        with patch("sys.argv", ["woodgate"]):
            args = parse_args()
            # 在__main__.py中，默认值为None，实际值由config提供
            assert args.host is None
            assert args.port is None
            assert args.log_level is None

    def test_parse_args_custom(self):
        """测试解析自定义参数"""
        with patch(
            "sys.argv", ["woodgate", "--host", "0.0.0.0", "--port", "8080", "--log-level", "DEBUG"]
        ):
            args = parse_args()
            assert args.host == "0.0.0.0"
            assert args.port == 8080
            assert args.log_level == "DEBUG"

    def test_main_function(self):
        """测试主函数"""
        mock_args = MagicMock()
        mock_args.host = "127.0.0.1"
        mock_args.port = 8000
        mock_args.log_level = "INFO"

        with patch("woodgate.__main__.parse_args", return_value=mock_args):
            with patch("woodgate.__main__.setup_logging") as mock_setup_logging:
                with patch("woodgate.__main__.mcp") as mock_mcp:
                    with patch("woodgate.__main__.print") as mock_print:
                        # 调用主函数
                        main()

                        # 验证调用
                        mock_setup_logging.assert_called_once()
                        mock_mcp.run.assert_called_once()
                        assert mock_print.call_count >= 3
