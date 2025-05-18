#!/bin/bash
# 安装和设置开发工具脚本

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}安装和设置开发工具${NC}"
echo -e "${BLUE}======================================${NC}"

# 安装开发依赖
echo -e "${YELLOW}安装开发依赖...${NC}"
uv pip install -e ".[dev]"

# 初始化 pre-commit
echo -e "${YELLOW}初始化 pre-commit...${NC}"
pre-commit install

# 安装 Playwright 浏览器
echo -e "${YELLOW}安装 Playwright 浏览器...${NC}"
python -m playwright install chromium

# 初始化 Sphinx 文档
if [ ! -d "docs" ] || [ ! -f "docs/conf.py" ]; then
    echo -e "${YELLOW}初始化 Sphinx 文档...${NC}"
    mkdir -p docs
    cd docs
    sphinx-quickstart --no-sep -p woodgate -a "DEADJOE" -v "0.1.0" -l zh_CN --ext-autodoc --ext-viewcode
    cd ..
fi

echo -e "${GREEN}开发工具安装和设置完成！${NC}"
echo -e "${YELLOW}您现在可以使用以下命令：${NC}"
echo -e "  ${GREEN}./run_all_checks.sh${NC} - 运行所有检查"
echo -e "  ${GREEN}./run_all_checks.sh --format${NC} - 只运行代码格式化"
echo -e "  ${GREEN}./run_all_checks.sh --lint${NC} - 只运行静态代码分析"
echo -e "  ${GREEN}./run_all_checks.sh --test${NC} - 只运行测试"
echo -e "  ${GREEN}./run_all_checks.sh --docs${NC} - 只生成文档"
echo -e "  ${GREEN}pre-commit run --all-files${NC} - 手动运行所有预提交检查"
