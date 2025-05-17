# Woodgate 技术设计文档

## 项目概述

Woodgate 是一个基于 Model Context Protocol (MCP) 的服务器，专为自动化搜索和从 Red Hat 客户门户提取数据而设计。该项目利用 Playwright 进行浏览器自动化，实现了高效的网页交互和数据提取功能。

本文档详细描述了 Woodgate 的技术架构、核心模块、实现细节和工作流程，旨在为开发人员提供全面的技术参考。

## 系统架构

Woodgate 采用模块化架构，主要由以下几个部分组成：

1. **MCP 服务器层**：实现 Model Context Protocol，提供与 Claude Desktop 等 AI 助手的集成接口
2. **核心功能层**：包含浏览器自动化、认证、搜索和数据提取等核心功能
3. **配置管理层**：处理系统配置、环境变量和用户凭据
4. **工具和辅助层**：提供日志记录、错误处理和其他辅助功能

### 架构图

```
+---------------------+     +----------------------+
| Claude Desktop      |     | 独立运行模式          |
| (MCP 客户端)        |     | (命令行/API)         |
+----------+----------+     +-----------+----------+
           |                            |
           v                            v
+----------+----------------------------+----------+
|                  MCP 服务器层                    |
|  (server.py / woodgate/server.py)               |
+----------------------------------------------------+
|                  核心功能层                        |
|  +----------------+  +----------------+           |
|  | 浏览器管理      |  | 认证管理        |           |
|  | (browser.py)   |  | (auth.py)      |           |
|  +----------------+  +----------------+           |
|  +----------------+  +----------------+           |
|  | 搜索功能        |  | 数据提取        |           |
|  | (search.py)    |  | (search.py)    |           |
|  +----------------+  +----------------+           |
+----------------------------------------------------+
|                  配置管理层                        |
|  (config.py)                                      |
+----------------------------------------------------+
|                  工具和辅助层                      |
|  (utils.py)                                       |
+----------------------------------------------------+
```

## 核心模块详解

### MCP 服务器实现

Woodgate 提供了两种 MCP 服务器实现：

1. **独立服务器** (`server.py`)：
   - 包含所有必要功能的单文件实现
   - 自动安装依赖
   - 内置凭据管理
   - 适合与 Claude Desktop 直接集成

2. **模块化服务器** (`woodgate/server.py`)：
   - 标准包结构的一部分
   - 依赖于 woodgate 包中的其他模块
   - 更适合通过 `python -m woodgate` 运行
   - 提供更好的代码组织和可维护性

两种实现都使用 `FastMCP` 类创建 MCP 服务器，并注册工具函数供 AI 助手调用。

### 浏览器自动化 (browser.py)

浏览器模块负责初始化和管理 Playwright 浏览器实例，主要功能包括：

- 初始化 Chromium 浏览器（`initialize_browser`）
- 配置浏览器选项和性能优化
- 处理 Cookie 横幅和通知（`setup_cookie_banner_handlers`）
- 管理浏览器生命周期（`close_browser`）

该模块使用 Playwright 的异步 API，提供高效的浏览器自动化能力。

### 认证管理 (auth.py)

认证模块处理 Red Hat 客户门户的登录和会话管理，主要功能包括：

- 登录到 Red Hat 客户门户（`login_to_redhat_portal`）
- 检查登录状态（`check_login_status`）
- 处理登录错误和重试机制
- 会话维护和 Cookie 管理

该模块实现了稳健的登录流程，能够处理各种登录场景和错误情况。

### 搜索和数据提取 (search.py)

搜索模块实现了 Red Hat 客户门户的搜索和数据提取功能，主要包括：

- 执行搜索查询（`perform_search`）
- 构建搜索 URL（`build_search_url`）
- 提取搜索结果（`extract_search_results`）
- 获取文档内容（`get_document_content`）
- 获取产品警报（`get_product_alerts`）

该模块能够处理复杂的搜索参数，并从搜索结果中提取结构化数据。

### 配置管理 (config.py)

配置模块负责管理系统配置和用户凭据，主要功能包括：

- 获取系统配置（`get_config`）
- 管理用户凭据（`get_credentials`）
- 获取可用产品列表（`get_available_products`）
- 获取文档类型（`get_document_types`）

该模块支持从环境变量和默认值获取配置，提供灵活的配置管理能力。

### 工具和辅助功能 (utils.py)

工具模块提供各种辅助功能，包括：

- 日志设置和管理（`setup_logging`）
- 步骤日志记录（`log_step`）
- Cookie 处理（`handle_cookie_popup`）
- 错误处理和重试机制

## 工作流程

### MCP 服务器启动流程

1. 用户通过 `start_server.sh` 或直接命令启动服务器
2. 系统检查并安装必要的依赖
3. 初始化日志系统
4. 创建 MCP 服务器实例
5. 注册工具函数和资源
6. 启动服务器，等待客户端连接

### 搜索执行流程

1. 客户端（如 Claude Desktop）发送搜索请求
2. MCP 服务器接收请求并调用 `search` 工具函数
3. 系统初始化浏览器并登录到 Red Hat 客户门户
4. 构建搜索 URL 并执行搜索
5. 提取搜索结果并返回给客户端

### 文档获取流程

1. 客户端请求特定文档内容
2. MCP 服务器调用 `get_document` 工具函数
3. 系统访问文档 URL 并提取内容
4. 处理和格式化文档内容
5. 返回结构化的文档数据给客户端

## 技术栈

Woodgate 使用以下主要技术和库：

- **Python 3.10+**：核心编程语言
- **Playwright**：浏览器自动化框架，替代 Selenium
- **MCP (Model Context Protocol)**：AI 助手集成协议
- **FastMCP**：MCP 服务器实现库
- **pytest**：测试框架
- **asyncio**：异步编程支持
- **httpx**：现代 HTTP 客户端

## 测试策略

Woodgate 采用多层次的测试策略：

1. **单元测试**：测试各个模块的独立功能
2. **集成测试**：测试模块间的交互
3. **端到端测试**：模拟真实用户场景的完整测试

测试使用 pytest 框架，并利用 pytest-playwright 插件进行浏览器自动化测试。测试覆盖率目标为 70% 以上。

## 部署和集成

### 与 Claude Desktop 集成

Woodgate 可以作为 MCP 服务器与 Claude Desktop 集成：

```bash
.venv/bin/mcp install server.py:mcp --name "Red Hat KB Search"
```

集成后，Claude Desktop 可以直接调用 Woodgate 提供的工具函数，实现无缝的 Red Hat 知识库搜索体验。

### 独立部署

Woodgate 也可以作为独立服务器部署：

```bash
uv run python -m woodgate --host 0.0.0.0 --port 8080 --log-level DEBUG
```

独立部署模式适合通过 API 或命令行方式使用 Woodgate 的功能。

## 安全考虑

- 用户凭据存储在服务器端，不需要在客户端配置
- 支持通过环境变量设置凭据，避免硬编码
- 确保凭据信息不被提交到公共代码仓库
- 使用 HTTPS 进行安全通信

## 未来扩展

- 支持更多 Red Hat 产品和服务
- 增强搜索功能和结果过滤
- 改进文档内容提取和格式化
- 添加缓存机制提高性能
- 支持更多浏览器和平台
