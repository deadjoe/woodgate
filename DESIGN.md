# Woodgate 设计文档

## 1. 项目概述

Woodgate 是一个基于 Model Context Protocol (MCP) 的服务器，用于自动化搜索和从 Red Hat 客户门户提取数据。该项目允许用户通过 Claude 等大型语言模型（LLM）直接搜索 Red Hat 知识库，获取技术文档、解决方案和警报信息。

### 1.1 核心功能

- 自动登录到 Red Hat 客户门户
- 执行关键词搜索，支持产品和文档类型过滤
- 提取搜索结果，包括标题、URL、摘要、文档类型和更新日期
- 获取特定产品的警报信息
- 获取文档的详细内容
- 与 Claude Desktop 等 MCP 客户端集成

### 1.2 技术栈

- **Python 3.10+**: 主要编程语言
- **Selenium**: 用于浏览器自动化和网页交互
- **Chrome/Chromium**: 浏览器引擎
- **MCP SDK**: 用于实现 Model Context Protocol 服务器
- **asyncio**: 用于异步编程
- **pytest**: 用于单元测试
- **uv**: Python 包管理工具

## 2. 系统架构

Woodgate 采用模块化架构设计，主要分为以下几个部分：

### 2.1 整体架构图

```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|  MCP 客户端      |     |  MCP 服务器      |     |  Red Hat 客户门户 |
|  (Claude Desktop)|<--->|  (Woodgate)     |<--->|  (Web 服务)      |
|                  |     |                  |     |                  |
+------------------+     +------------------+     +------------------+
                               |
                               |
                         +-----v------+
                         |            |
                         | 浏览器引擎  |
                         | (Chrome)   |
                         |            |
                         +------------+
```

### 2.2 模块结构

```
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
```

### 2.3 独立服务器文件

除了标准的模块化结构外，项目还包含两个独立的服务器文件，用于直接与 Claude Desktop 集成：

- `server.py`: 独立的 MCP 服务器实现，包含所有必要的功能
- `mcp_server.py`: 辅助脚本，用于启动 MCP 服务器

## 3. 核心模块详解

### 3.1 配置模块 (`config.py`)

配置模块负责管理应用程序配置和环境变量，提供以下功能：

- **获取凭据**: 从环境变量中获取 Red Hat 客户门户的登录凭据
- **获取配置**: 从环境变量和默认值构建配置字典
- **获取可用产品列表**: 提供 Red Hat 产品列表
- **获取文档类型列表**: 提供可用的文档类型

配置通过环境变量进行管理，支持以下配置项：

```python
config = {
    # 浏览器配置
    "headless": os.environ.get("WOODGATE_HEADLESS", "true").lower() == "true",
    "browser_timeout": int(os.environ.get("WOODGATE_BROWSER_TIMEOUT", "20")),
    # 搜索配置
    "default_rows": int(os.environ.get("WOODGATE_DEFAULT_ROWS", "20")),
    "default_sort": os.environ.get("WOODGATE_DEFAULT_SORT", "relevant"),
    # 服务器配置
    "host": os.environ.get("WOODGATE_HOST", "127.0.0.1"),
    "port": int(os.environ.get("WOODGATE_PORT", "8000")),
    # 日志配置
    "log_level": os.environ.get("WOODGATE_LOG_LEVEL", "INFO"),
    # 重试配置
    "max_retries": int(os.environ.get("WOODGATE_MAX_RETRIES", "3")),
    "retry_delay": int(os.environ.get("WOODGATE_RETRY_DELAY", "3")),
}
```

### 3.2 浏览器管理模块 (`core/browser.py`)

浏览器管理模块负责初始化和管理 Chrome 浏览器实例，提供以下功能：

- **初始化浏览器**: 配置并启动 Chrome 浏览器，设置无头模式、窗口大小等选项
- **优化浏览器性能**: 禁用扩展、GPU 加速、图片加载等，提高性能
- **设置超时时间**: 配置页面加载和脚本执行的超时时间

浏览器配置示例：

