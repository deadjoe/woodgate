#!/usr/bin/env python
"""
MCP服务器入口点
"""

import os
import sys
import logging
import subprocess
import importlib.util

# 环境变量应该在运行时设置，而不是硬编码在代码中
# 例如: export REDHAT_USERNAME="your_username" && export REDHAT_PASSWORD="your_password"

# 设置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stderr)
logger = logging.getLogger("woodgate-mcp")

# 检查并安装必要的依赖
required_packages = ['selenium', 'webdriver-manager', 'httpx']

for package in required_packages:
    if importlib.util.find_spec(package) is None:
        logger.info(f"正在安装 {package}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            logger.info(f"{package} 安装成功")
        except Exception as e:
            logger.error(f"安装 {package} 失败: {e}")
            sys.exit(1)
    else:
        logger.info(f"{package} 已安装")

try:
    logger.info("正在导入woodgate.server模块...")
    # 确保当前目录在Python路径中
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    # 尝试导入
    from woodgate.server import mcp
    logger.info("成功导入woodgate.server模块")
except ImportError as e:
    logger.error(f"导入错误: {e}")
    # 尝试直接导入
    try:
        logger.info("尝试直接导入server.py...")
        import server
        mcp = server.mcp
        logger.info("成功导入server.py")
    except ImportError as e2:
        logger.error(f"直接导入失败: {e2}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("启动Woodgate MCP服务器...")
    try:
        mcp.run(transport="sse")
    except Exception as e:
        logger.error(f"启动服务器时出错: {e}")
        sys.exit(1)
