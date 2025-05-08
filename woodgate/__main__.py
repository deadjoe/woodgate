"""
主模块 - 提供命令行入口点
"""

import argparse
import logging
import sys

from .config import get_config
from .core.utils import setup_logging

# FastMCP类有run方法，不需要单独导入run_server
from .server import mcp


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Woodgate - Red Hat客户门户搜索MCP服务器")

    parser.add_argument("--host", type=str, default=None, help="服务器主机地址 (默认: 127.0.0.1)")

    parser.add_argument("--port", type=int, default=None, help="服务器端口 (默认: 8000)")

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="日志级别 (默认: INFO)",
    )

    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()

    # 获取配置
    config = get_config()

    # 命令行参数覆盖配置
    host = args.host or config["host"]
    port = args.port or config["port"]
    log_level = args.log_level or config["log_level"]

    # 设置日志
    setup_logging(level=getattr(logging, log_level))

    # 打印启动信息
    print("准备启动Woodgate MCP服务器...")
    print("使用Ctrl+C停止服务器")

    # 运行服务器
    try:
        # 更新FastMCP的settings属性
        mcp.settings.host = host
        mcp.settings.port = port
        mcp.settings.log_level = log_level

        # 使用FastMCP的run方法启动服务器
        print(f"启动Woodgate MCP服务器 (transport=sse, host={host}, port={port})...")
        mcp.run(transport="sse")
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动服务器时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