```python
chrome_options = Options()
chrome_options.add_argument("--headless")  # 启用无头模式
chrome_options.add_argument("--no-sandbox")  # 禁用沙箱
chrome_options.add_argument("--disable-dev-shm-usage")  # 解决低内存环境中的崩溃问题
chrome_options.add_argument("--window-size=1920,1080")  # 设置窗口大小
chrome_options.add_argument("--disable-extensions")  # 禁用扩展
chrome_options.add_argument("--disable-gpu")  # 禁用GPU加速
chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # 禁用图片加载
chrome_options.page_load_strategy = "eager"  # 使用eager加载策略
```

### 3.3 认证模块 (`core/auth.py`)

认证模块处理 Red Hat 客户门户的登录和会话管理，提供以下功能：

- **登录到 Red Hat 客户门户**: 自动填写用户名和密码，处理登录流程
- **检查登录状态**: 验证当前会话是否已登录
- **处理登录失败**: 识别和处理各种登录失败情况，包括凭据错误、网络问题等
- **重试机制**: 实现登录重试，处理临时性错误

登录流程包括以下步骤：

1. 访问登录页面
2. 处理 Cookie 弹窗
3. 输入用户名
4. 点击下一步
5. 输入密码
6. 点击登录按钮
7. 等待登录完成
8. 验证登录状态

### 3.4 搜索模块 (`core/search.py`)

搜索模块处理 Red Hat 客户门户的搜索功能，提供以下功能：

- **执行搜索**: 根据关键词、产品和文档类型执行搜索
- **构建搜索 URL**: 根据搜索参数构建 URL
- **提取搜索结果**: 从搜索结果页面提取结果
- **获取产品警报**: 获取特定产品的警报信息
- **获取文档内容**: 获取特定文档的详细内容

搜索结果包含以下信息：

```python
{
    "title": "文档标题",
    "url": "文档URL",
    "summary": "文档摘要",
    "doc_type": "文档类型",
    "last_updated": "最后更新日期"
}
```

### 3.5 工具函数模块 (`core/utils.py`)

工具函数模块提供各种辅助功能，包括：

- **设置日志**: 配置日志格式和级别
- **打印日志**: 打印带时间戳的日志信息
- **打印 Cookie**: 打印当前浏览器中的所有 Cookie 信息，用于诊断
- **处理 Cookie 弹窗**: 自动处理网页上出现的 cookie 或隐私弹窗
- **格式化警报**: 将警报数据格式化为可读字符串

Cookie 弹窗处理使用多种选择器策略，确保能够处理不同类型的弹窗：

```python
popup_selectors = [
    "#onetrust-banner-sdk",  # 最常见的
    ".pf-c-modal-box",  # Red Hat特有的
    "[role='dialog'][aria-modal='true']",  # 通用备选
]

close_buttons = [
    "button.pf-c-button[aria-label='Close']",
    "#onetrust-accept-btn-handler",
    "button.pf-c-button.pf-m-primary",
    ".close-button",
    "button[aria-label='Close']",
]
```

## 4. MCP 服务器实现

### 4.1 MCP 服务器模块 (`server.py`)

MCP 服务器模块实现 Model Context Protocol 服务器，提供以下功能：

- **创建 MCP 服务器**: 使用 FastMCP 创建服务器实例
- **定义工具函数**: 实现搜索、获取警报和获取文档内容的工具函数
- **定义资源**: 提供可用产品列表和文档类型列表
- **定义提示**: 提供搜索帮助和示例

MCP 服务器使用 FastMCP 创建：

```python
mcp = FastMCP("Woodgate", description="Red Hat客户门户搜索工具")
```

### 4.2 工具函数

MCP 服务器定义了以下工具函数：

#### 4.2.1 搜索工具

```python
@mcp.tool()
async def search(
    query: str,
    products: Optional[List[str]] = None,
    doc_types: Optional[List[str]] = None,
    page: int = 1,
    rows: int = 20,
    sort_by: str = "relevant",
) -> List[Dict[str, Any]]:
    """在Red Hat客户门户中执行搜索"""
    # 实现...
```

#### 4.2.2 获取警报工具

```python
@mcp.tool()
async def get_alerts(product: str) -> List[Dict[str, Any]]:
    """获取特定产品的警报信息"""
    # 实现...
```

#### 4.2.3 获取文档工具

```python
@mcp.tool()
async def get_document(document_url: str) -> Dict[str, Any]:
    """获取特定文档的详细内容"""
    # 实现...
```

### 4.3 资源

MCP 服务器定义了以下资源：

