# Woodgate 项目测试方案文档

本文档详细描述了 Woodgate 项目中使用的所有测试技术、方法和方案，旨在提供一个全面的测试参考指南，便于团队成员和 AI 协作者快速了解项目的测试体系。

## 目录

- [1. 测试框架与工具](#1-测试框架与工具)
- [2. 测试类型与方法](#2-测试类型与方法)
- [3. 测试配置与设置](#3-测试配置与设置)
- [4. 自动化测试流程](#4-自动化测试流程)
- [5. 代码质量检查](#5-代码质量检查)
- [6. 持续集成与部署](#6-持续集成与部署)
- [7. 文档生成](#7-文档生成)
- [8. 测试覆盖率分析](#8-测试覆盖率分析)
- [9. 测试优化建议](#9-测试优化建议)

## 1. 测试框架与工具

### 1.1 核心测试框架

- **pytest (8.3.5)**: 主要测试框架，用于运行所有单元测试和集成测试
- **pytest-asyncio (0.26.0)**: 支持异步测试的 pytest 插件
- **pytest-playwright (0.7.0)**: 集成 Playwright 进行浏览器自动化测试的 pytest 插件
- **pytest-cov (6.1.1)**: 用于生成测试覆盖率报告的 pytest 插件

### 1.2 浏览器自动化工具

- **Playwright (1.52.0)**: 用于浏览器自动化测试，支持多种浏览器
- **Selenium (4.31.0)**: 作为备选的浏览器自动化工具

### 1.3 代码质量工具

- **Black (25.1.0)**: Python 代码格式化工具
- **isort (6.0.1)**: 导入语句排序工具
- **flake8 (7.2.0)**: Python 代码风格检查工具
- **pylint (3.3.7)**: 全面的 Python 代码静态分析工具
- **ruff (0.11.8)**: 快速的 Python linter，用 Rust 编写
- **mypy (1.9.0)**: Python 静态类型检查工具

### 1.4 工作流自动化工具

- **pre-commit (3.5.0)**: Git 预提交钩子管理工具
- **uv**: Python 包管理和虚拟环境工具

## 2. 测试类型与方法

### 2.1 单元测试

项目中的单元测试主要集中在 `tests/` 目录下，按模块划分为不同的测试文件：

- **`test_async_helpers.py`**: 测试异步辅助函数
- **`test_auth.py`**: 测试认证相关功能
- **`test_browser.py`**: 测试浏览器操作功能
- **`test_config.py`**: 测试配置管理功能
- **`test_main.py`**: 测试主程序入口
- **`test_mcp_server.py`**: 测试 MCP 服务器功能
- **`test_search.py`**: 测试搜索功能
- **`test_server.py`**: 测试服务器功能
- **`test_utils.py`**: 测试工具类函数

单元测试采用了以下测试方法：
- 正常路径测试（Happy Path Testing）
- 异常路径测试（Error Path Testing）
- 边界条件测试（Boundary Testing）
- 模拟对象测试（Mock Object Testing）

### 2.2 集成测试

项目使用 pytest 的标记系统来区分不同类型的测试：

```python
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "e2e: marks tests as end-to-end tests",
]
```

集成测试主要关注：
- 组件之间的交互
- API 调用的完整流程
- 数据流在多个组件间的传递

### 2.3 浏览器自动化测试

项目使用 Playwright 进行浏览器自动化测试，主要测试：
- 页面导航和交互
- 表单提交
- 元素可见性和状态
- Cookie 处理
- 登录流程

浏览器测试配置在 `conftest.py` 中定义了多个固件（fixtures）：
- `browser_type_launch_args`: 浏览器启动参数
- `browser_context_args`: 浏览器上下文参数
- `page`: 页面固件
- `async_browser`: 异步浏览器实例
- `async_context`: 异步浏览器上下文
- `async_page`: 异步页面实例
- `authenticated_page`: 已登录的页面实例

### 2.4 异步测试

项目大量使用异步编程，因此配置了专门的异步测试支持：

```ini
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

异步测试主要使用 `pytest-asyncio` 插件，并在 `conftest.py` 中配置了事件循环策略：

```python
@pytest.fixture(scope="session")
def event_loop_policy():
    """设置事件循环策略"""
    policy = asyncio.get_event_loop_policy()
    return policy
```

## 3. 测试配置与设置

### 3.1 pytest 配置

项目使用 `pytest.ini` 和 `pyproject.toml` 中的 `[tool.pytest.ini_options]` 部分配置 pytest：

```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    asyncio: mark a test as an asyncio test
    playwright: mark a test as a playwright test
```

### 3.2 mypy 类型检查配置

项目使用 `mypy.ini` 和 `pyproject.toml` 中的 `[tool.mypy]` 部分配置 mypy：

```ini
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False
disallow_incomplete_defs = False
check_untyped_defs = True
disallow_untyped_decorators = False
no_implicit_optional = True
strict_optional = True
```

对于第三方库，配置了特殊处理：

```ini
[mypy.plugins.playwright.*]
ignore_missing_imports = True

[mypy.plugins.httpx.*]
ignore_missing_imports = True
```

### 3.3 代码风格配置

项目使用多种工具确保代码风格一致：

**Black 配置**:
```toml
[tool.black]
line-length = 100
target-version = ["py310", "py311", "py312"]
```

**isort 配置**:
```toml
[tool.isort]
profile = "black"
line_length = 100
```

**Ruff 配置**:
```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I"]
ignore = ["E501"]  # 忽略行长度检查，由black处理

[tool.ruff.lint.isort]
known-first-party = ["woodgate"]
```

**flake8 配置**:
```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,build,dist
ignore = E501
```

## 4. 自动化测试流程

### 4.1 测试运行脚本

项目使用 `run_all_checks.sh` 脚本自动化运行所有测试和检查：

```bash
./run_all_checks.sh          # 运行所有检查
./run_all_checks.sh --format # 只运行代码格式化
./run_all_checks.sh --lint   # 只运行静态代码分析
./run_all_checks.sh --test   # 只运行测试
./run_all_checks.sh --docs   # 只生成文档
```

该脚本集成了以下功能：
- 代码格式化（Black 和 isort）
- 静态代码分析（Ruff、flake8、pylint 和 mypy）
- 单元测试和覆盖率分析
- 文档生成

### 4.2 预提交钩子

项目使用 pre-commit 在代码提交前自动运行检查，配置在 `.pre-commit-config.yaml` 中：

```yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files

-   repo: https://github.com/psf/black
    rev: 25.1.0
    hooks:
    -   id: black
        args: [--line-length=100]

-   repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
    -   id: isort
        args: ["--profile", "black", "--line-length", "100"]

-   repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.8
    hooks:
    -   id: ruff
        args: [--fix, --exit-non-zero-on-fix]

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.9.0
    hooks:
    -   id: mypy
        additional_dependencies: [types-requests]
```

预提交钩子确保每次提交的代码都符合项目的代码质量标准。

### 4.3 开发环境设置

项目提供了 `setup_dev_tools.sh` 脚本，用于设置开发环境：

```bash
./setup_dev_tools.sh
```

该脚本执行以下操作：
- 安装所有开发依赖
- 初始化 pre-commit 钩子
- 安装 Playwright 浏览器
- 初始化 Sphinx 文档

## 5. 代码质量检查

### 5.1 静态代码分析

项目使用多种工具进行静态代码分析：

- **Ruff**: 快速的 Python linter，用于检查常见错误和代码风格问题
- **flake8**: 用于检查 PEP 8 风格问题和语法错误
- **pylint**: 全面的静态分析工具，检查代码风格、错误和设计问题
- **mypy**: 静态类型检查工具，基于类型注解检查类型错误

### 5.2 代码格式化

项目使用自动化工具确保代码格式一致：

- **Black**: 自动格式化 Python 代码，确保一致的代码风格
- **isort**: 自动排序导入语句，确保导入顺序一致

## 6. 持续集成与部署

### 6.1 GitHub Actions

项目使用 GitHub Actions 进行持续集成，配置在 `.github/workflows/python-tests.yml` 中：

```yaml
name: Python Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install uv
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "$HOME/.cargo/bin" >> $GITHUB_PATH

    - name: Install dependencies
      run: |
        uv pip install --system -e ".[dev]"

    - name: Install Playwright browsers
      run: |
        python -m playwright install chromium

    - name: Lint with ruff
      run: |
        uv run ruff check woodgate tests

    - name: Check types with mypy
      run: |
        uv run mypy woodgate

    - name: Run tests
      run: |
        uv run pytest -v --cov=woodgate

    - name: Generate coverage report
      run: |
        uv run pytest --cov=woodgate --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false
```

CI 流程包括：
- 在多个 Python 版本上运行测试
- 运行代码风格检查和静态分析
- 运行单元测试和生成覆盖率报告
- 上传覆盖率报告到 Codecov

### 6.2 文档构建

项目在 CI 中也包含了文档构建流程：

```yaml
  docs:
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install uv
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "$HOME/.cargo/bin" >> $GITHUB_PATH

    - name: Install dependencies
      run: |
        uv pip install --system -e ".[dev]"

    - name: Build documentation
      run: |
        cd docs
        uv run sphinx-apidoc -f -o source ../woodgate
        uv run make html
```

文档构建仅在主分支上的推送事件触发，并且只有在测试通过后才会执行。

## 7. 文档生成

### 7.1 Sphinx 文档

项目使用 Sphinx 生成 API 文档，配置在 `docs/conf.py` 中。文档生成过程包括：

1. 使用 `sphinx-apidoc` 从代码中提取 API 文档
2. 使用 `sphinx-build` 构建 HTML 文档

文档生成可以通过以下命令执行：

```bash
./run_all_checks.sh --docs
```

### 7.2 文档主题和扩展

项目使用以下 Sphinx 扩展和主题：

- **sphinx_rtd_theme**: Read the Docs 主题，提供现代化的文档外观
- **sphinx.ext.autodoc**: 自动从代码中提取文档
- **sphinx.ext.viewcode**: 在文档中显示源代码
- **sphinx.ext.napoleon**: 支持 Google 风格的文档字符串
- **sphinx_autodoc_typehints**: 从类型注解中提取类型信息

## 8. 测试覆盖率分析

### 8.1 覆盖率工具

项目使用 `pytest-cov` 插件生成测试覆盖率报告，可以生成多种格式的报告：

```bash
pytest --cov=woodgate --cov-report=term --cov-report=html
```

这将生成：
- 终端输出的覆盖率摘要
- HTML 格式的详细覆盖率报告（位于 `htmlcov/` 目录）

### 8.2 覆盖率目标

项目的当前覆盖率情况：
- 总体覆盖率：84%
- 各模块覆盖率：
  - `__init__.py`: 100%
  - `__main__.py`: 82%
  - `config.py`: 91%
  - `core/__init__.py`: 100%
  - `core/auth.py`: 79%
  - `core/browser.py`: 71%
  - `core/search.py`: 93%
  - `core/utils.py`: 73%
  - `server.py`: 96%

项目的目标是保持或提高当前的覆盖率水平，特别是提高低覆盖率模块的测试覆盖。

### 8.3 CI 中的覆盖率报告

在 CI 流程中，覆盖率报告会被上传到 Codecov，以便进行历史跟踪和可视化：

```yaml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
    fail_ci_if_error: false
```

## 9. 测试优化建议

### 9.1 提高测试覆盖率

- **增加低覆盖率模块的测试**：
  - 重点关注 `browser.py`（71%）和 `utils.py`（73%）模块
  - 为 `auth.py`（79%）添加更多认证场景的测试

- **添加更多边缘情况测试**：
  - 增加网络错误处理测试
  - 增加超时处理测试
  - 增加并发操作测试

### 9.2 改进测试结构

- **引入测试分层策略**：
  - 明确区分单元测试、集成测试和端到端测试
  - 使用 pytest 标记系统更有效地组织测试

- **实现测试数据管理**：
  - 引入 `factory-boy` 和 `faker` 生成一致的测试数据
  - 创建测试数据工厂，减少测试代码中的重复

### 9.3 解决现有问题

- **修复异步代码警告**：
  - 解决 RuntimeWarning: coroutine was never awaited 警告
  - 检查 `browser.py` 和 `utils.py` 中的异步代码

- **完善文档结构**：
  - 解决文档未包含在目录树中的警告
  - 完善模块和函数的文档注释

### 9.4 增强测试自动化

- **引入性能测试**：
  - 使用 `locust` 进行负载测试
  - 使用 `py-spy` 和 `scalene` 进行性能分析

- **增强安全测试**：
  - 添加依赖安全检查（使用 `pip-audit`）
  - 添加 OWASP 安全测试

- **实现测试报告增强**：
  - 使用 `pytest-html` 生成更美观的测试报告
  - 使用 `pytest-xdist` 并行执行测试，提高速度

### 9.5 逐步提高类型安全

- **增加类型注解覆盖**：
  - 为核心模块添加完整的类型注解
  - 逐步提高 mypy 配置的严格程度

- **启用更严格的类型检查**：
  - 在稳定模块中启用 `disallow_untyped_defs`
  - 最终目标是实现全项目的严格类型检查

通过实施这些优化建议，可以进一步提高项目的代码质量、测试覆盖率和开发效率。
