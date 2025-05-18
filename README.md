<p align="center">
  <img src="woodgate.png" alt="Woodgate Logo" width="256">
</p>

# Woodgate

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Tests](https://github.com/deadjoe/woodgate/actions/workflows/python-tests.yml/badge.svg)](https://github.com/deadjoe/woodgate/actions/workflows/python-tests.yml)
[![Python Version](https://img.shields.io/badge/python-3.10--3.12-blue)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/Playwright-1.44%2B-green)](https://playwright.dev/)
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

- Python 3.10-3.12
- 必要的Python包（见`requirements.txt`）
- MCP SDK 1.6+
- Playwright 1.44+（会自动安装浏览器）

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
   export PYTHONUNBUFFERED=1  # 禁用Python输出缓冲
   export LOGLEVEL=DEBUG      # 设置日志级别为DEBUG
   export PYTHONTRACEMALLOC=1 # 启用内存分配跟踪
   export PYTHONASYNCIODEBUG=1 # 启用asyncio调试

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
- 启动服务器（主机：0.0.0.0，端口：8080，日志级别：DEBUG）

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

#### 启动MCP服务器

首先，需要启动MCP服务器：

```bash
# 设置Red Hat客户门户凭据
export REDHAT_USERNAME="your_username"
export REDHAT_PASSWORD="your_password"

# 启动MCP服务器
uv run python -m woodgate --host 0.0.0.0 --port 8080 --log-level DEBUG
```

服务器将在端口8080上启动，并使用SSE传输协议。

#### 安装到Claude Desktop

在Claude Desktop中安装MCP服务器：

1. 打开Claude Desktop
2. 点击菜单栏中的Claude图标
3. 选择"Settings..."
4. 在左侧边栏选择"Developer"
5. 点击"Edit Config"

这将打开配置文件（通常位于`~/Library/Application Support/Claude/claude_desktop_config.json`）。将以下内容添加到配置文件中：

```json
{
  "globalShortcut": "",
  "mcpServers": {
    "Red Hat KB Search": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "mcp[cli]",
        "mcp",
        "run",
        "/path/to/your/project/server.py:mcp"
      ],
      "env": {
        "REDHAT_USERNAME": "your_username",
        "REDHAT_PASSWORD": "your_password"
      }
    }
  }
}
```

请确保将`/path/to/your/project/`替换为您项目的实际路径。

保存配置文件后，重启Claude Desktop。现在，您应该能够在Claude Desktop中使用Red Hat KB Search工具了。

#### 注意事项

- MCP服务器使用默认端口8000，无需在Claude Desktop配置中指定端口
- 如果您在启动服务器时指定了不同的端口（如8080），请确保服务器正在运行
- 凭据可以通过环境变量传递，也可以在配置文件的`env`部分设置
- 如果您使用`redhat_credentials.txt`文件存储凭据，服务器会自动读取该文件
- 确保凭据信息不被提交到公共代码仓库

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

- 系统支持多种凭据管理方式：
  1. 环境变量：`REDHAT_USERNAME` 和 `REDHAT_PASSWORD`
  2. 配置文件：`redhat_credentials.txt`（包含两行，第一行是用户名，第二行是密码）
  3. Claude Desktop配置：在`claude_desktop_config.json`的`env`部分设置
- 凭据优先级：环境变量 > 配置文件 > 默认值
- 在生产环境中，建议使用环境变量或配置文件管理凭据
- 确保凭据信息不被提交到公共代码仓库（已在`.gitignore`中排除）
- 凭据存储在服务器端，可以通过Claude Desktop配置传递

## 开发

### 持续集成

项目使用GitHub Actions进行持续集成，配置文件位于`.github/workflows/python-tests.yml`。每次推送到main分支或创建Pull Request时，会自动运行测试并生成覆盖率报告。

CI流程包括：

- 在多个Python版本（3.10、3.11、3.12）上运行测试
- 安装依赖和Playwright浏览器
- 运行所有测试并生成覆盖率报告
- 上传覆盖率报告到Codecov

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
# 使用black格式化代码
uv run black woodgate tests

# 使用isort排序导入
uv run isort woodgate tests

# 使用flake8检查代码质量
uv run flake8 woodgate tests

# 使用ruff进行快速代码检查和修复
uv run ruff check woodgate tests
uv run ruff check --fix woodgate tests
```

### 测试覆盖率

项目的测试覆盖率目标为70%以上。可以使用以下命令查看当前的测试覆盖率：

```bash
uv run pytest --cov=woodgate --cov-report=term-missing
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

## 文档

- **README.md**: 项目概述、安装和使用说明
- **DESIGN.md**: 详细的技术设计文档，包括架构、模块和工作流程
- **playwright_guide.md**: Playwright使用指南，包括API参考和最佳实践

## 版本控制与.gitignore

项目使用Git进行版本控制，并配置了.gitignore文件以排除以下内容：

- Python缓存文件（`__pycache__/`, `*.py[cod]`）
- 虚拟环境目录（`.venv/`, `env/`）
- 构建和分发文件（`build/`, `dist/`, `*.egg-info/`）
- 测试覆盖率报告（`.coverage`, `coverage.xml`）
- 敏感文件（`*credentials*.txt`, `*password*.txt`, `*secret*.txt`）
- 系统特定文件（`.DS_Store`）
- 临时文件和备份（`*.bak`, `*.orig`）

提交代码前请确保不包含敏感信息和不必要的临时文件。

## 许可证

本项目采用MIT许可证 - 详见LICENSE文件。