#### 4.3.1 产品列表资源

```python
@mcp.resource("config://products")
def available_products() -> List[str]:
    """获取可用的产品列表"""
    return get_available_products()
```

#### 4.3.2 文档类型资源

```python
@mcp.resource("config://doc-types")
def document_types() -> List[str]:
    """获取可用的文档类型"""
    return get_document_types()
```

#### 4.3.3 搜索参数资源

```python
@mcp.resource("config://search-params")
def search_params() -> Dict[str, Any]:
    """获取搜索参数配置"""
    return {
        "sort_options": [
            {"value": "relevant", "label": "相关性"},
            {"value": "lastModifiedDate desc", "label": "最新更新"},
            # ...
        ],
        "default_rows": 20,
        "max_rows": 100,
        "products": get_available_products(),
        "doc_types": get_document_types(),
    }
```

### 4.4 提示

MCP 服务器定义了以下提示：

#### 4.4.1 搜索帮助提示

```python
@mcp.prompt()
def search_help() -> str:
    """提供搜索帮助信息"""
    return """
    # Red Hat 客户门户搜索帮助
    
    您可以使用以下参数进行搜索：
    
    - **query**: 搜索关键词，例如 "memory leak"
    - **products**: 要搜索的产品列表，例如 ["Red Hat Enterprise Linux", "Red Hat OpenShift"]
    - **doc_types**: 文档类型列表，例如 ["Solution", "Article"]
    - **page**: 页码，默认为1
    - **rows**: 每页结果数，默认为20
    - **sort_by**: 排序方式，可选值: "relevant", "lastModifiedDate desc", "lastModifiedDate asc"
    
    示例：search(query="kubernetes troubleshooting", products=["Red Hat OpenShift Container Platform"], doc_types=["Solution"])
    """
```

#### 4.4.2 搜索示例提示

```python
@mcp.prompt()
def search_example() -> str:
    """提供搜索示例"""
    return """
    # Red Hat 客户门户搜索示例
    
    ## 基本搜索
    ```python
    search(query="memory leak")
    ```
    
    ## 带产品过滤的搜索
    ```python
    search(
        query="kubernetes pod crash",
        products=["Red Hat OpenShift Container Platform"]
    )
    ```
    
    # ...更多示例...
    """
```

### 4.5 独立服务器文件

#### 4.5.1 `server.py`

`server.py` 是一个独立的 MCP 服务器实现，包含所有必要的功能，可以直接与 Claude Desktop 集成。它具有以下特点：

- **自动安装依赖**: 检查并安装必要的依赖包
- **内置所有功能**: 包含浏览器管理、认证、搜索等所有功能
- **详细日志**: 提供详细的调试日志
- **错误处理**: 实现全面的错误处理和异常捕获

#### 4.5.2 `mcp_server.py`

`mcp_server.py` 是一个辅助脚本，用于启动 MCP 服务器，具有以下特点：

- **依赖检查**: 检查并安装必要的依赖
- **模块导入**: 尝试导入 woodgate.server 模块，如果失败则尝试直接导入 server.py
- **错误处理**: 处理导入和启动过程中的错误

## 5. 日志系统

### 5.1 日志配置

Woodgate 使用 Python 的 logging 模块进行日志记录，支持多种日志级别：

- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误信息

日志配置示例：

```python
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
```

### 5.2 日志记录策略

Woodgate 采用以下日志记录策略：

- **步骤日志**: 记录每个操作步骤，便于跟踪执行流程
- **错误日志**: 详细记录错误信息和堆栈跟踪
- **诊断日志**: 记录 Cookie 和会话信息，用于诊断认证问题
- **性能日志**: 记录操作耗时，用于性能优化

### 5.3 调试日志

在调试模式下，Woodgate 提供更详细的日志信息：

- **函数参数**: 记录函数调用的参数值
- **中间结果**: 记录函数执行过程中的中间结果
- **异常堆栈**: 记录完整的异常堆栈跟踪
- **浏览器状态**: 记录浏览器的状态和操作

## 6. 错误处理

### 6.1 异常捕获

Woodgate 实现了全面的异常捕获机制，处理以下类型的异常：

- **网络异常**: 处理网络连接问题
- **认证异常**: 处理登录失败和会话过期
- **浏览器异常**: 处理浏览器操作和元素查找失败
- **超时异常**: 处理操作超时
- **导入异常**: 处理模块导入失败

