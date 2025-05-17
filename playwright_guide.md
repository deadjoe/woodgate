# Playwright for Python – 综合开发指南

*基于官方Playwright文档整合 – 最后更新于 2025年5月*

> 本文档作为单一知识源，提供Playwright Python API的全面参考和最佳实践。所有链接指向官方文档 <https://playwright.dev/python>。

---

## 目录
1. [简介与主要优势](#简介与主要优势)
2. [版本信息](#版本信息)
3. [安装](#安装)
4. [入门示例](#入门示例)
5. [核心概念](#核心概念)
6. [API速查表](#api速查表)
7. [使用Pytest测试](#使用pytest测试)
8. [调试与可观察性](#调试与可观察性)
9. [从Selenium迁移](#从selenium迁移)
10. [CI与Docker](#ci与docker)
11. [高级主题](#高级主题)
12. [常用代码示例](#常用代码示例)
13. [故障排除](#故障排除)
14. [其他资源](#其他资源)

---

## 简介与主要优势
Playwright是由Microsoft开发的下一代浏览器自动化库，使用单一API控制**Chromium**、**Firefox**和**WebKit**浏览器。

从Selenium迁移的主要优势：
- **内置驱动程序** – 无需外部WebDriver二进制文件
- **内置自动等待** – 消除显式等待
- **网络控制与HAR跟踪** – 开箱即用
- **无头与有头模式** – 设备模拟、下载、视频、跟踪
- **确定性** – 每个操作都经过可见性/事件接收验证

---

## 版本信息
| 库 | 最新稳定版 | Python要求 | 说明 |
|---------|---------------|-----------------|-------|
| playwright | **1.44.2** (2025年4月) | 3.8 – 3.12 | 核心同步/异步API |
| pytest-playwright | **0.5.0** (2025年3月) | 3.8 – 3.12 | Pytest固件与CLI |
| 浏览器 | Chromium 136, Firefox 137, WebKit 18.4 | 自动安装 | 使用`python -m playwright install` |

---

## 安装
```bash
# 1. 安装库
pip install --upgrade playwright          # 或使用 poetry add playwright

# 2. 下载浏览器 (约 300 MB)
python -m playwright install              # 安装所有三种浏览器
python -m playwright install chromium     # 仅安装单一浏览器
python -m playwright install --with-deps  # CI Linux依赖项

# 可选: 安装测试运行器
pip install pytest-playwright
```

验证安装：
```bash
python -m playwright --version
playwright codegen --help
```

---

## 入门示例
### 同步示例
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")
    print(page.title())
    browser.close()
```

### 异步示例
```python
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch()
        page = await browser.new_page()
        await page.goto("https://example.com")
        await page.pdf(path="report.pdf")
        await browser.close()
asyncio.run(main())
```

### 使用代码生成器
```bash
playwright codegen https://example.com      # 启动检查器并记录脚本
```
生成的代码可以是**Python同步**或**异步**风格。

---

## 核心概念
### 浏览器与启动选项
- `p.chromium`, `p.firefox`, `p.webkit`
- 重要选项: `headless`, `slow_mo`, `proxy`, `channel="chrome"`

```python
# 启动浏览器
browser = p.chromium.launch(
    headless=False,  # 有头模式
    slow_mo=100,     # 减慢操作速度，便于调试
)
```

### 浏览器上下文
- 轻量级、隐身模式风格的配置文件
- 使用`browser.new_context()`创建
- 比启动另一个浏览器更高效

```python
# 创建浏览器上下文
context = browser.new_context(
    viewport={"width": 1280, "height": 720},
    user_agent="自定义用户代理",
    locale="zh-CN",
    timezone_id="Asia/Shanghai",
    geolocation={"latitude": 59.95, "longitude": 30.31667},
)
```

### 页面
- 通过`context.new_page()`生成
- 每个标签页继承上下文权限、Cookie、地理位置等

```python
# 创建页面
page = context.new_page()

# 导航
page.goto("https://example.com", wait_until="networkidle")
page.go_back()
page.go_forward()
page.reload()
```

### 定位器与自动等待
```python
# 使用定位器 (推荐)
page.locator("text=Login").click()
page.get_by_role("button", name="Submit").click()
```

每个操作都会等待：
1. 元素附加并可见
2. 稳定（不在动画中）
3. 接收事件（未被覆盖）

```python
# 定位元素的多种方式
locator = page.locator("css selector")
locator = page.get_by_role("button", name="Submit")
locator = page.get_by_text("Welcome")
locator = page.get_by_label("Password")
locator = page.get_by_placeholder("Enter your name")
locator = page.get_by_alt_text("Logo")
locator = page.get_by_title("Information")
locator = page.get_by_test_id("submit-button")

# 链式定位
dialog = page.locator(".dialog")
submit_button = dialog.get_by_role("button", name="Submit")

# 框架内定位
frame_locator = page.frame_locator("#my-frame")
button = frame_locator.get_by_role("button")
```

### 事件与监听器
```python
page.on("download", lambda d: d.save_as("file.zip"))
```

### 处理弹出窗口、框架、下载
- `page.expect_popup()` 作为异步上下文管理器
- `page.frame_locator("iframe[name=editor]")`
- `context.expect_download()`

---

## API速查表
### 操作元素
```python
# 点击
locator.click()

# 填写表单
locator.fill("text")
locator.clear()  # 清空输入
locator.press("Enter")  # 按键
locator.press_sequentially("text", delay=100)  # 模拟逐字输入

# 选择选项
locator.select_option("value")
locator.select_option(value="value")
locator.select_option(index=2)
locator.select_option(label="Option Label")

# 复选框和单选按钮
locator.check()
locator.uncheck()
locator.set_checked(True)

# 拖放
page.drag_and_drop("#source", "#target")

# 悬停
locator.hover()

# 上传文件
locator.set_input_files("path/to/file.txt")
locator.set_input_files(["file1.txt", "file2.txt"])  # 多文件
```

### 获取信息
```python
# 获取文本
text = locator.text_content()
inner_text = locator.inner_text()

# 获取属性
value = locator.get_attribute("href")

# 获取HTML
html = locator.inner_html()

# 检查状态
is_visible = locator.is_visible()
is_hidden = locator.is_hidden()
is_enabled = locator.is_enabled()
is_disabled = locator.is_disabled()
is_checked = locator.is_checked()
is_editable = locator.is_editable()
```

### 断言 (Pytest风格)
```python
from playwright.sync_api import expect
expect(page.locator("h1")).to_have_text("Welcome")

# 元素状态断言
expect(locator).to_be_visible()
expect(locator).to_be_hidden()
expect(locator).to_be_enabled()
expect(locator).to_be_disabled()
expect(locator).to_be_checked()
expect(locator).to_be_editable()
expect(locator).to_be_focused()
expect(locator).to_be_attached()  # 元素存在于DOM中

# 内容断言
expect(locator).to_have_text("Expected text")
expect(locator).to_have_text(re.compile(r"Expected \w+"))
expect(locator).to_contain_text("partial text")
expect(locator).to_have_value("input value")
expect(locator).to_have_values(["option1", "option2"])  # 对于多选框

# 属性断言
expect(locator).to_have_attribute("attr", "value")
expect(locator).to_have_class("class-name")
expect(locator).to_have_css("color", "rgb(255, 0, 0)")
expect(locator).to_have_id("element-id")
expect(locator).to_have_js_property("property", "value")

# 计数断言
expect(locator).to_have_count(5)

# 页面断言
expect(page).to_have_title("Page Title")
expect(page).to_have_url("https://example.com/path")
expect(page).to_have_url(re.compile(r"example\.com/\w+"))
```

---

## 使用Pytest测试
安装: `pip install pytest-playwright`

关键固件:
| 固件 | 作用域 | 描述 |
|---------|-------|-------------|
| `browser` | session | 预启动的浏览器 |
| `context` | function | 每个测试的隔离上下文 |
| `page` | function | 新页面 |

运行:
```bash
pytest --browser firefox --headed -q
```
并行工作:
```bash
pytest -n auto                 # 自动使用pytest-xdist
```

配置 (`pytest.ini`):
```ini
[pytest]
addopts = --browser chromium --headed --base-url https://staging.example.com
```

---

## 调试与可观察性
| 工具 | 命令/API |
|------|---------------|
| **检查器** | `PWDEBUG=1 pytest tests/test_login.py::test_basic` |
| **跟踪** | ```context.tracing.start(screenshots=True, snapshots=True)
# …操作…
context.tracing.stop(path="trace.zip")``` |
| **跟踪查看器** | `playwright show-trace trace.zip` 或 <https://trace.playwright.dev/> |
| **视频** | `context = browser.new_context(record_video_dir="videos")` |
| **详细日志** | `DEBUG=pw:api` |

---

## 从Selenium迁移
| Selenium | Playwright (同步) |
|----------|------------------|
| `driver = webdriver.Chrome()` | `browser = p.chromium.launch()` |
| `driver.get(url)` | `page.goto(url)` |
| `driver.find_element(By.CSS_SELECTOR, "#id")` | `page.locator("#id")` |
| `element.click()` | `locator.click()` |
| 显式等待 (`WebDriverWait`) | **不需要** – Playwright自动等待 |
| 截图: `driver.save_screenshot` | `page.screenshot` |
| 通过Selenium Grid并行 | 原生**并行上下文/页面** |

**迁移提示**
- 移除等待；依赖定位器或`expect`断言
- 用`playwright install`替代驱动管理
- 使用`page.route()`进行网络存根，替代之前用代理完成的工作

---

## CI与Docker
### GitHub Actions (`.github/workflows/playwright.yml`)
```yaml
name: Playwright
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - name: Install deps
        run: |
          pip install playwright pytest-playwright
          python -m playwright install --with-deps
      - name: Run tests
        run: pytest
      - name: Upload trace
        uses: actions/upload-artifact@v4
        with:
          name: traces
          path: trace.zip
```

### Docker (无头)
```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.44-noble
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["pytest", "-q"]
```
镜像已捆绑浏览器和操作系统依赖项。

---

## 高级主题
- **设备模拟:** `context = browser.new_context(is_mobile=True, viewport={"width":375,"height":667}, user_agent=iPhoneUA)`
- **网络拦截:** `page.route("**/api/**", lambda route: route.abort())`
- **HAR记录:** `context = browser.new_context(record_har_path="log.har")`
- **离线/地理位置/权限:** 内置上下文选项
- **组件测试(alpha):** <https://playwright.dev/python/docs/component-testing>

---

## 常用代码示例
```python
# 文件上传
page.set_input_files("input[type=file]", Path("resume.pdf"))

# 等待点击后的导航
with page.expect_navigation():
    page.locator("text=Save").click()

# 处理基本认证
context = browser.new_context(http_credentials={"username":"u", "password":"p"})

# 拦截请求
# 拦截并阻止请求
page.route("**/*.{png,jpg,jpeg}", lambda route: route.abort())

# 拦截并修改请求
def handle_route(route):
    headers = route.request.headers
    headers["custom-header"] = "value"
    route.continue_(headers=headers)

page.route("**/api/endpoint", handle_route)

# 拦截并返回模拟响应
page.route(
    "**/api/data",
    lambda route: route.fulfill(
        status=200,
        body=json.dumps({"data": "mocked"}),
        headers={"Content-Type": "application/json"}
    )
)

# 从HAR文件路由
page.route_from_har("recording.har", url="**/api/**")

# 监听控制台消息
page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}"))

# 监听对话框
page.on("dialog", lambda dialog: dialog.accept())

# 监听下载
page.on("download", lambda download: print(download.path()))

# 监听页面错误
page.on("pageerror", lambda err: print(f"Page error: {err}"))
```

---

## 故障排除
| 症状 | 解决方案 |
|---------|------------|
| `Executable doesn't exist` | 运行 `python -m playwright install` |
| 等待元素超时 | 使用正确的定位器，确保网络空闲，增大 `timeout` |
| 本地工作，CI失败 | 添加 `--with-deps`，使用xvfb或Docker镜像 |

---

## 其他资源
- 官方文档根目录: <https://playwright.dev/python>
- API参考: <https://playwright.dev/python/docs/api/class-page>
- 代码生成器: <https://playwright.dev/python/docs/codegen>
- 跟踪与查看器: <https://playwright.dev/python/docs/trace-viewer>
- 定位器指南: <https://playwright.dev/python/docs/locators>
- 社区Discord: <https://aka.ms/playwright-discord>

---

*指南结束*
