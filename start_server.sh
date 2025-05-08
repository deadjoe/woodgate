#!/bin/bash
# 启动 Red Hat KB Search 服务器的脚本

# 输出彩色日志
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 启动 Red Hat KB Search 服务器 ===${NC}"

# 切换到项目目录
cd "$(dirname "$0")"
echo -e "${BLUE}当前工作目录: $(pwd)${NC}"

# 激活虚拟环境
source .venv/bin/activate
echo -e "${BLUE}已激活虚拟环境${NC}"

# 设置环境变量
export WOODGATE_LOG_LEVEL="DEBUG"
export PYTHONUNBUFFERED=1  # 禁用Python输出缓冲
export LOGLEVEL=DEBUG      # 设置日志级别为DEBUG
export PYTHONTRACEMALLOC=1 # 启用内存分配跟踪
export PYTHONASYNCIODEBUG=1 # 启用asyncio调试
echo -e "${BLUE}已设置环境变量${NC}"

# 注意：凭据已内置在代码中，无需设置环境变量
# 如需使用不同凭据，可取消下面两行的注释并修改
# export REDHAT_USERNAME="your_username"
# export REDHAT_PASSWORD="your_password"

# 创建日志和截图目录
mkdir -p logs
mkdir -p screenshots
echo -e "${BLUE}已创建日志和截图目录${NC}"

# 清理旧的截图文件
find screenshots -type f -mtime +1 -delete
echo -e "${BLUE}已清理旧的截图文件${NC}"

# 显示启动信息
echo -e "${YELLOW}启动参数:${NC}"
echo -e "  主机: 0.0.0.0"
echo -e "  端口: 8080"
echo -e "  日志级别: DEBUG"
echo -e "  用户名: 使用内置凭据${REDHAT_USERNAME:+ (覆盖: $REDHAT_USERNAME)}"
echo -e "${GREEN}正在启动服务器...${NC}"

# 启动服务器，同时将输出重定向到日志文件
LOG_FILE="logs/server_$(date +%Y%m%d_%H%M%S).log"
echo -e "${BLUE}日志文件: $LOG_FILE${NC}"

# 直接启动服务器，依赖PYTHONUNBUFFERED环境变量确保输出不被缓冲
uv run python -m woodgate --host 0.0.0.0 --port 8080 --log-level DEBUG 2>&1 | tee "$LOG_FILE"