### 6.2 重试机制

对于可恢复的错误，Woodgate 实现了重试机制：

- **登录重试**: 在登录失败时重试，最多尝试 3 次
- **搜索重试**: 在搜索失败时重试，处理临时性错误
- **元素查找重试**: 在元素查找失败时重试，处理页面加载延迟

### 6.3 错误报告

Woodgate 提供详细的错误报告：

- **错误消息**: 返回人类可读的错误消息
- **错误代码**: 返回错误代码，便于诊断
- **错误详情**: 返回详细的错误信息，包括异常类型和堆栈跟踪

## 7. 测试框架

### 7.1 测试结构

Woodgate 使用 pytest 进行单元测试，测试结构如下：

```
tests/
├── test_auth.py         # 认证测试
├── test_auth_extended.py# 扩展认证测试
├── test_browser.py      # 浏览器测试
├── test_config.py       # 配置测试
├── test_main.py         # 主模块测试
├── test_search.py       # 搜索测试
├── test_search_extended.py # 扩展搜索测试
├── test_server.py       # 服务器测试
└── test_utils.py        # 工具函数测试
```

### 7.2 测试类型

Woodgate 实现了以下类型的测试：

- **单元测试**: 测试单个函数和方法
- **集成测试**: 测试多个组件的交互
- **模拟测试**: 使用 unittest.mock 模拟外部依赖
- **异步测试**: 使用 pytest.mark.asyncio 测试异步函数

### 7.3 测试覆盖率

Woodgate 的测试覆盖率目标为 70%，当前覆盖率为 79%。测试覆盖以下方面：

- **功能覆盖**: 测试所有公共函数和方法
- **分支覆盖**: 测试条件分支
- **异常覆盖**: 测试异常处理路径
- **参数覆盖**: 测试不同参数组合

## 8. 与 Claude Desktop 集成

### 8.1 安装到 Claude Desktop

Woodgate 可以安装到 Claude Desktop，使用以下命令：

```bash
# 设置环境变量
export REDHAT_USERNAME="your_username"
export REDHAT_PASSWORD="your_password"

# 安装MCP服务器到Claude Desktop
/path/to/venv/bin/mcp install server.py:mcp --name "Red Hat KB Search"
```

### 8.2 开发服务器

可以启动带有调试日志的开发服务器：

```bash
export REDHAT_USERNAME="your_username"
export REDHAT_PASSWORD="your_password"
export PYTHONUNBUFFERED=1
export LOGLEVEL=DEBUG
.venv/bin/mcp dev server.py:mcp
```

### 8.3 使用示例

在 Claude Desktop 中，可以使用以下命令：

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

# 获取产品警报
get_alerts(product="Red Hat Enterprise Linux")

