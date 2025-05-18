#!/bin/bash
# 全面的质量检查脚本
# 整合已有工具和新增优化点

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的标题
print_header() {
    echo -e "\n${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}"
}

# 检查命令执行状态
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 通过${NC}"
    else
        echo -e "${RED}✗ 失败${NC}"
        if [ "$2" = "exit" ]; then
            exit 1
        fi
    fi
}

# 代码格式化
run_formatting() {
    print_header "运行代码格式化"

    echo -e "${YELLOW}运行 Black 格式化...${NC}"
    uv run black woodgate tests
    check_status "Black 格式化"

    echo -e "${YELLOW}运行 isort 导入排序...${NC}"
    uv run isort woodgate tests
    check_status "isort 导入排序"
}

# 静态代码分析
run_static_analysis() {
    print_header "运行静态代码分析"

    echo -e "${YELLOW}运行 Ruff 检查...${NC}"
    uv run ruff check woodgate tests
    check_status "Ruff 检查"

    echo -e "${YELLOW}运行 flake8 检查...${NC}"
    uv run flake8 woodgate tests
    check_status "flake8 检查"

    echo -e "${YELLOW}运行 pylint 检查...${NC}"
    uv run pylint woodgate
    # pylint 可能会返回非零状态码，但我们不想因此停止脚本
    echo -e "${YELLOW}pylint 检查完成 (警告可能存在)${NC}"

    echo -e "${YELLOW}运行 mypy 类型检查...${NC}"
    uv run mypy woodgate
    # mypy 可能会返回非零状态码，但我们不想因此停止脚本
    echo -e "${YELLOW}mypy 类型检查完成 (警告可能存在)${NC}"
}

# 运行测试
run_tests() {
    print_header "运行测试套件"

    echo -e "${YELLOW}运行单元测试...${NC}"
    uv run pytest -v
    check_status "单元测试"

    echo -e "${YELLOW}运行覆盖率测试...${NC}"
    uv run pytest --cov=woodgate --cov-report=term --cov-report=html
    check_status "覆盖率测试"

    echo -e "${GREEN}测试报告已生成在 htmlcov/ 目录${NC}"
}

# 生成文档
generate_docs() {
    print_header "生成文档"

    # 检查 docs 目录是否存在
    if [ ! -d "docs" ]; then
        echo -e "${YELLOW}初始化 Sphinx 文档...${NC}"
        mkdir -p docs
        cd docs
        sphinx-quickstart --no-sep -p woodgate -a "DEADJOE" -v "0.1.0" -l zh_CN --ext-autodoc --ext-viewcode
        cd ..
    fi

    echo -e "${YELLOW}生成 API 文档...${NC}"
    cd docs
    uv run sphinx-apidoc -f -o source ../woodgate

    echo -e "${YELLOW}构建 HTML 文档...${NC}"
    uv run make html
    check_status "文档生成"
    cd ..

    echo -e "${GREEN}文档已生成在 docs/_build/html/ 目录${NC}"
}

# 主函数
main() {
    print_header "开始全面质量检查"

    # 检查参数
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        echo "用法: $0 [选项]"
        echo "选项:"
        echo "  --format    只运行代码格式化"
        echo "  --lint      只运行静态代码分析"
        echo "  --test      只运行测试"
        echo "  --docs      只生成文档"
        echo "  --all       运行所有检查 (默认)"
        echo "  --help, -h  显示此帮助信息"
        exit 0
    fi

    # 根据参数执行不同的检查
    if [ "$1" = "--format" ]; then
        run_formatting
    elif [ "$1" = "--lint" ]; then
        run_static_analysis
    elif [ "$1" = "--test" ]; then
        run_tests
    elif [ "$1" = "--docs" ]; then
        generate_docs
    else
        # 默认运行所有检查
        run_formatting
        run_static_analysis
        run_tests
        generate_docs
    fi

    print_header "质量检查完成"
}

# 执行主函数
main "$@"
