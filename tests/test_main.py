"""
主模块测试
"""

from unittest.mock import MagicMock, patch

from woodgate.__main__ import main, parse_args


def test_parse_args_defaults():
    """测试参数解析 - 默认值"""
    with patch("sys.argv", ["woodgate"]):
        args = parse_args()
        # 在__main__.py中，默认值为None，实际值由config提供
        assert args.host is None
        assert args.port is None
        assert args.log_level is None


def test_parse_args_custom():
    """测试参数解析 - 自定义值"""
    with patch(
        "sys.argv", ["woodgate", "--host", "0.0.0.0", "--port", "9000", "--log-level", "DEBUG"]
    ):
        args = parse_args()
        assert args.host == "0.0.0.0"
        assert args.port == 9000
        assert args.log_level == "DEBUG"


def test_main_success():
    """测试主函数 - 成功"""
    mock_args = MagicMock()
    mock_args.host = "127.0.0.1"
    mock_args.port = 8000
    mock_args.log_level = "INFO"

    with patch("woodgate.__main__.parse_args", return_value=mock_args):
        with patch("woodgate.__main__.setup_logging") as mock_setup_logging:
            with patch("woodgate.__main__.mcp") as mock_mcp:
                with patch("woodgate.__main__.print") as mock_print:
                    # 模拟正常运行
                    main()

                    # 验证调用
                    mock_setup_logging.assert_called_once()
                    mock_mcp.run.assert_called_once()
                    assert mock_print.call_count >= 3


def test_main_keyboard_interrupt():
    """测试主函数 - 键盘中断"""
    mock_args = MagicMock()
    mock_args.host = "127.0.0.1"
    mock_args.port = 8000
    mock_args.log_level = "INFO"

    with patch("woodgate.__main__.parse_args", return_value=mock_args):
        with patch("woodgate.__main__.setup_logging"):
            with patch("woodgate.__main__.mcp") as mock_mcp:
                with patch("woodgate.__main__.print") as mock_print:
                    # 模拟键盘中断
                    mock_mcp.run.side_effect = KeyboardInterrupt()

                    main()

                    # 验证调用
                    mock_mcp.run.assert_called_once()
                    mock_print.assert_any_call("\n服务器已停止")


def test_main_exception():
    """测试主函数 - 异常"""
    mock_args = MagicMock()
    mock_args.host = "127.0.0.1"
    mock_args.port = 8000
    mock_args.log_level = "INFO"

    with patch("woodgate.__main__.parse_args", return_value=mock_args):
        with patch("woodgate.__main__.setup_logging"):
            with patch("woodgate.__main__.mcp") as mock_mcp:
                with patch("woodgate.__main__.print") as mock_print:
                    with patch("woodgate.__main__.sys.exit") as mock_exit:
                        # 模拟异常
                        mock_mcp.run.side_effect = Exception("Test error")

                        main()

                        # 验证调用
                        mock_mcp.run.assert_called_once()
                        mock_print.assert_any_call("启动服务器时出错: Test error")
                        mock_exit.assert_called_once_with(1)