# 获取文档内容
get_document(document_url="https://access.redhat.com/solutions/12345")
```

## 9. 性能优化

### 9.1 浏览器优化

Woodgate 实现了以下浏览器优化：

- **无头模式**: 使用无头模式运行浏览器，减少资源占用
- **禁用图片**: 禁用图片加载，加快页面处理速度
- **禁用扩展**: 禁用浏览器扩展，减少资源占用
- **页面加载策略**: 使用 eager 加载策略，DOM 就绪后立即返回

### 9.2 并发优化

Woodgate 使用 asyncio 实现异步编程，提高并发性能：

- **异步函数**: 使用 async/await 实现异步函数
- **事件循环**: 在事件循环中执行 I/O 密集型操作
- **并发请求**: 支持并发执行多个请求

### 9.3 缓存优化

Woodgate 实现了以下缓存优化：

- **会话缓存**: 重用浏览器会话，减少登录次数
- **WebDriver 缓存**: 使用 ChromeDriverManager 缓存 WebDriver，减少下载次数

## 10. 安全考虑

### 10.1 凭据管理

Woodgate 使用环境变量存储凭据，避免硬编码：

```python
username = os.environ.get("REDHAT_USERNAME")
password = os.environ.get("REDHAT_PASSWORD")
```

### 10.2 会话管理

Woodgate 实现了安全的会话管理：

- **会话超时**: 处理会话超时和过期
- **会话验证**: 验证会话状态，确保已登录
- **会话清理**: 在操作完成后关闭浏览器，清理会话

### 10.3 错误处理

Woodgate 实现了安全的错误处理：

- **敏感信息过滤**: 在日志和错误消息中过滤敏感信息
- **异常捕获**: 捕获所有异常，避免泄露堆栈信息
- **安全默认值**: 使用安全的默认值，避免暴露敏感信息

## 11. 部署和运行

### 11.1 环境要求

Woodgate 需要以下环境：

- **Python 3.10+**: 主要编程语言
- **Chrome/Chromium**: 浏览器引擎
- **必要的 Python 包**: 见 `pyproject.toml`
- **MCP SDK 1.6+**: 用于实现 MCP 服务器

### 11.2 安装步骤

1. 克隆仓库:

   ```bash
   git clone https://github.com/deadjoe/woodgate.git
   cd woodgate
   ```

2. 使用 uv 创建虚拟环境并安装依赖:

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

### 11.3 运行方式

#### 11.3.1 作为 MCP 服务器运行

```bash
uv run python -m woodgate
```

或者指定主机、端口和日志级别:

```bash
uv run python -m woodgate --host 0.0.0.0 --port 8080 --log-level DEBUG
```

#### 11.3.2 与 Claude Desktop 集成

```bash
.venv/bin/mcp install server.py:mcp --name "Red Hat KB Search"
```

## 12. 调试和故障排除

### 12.1 常见问题

#### 12.1.1 登录失败

可能的原因：
- 凭据错误
- 网络问题
- 页面结构变化
- Cookie 弹窗干扰

解决方法：
- 检查环境变量
- 检查网络连接
- 更新选择器
- 更新 Cookie 弹窗处理逻辑

#### 12.1.2 搜索结果为空

可能的原因：
- 搜索关键词不匹配
- 产品或文档类型过滤过于严格
- 页面结构变化
- 结果提取逻辑错误

解决方法：
- 使用更通用的关键词
- 减少过滤条件
- 更新选择器
- 更新结果提取逻辑

### 12.2 调试技巧

#### 12.2.1 启用调试日志

```bash
export LOGLEVEL=DEBUG
.venv/bin/mcp dev server.py:mcp
```

#### 12.2.2 检查浏览器状态

使用 `print_cookies` 函数检查 Cookie 状态：

```python
print_cookies(driver, "登录后")
```

#### 12.2.3 使用开发服务器

使用 MCP 开发服务器查看实时日志：

```bash
.venv/bin/mcp dev server.py:mcp
```

## 13. 未来改进

### 13.1 功能改进

- **支持更多搜索选项**: 添加更多搜索过滤器和排序选项
- **支持更多文档类型**: 添加对更多文档类型的支持
- **支持更多产品**: 添加对更多 Red Hat 产品的支持
- **支持更多语言**: 添加对多语言的支持

### 13.2 技术改进

- **使用 Playwright**: 替换 Selenium，提高浏览器自动化的稳定性和性能
- **实现缓存机制**: 缓存搜索结果，减少重复请求
- **实现并发搜索**: 支持并发执行多个搜索请求
- **实现分布式部署**: 支持分布式部署，提高可扩展性

### 13.3 用户体验改进

- **提供更多示例**: 添加更多搜索示例，便于用户学习
- **提供更多提示**: 添加更多提示，帮助用户使用
- **提供更多反馈**: 添加更多反馈信息，帮助用户理解结果
- **提供更多可视化**: 添加结果可视化，提高用户体验

## 14. 总结

Woodgate 是一个功能强大的 MCP 服务器，用于自动化搜索和从 Red Hat 客户门户提取数据。它采用模块化架构设计，实现了浏览器自动化、认证、搜索和结果提取等功能，并与 Claude Desktop 等 MCP 客户端集成。

Woodgate 的主要优势包括：

- **模块化设计**: 便于维护和扩展
- **全面的错误处理**: 提高稳定性和可靠性
- **详细的日志记录**: 便于调试和故障排除
- **高测试覆盖率**: 确保代码质量和功能正确性
- **与 MCP 集成**: 便于与 Claude 等 LLM 集成

通过 Woodgate，用户可以直接在 Claude Desktop 中搜索 Red Hat 知识库，获取技术文档、解决方案和警报信息，提高工作效率和问题解决速度。
