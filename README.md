<div align="center">
  <img src="woodgate.png" width="256" height="256" alt="Woodgate Logo" />
</div>

# Woodgate

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Tests](https://github.com/deadjoe/woodgate/actions/workflows/python-tests.yml/badge.svg)](https://github.com/deadjoe/woodgate/actions/workflows/python-tests.yml)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/Playwright-1.40%2B-green)](https://playwright.dev/)
[![MCP](https://img.shields.io/badge/MCP-1.6%2B-purple)](https://modelcontextprotocol.io/)

一个基于Model Context Protocol (MCP)的服务器，用于自动化搜索和从Red Hat客户门户提取数据。

## 功能特点

- 基于MCP协议的标准服务器，可与Claude等LLM集成
- 使用Playwright实现高效的浏览器自动化
- 自动登录到Red Hat客户门户
- 可配置的搜索参数（查询、产品、文档类型、分页）
- 结果提取与可配置的排序选项
- 强大的Cookie弹窗处理
- 详细的日志记录和诊断
- 模块化设计，便于维护和扩展
- 完善的单元测试
- 支持uv包管理工具（已测试兼容uv 0.7.2+）
- 便捷的启动脚本，一键启动服务器

## 系统要求

- Python 3.10+
- 必要的Python包（见`requirements.txt`）
- MCP SDK 1.6+
- Playwright 1.40+（会自动安装浏览器）

## 安装

1. 克隆仓库:

   ```bash
   git clone https://github.com/deadjoe/woodgate.git
   cd woodgate
   ```

2. 使用uv创建虚拟环境并安装依赖:

   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```

3. 设置环境变量进行安全认证:

   ```bash
   export REDHAT_USERNAME="your_username"
   export REDHAT_PASSWORD="your_password"
   ```

4. 可选的环境变量配置:

   ```bash
   # 浏览器配置
   export WOODGATE_HEADLESS="true"  # 是否使用无头模式
   export WOODGATE_BROWSER_TIMEOUT="20"  # 浏览器操作超时时间(秒)

   # 搜索配置
   export WOODGATE_DEFAULT_ROWS="20"  # 默认每页结果数
   export WOODGATE_DEFAULT_SORT="relevant"  # 默认排序方式

   # 服务器配置
   export WOODGATE_HOST="127.0.0.1"  # 服务器主机地址
   export WOODGATE_PORT="8000"  # 服务器端口

   # 日志配置
   export WOODGATE_LOG_LEVEL="INFO"  # 日志级别

   # 重试配置
   export WOODGATE_MAX_RETRIES="3"  # 最大重试次数
   export WOODGATE_RETRY_DELAY="3"  # 重试延迟(秒)
   ```

## 使用方法

### 使用启动脚本运行

最简单的方法是使用提供的启动脚本：

```bash
./start_server.sh
```

这将自动：

- 激活虚拟环境
- 设置必要的环境变量
- 创建日志和截图目录
- 启动服务器（主机：0.0.0.0，端口：8080，日志级别：DEBUG）
- 将日志输出重定向到日志文件

### 作为MCP服务器运行

手动运行MCP服务器:

```bash
uv run python -m woodgate
```

或者指定主机、端口和日志级别:

```bash
uv run python -m woodgate --host 0.0.0.0 --port 8080 --log-level DEBUG
```

### 与Claude Desktop集成

安装到Claude Desktop:

```bash
# 安装MCP服务器到Claude Desktop（凭据已内置）
/path/to/venv/bin/mcp install server.py:mcp --name "Red Hat KB Search"
```

如果您使用的是项目的虚拟环境，命令应该是:

```bash
.venv/bin/mcp install server.py:mcp --name "Red Hat KB Search"
```

要启动带有调试日志的开发服务器:

```bash
export PYTHONUNBUFFERED=1
export LOGLEVEL=DEBUG
.venv/bin/mcp dev server.py:mcp
```

注意：系统已内置默认凭据，无需设置环境变量。如果需要使用不同的凭据，可以设置环境变量：

```bash
export REDHAT_USERNAME="your_username"
export REDHAT_PASSWORD="your_password"
```

### MCP工具使用示例

在支持MCP的客户端中，可以使用以下工具:

```python
# 基本搜索
search(query="memory leak")

# 带产品过滤的搜索
search(
    query="kubernetes pod crash",
    products=["Red Hat OpenShift Container Platform"]
)

# 带文档类型过滤的搜索
search(
    query="selinux permission denied",
    doc_types=["Solution", "Article"]
)

# 完整搜索示例
search(
    query="performance tuning",
    products=["Red Hat Enterprise Linux"],
    doc_types=["Solution", "Article", "Documentation"],
    page=1,
    rows=50,
    sort_by="lastModifiedDate desc"
)

# 获取产品警报
get_alerts(product="Red Hat Enterprise Linux")

# 获取文档内容
get_document(document_url="https://access.redhat.com/solutions/12345")
```

可用的产品和文档类型可以通过MCP资源获取:

```python
# 获取可用产品列表
available_products = mcp.resources["config://products"]

# 获取可用文档类型
document_types = mcp.resources["config://doc-types"]
```

## 安全说明

- 系统已内置默认凭据，可直接使用
- 如需使用不同凭据，可通过环境变量覆盖：`REDHAT_USERNAME` 和 `REDHAT_PASSWORD`
- 在生产环境中，建议使用环境变量或配置文件管理凭据
- 确保凭据信息不被提交到公共代码仓库
- 凭据存储在服务器端，不需要在Claude Desktop端配置

## 开发

### 运行测试

```bash
# 安装测试依赖
uv pip install -e ".[dev]"
python -m playwright install

# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_auth.py

# 运行测试并生成覆盖率报告
uv run pytest --cov=woodgate --cov-report=term-missing

# 运行Playwright测试
uv run pytest tests/test_with_playwright_fixtures.py

# 运行Playwright测试并指定浏览器
uv run pytest tests/test_with_playwright_fixtures.py --browser firefox

# 运行Playwright测试并启用有头模式
uv run pytest tests/test_with_playwright_fixtures.py --headed

# 运行Playwright测试并启用调试模式
PWDEBUG=1 uv run pytest tests/test_with_playwright_fixtures.py

# 运行Playwright测试并生成跟踪文件
uv run pytest tests/test_with_playwright_fixtures.py
# 查看跟踪文件
playwright show-trace trace.zip
```


### 代码格式化

```bash
uv run black woodgate tests
uv run isort woodgate tests
uv run flake8 woodgate tests
```

## 项目结构

```text
woodgate/
├── __init__.py          # 包初始化
├── __main__.py          # 命令行入口点
├── config.py            # 配置管理
├── server.py            # MCP服务器定义
└── core/                # 核心功能模块
    ├── __init__.py      # 核心包初始化
    ├── auth.py          # 认证模块
    ├── browser.py       # 浏览器管理
    ├── search.py        # 搜索功能
    └── utils.py         # 工具函数

tests/                   # 测试目录
├── conftest.py          # 测试配置和固件
├── test_async_fixed.py  # 修复的异步测试
├── test_async_with_playwright.py # 使用Playwright的异步测试
├── test_auth.py         # 认证测试
├── test_auth_extended.py# 扩展认证测试
├── test_browser.py      # 浏览器测试
├── test_config.py       # 配置测试
├── test_main.py         # 主模块测试
├── test_mcp_server.py   # MCP服务器测试
├── test_playwright_browser.py # Playwright浏览器测试
├── test_search.py       # 搜索测试
├── test_search_extended.py # 扩展搜索测试
├── test_server.py       # 服务器测试
├── test_utils.py        # 工具函数测试
└── test_with_playwright_fixtures.py # 使用Playwright固件的测试

# 根目录关键文件
server.py                # 独立MCP服务器实现，包含所有必要功能
mcp_server.py            # MCP服务器启动脚本，处理依赖和环境
start_server.sh          # 便捷的服务器启动脚本，自动设置环境和启动服务器
```

### 关键文件说明

#### server.py

独立的MCP服务器实现，包含所有必要的功能，可以直接与Claude Desktop集成。它具有以下特点：

- 自动安装依赖
- 内置所有功能（浏览器管理、认证、搜索等）
- 详细的调试日志
- 全面的错误处理
- 禁用截图功能（在Claude Desktop环境中）

#### woodgate/server.py

模块化的MCP服务器实现，是标准包结构的一部分。与根目录的server.py相比，它更加模块化，依赖于woodgate包中的其他模块。在通过`python -m woodgate`运行时使用。

#### mcp_server.py

MCP服务器启动脚本，在不同环境下确保服务器能够正确启动：

- 自动检查并安装必要的依赖
- 智能模块导入（支持包安装和直接脚本运行两种模式）
- 自动路径管理
- 全面的错误处理
- 详细的日志记录

使用方法：

```bash
# 直接运行
python mcp_server.py

# 或者设置环境变量后运行
export REDHAT_USERNAME="your_username"
export REDHAT_PASSWORD="your_password"
python mcp_server.py
```

#### start_server.sh

便捷的服务器启动脚本，提供一键启动功能：

- 自动设置环境变量（包括凭据和日志级别）
- 自动激活Python虚拟环境
- 创建必要的日志和截图目录
- 使用正确的参数启动服务器
- 将日志输出重定向到文件

使用方法：

```bash
# 确保脚本有执行权限
chmod +x start_server.sh

# 运行脚本
./start_server.sh
```

## 许可证

本项目采用MIT许可证 - 详见LICENSE文件。
