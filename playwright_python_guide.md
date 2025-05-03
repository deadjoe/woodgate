# Playwright Python 文档总结

## 1. 安装和设置

### 安装 Playwright

```bash
pip install playwright
playwright install  # 安装浏览器
```

### 基本使用

```python
# 同步模式
from playwright.sync_api import sync_playwright

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")
    # 其他操作...
    browser.close()

# 异步模式
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://example.com")
        # 其他操作...
        await browser.close()

asyncio.run(run())
```

## 2. 浏览器和上下文

### 浏览器启动选项

```python
# 启动浏览器
browser = playwright.chromium.launch(
    headless=False,  # 有头模式
    slow_mo=100,     # 减慢操作速度，便于调试
)

# 创建浏览器上下文
context = browser.new_context(
    viewport={"width": 1280, "height": 720},
    user_agent="自定义用户代理",
    locale="zh-CN",
    timezone_id="Asia/Shanghai",
    geolocation={"latitude": 59.95, "longitude": 30.31667},
)

# 创建页面
page = context.new_page()
```

### 多个浏览器上下文

```python
# 创建多个独立的上下文（类似于隐私模式）
context1 = browser.new_context()
context2 = browser.new_context()

page1 = context1.new_page()
page2 = context2.new_page()
```

## 3. 页面操作和定位器

### 页面导航

```python
# 导航到URL
page.goto("https://example.com")

# 等待加载状态
page.goto("https://example.com", wait_until="networkidle")  # 等待网络空闲
page.goto("https://example.com", wait_until="domcontentloaded")  # 等待DOM加载完成
page.goto("https://example.com", wait_until="load")  # 等待页面完全加载

# 导航历史
page.go_back()
page.go_forward()
page.reload()
```

### 定位元素

```python
# 使用定位器 (推荐)
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

## 4. 等待和自动等待

### 自动等待

Playwright 会自动等待元素满足"可操作性"条件，包括：
- 元素可见
- 元素稳定（不在动画中）
- 元素可接收事件（不被其他元素遮挡）
- 元素已启用（非禁用状态）
- 元素可编辑（对于输入操作）

### 显式等待

```python
# 等待元素
locator.wait_for()  # 等待元素可见
locator.wait_for(state="hidden")  # 等待元素隐藏

# 等待导航
with page.expect_navigation():
    locator.click()  # 触发导航的操作

# 等待网络请求
with page.expect_request("**/api/data") as request_info:
    locator.click()  # 触发请求的操作
request = request_info.value

# 等待响应
with page.expect_response("**/api/data") as response_info:
    locator.click()
response = response_info.value

# 等待下载
with page.expect_download() as download_info:
    locator.click()  # 触发下载的操作
download = download_info.value

# 等待对话框
with page.expect_dialog() as dialog_info:
    locator.click()  # 触发对话框的操作
dialog = dialog_info.value
dialog.accept()  # 或 dialog.dismiss()

# 等待函数条件
page.wait_for_function("() => window.status === 'ready'")

# 等待超时
page.wait_for_timeout(1000)  # 等待1秒（不推荐在生产环境使用）
```

## 5. 断言

```python
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

# API响应断言
expect(response).to_be_ok()  # 状态码 200-299
```

## 6. 网络拦截和模拟

### 拦截请求

```python
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
```

### 模拟设备和环境

```python
# 模拟移动设备
iphone = playwright.devices["iPhone 13"]
context = browser.new_context(**iphone)

# 模拟地理位置
context = browser.new_context(
    geolocation={"latitude": 59.95, "longitude": 30.31667},
    permissions=["geolocation"]
)

# 模拟时区和语言
context = browser.new_context(
    locale="zh-CN",
    timezone_id="Asia/Shanghai"
)

# 模拟颜色方案
context = browser.new_context(color_scheme="dark")
# 或
page.emulate_media(color_scheme="dark")

# 模拟网络状态
context = browser.new_context(offline=True)
```

## 7. JavaScript 执行

```python
# 执行JavaScript
result = page.evaluate("1 + 2")

# 传递参数
result = page.evaluate("([x, y]) => x + y", [1, 2])

# 执行异步JavaScript
result = page.evaluate("async () => { await new Promise(r => setTimeout(r, 1000)); return 42; }")

# 获取JavaScript句柄
handle = page.evaluate_handle("document.body")
```

## 8. 事件监听

```python
# 监听控制台消息
page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}"))

# 监听对话框
page.on("dialog", lambda dialog: dialog.accept())

# 监听下载
page.on("download", lambda download: print(download.path()))

# 监听页面错误
page.on("pageerror", lambda err: print(f"Page error: {err}"))

# 监听请求
page.on("request", lambda request: print(f"Request: {request.url}"))

# 监听响应
page.on("response", lambda response: print(f"Response: {response.url}, {response.status}"))
```

## 9. 截图和视频

```python
# 页面截图
page.screenshot(path="screenshot.png")

# 元素截图
locator.screenshot(path="element.png")

# 全页面截图
page.screenshot(path="fullpage.png", full_page=True)

# 录制视频
context = browser.new_context(
    record_video_dir="videos/",
    record_video_size={"width": 1280, "height": 720}
)
```

## 10. 其他功能

### 文件下载

```python
# 等待下载
with page.expect_download() as download_info:
    page.click("button#download")
download = download_info.value

# 保存下载文件
download.save_as("/path/to/save/file.txt")

# 获取下载信息
path = download.path()
url = download.url
suggested_filename = download.suggested_filename
```

### 对话框处理

```python
# 自动处理对话框
page.on("dialog", lambda dialog: dialog.accept())
page.on("dialog", lambda dialog: dialog.dismiss())

# 等待对话框
with page.expect_dialog() as dialog_info:
    page.click("button#show-dialog")
dialog = dialog_info.value
dialog.accept("输入文本")  # 对于prompt对话框
```

### 存储状态

```python
# 保存存储状态（cookies和localStorage）
storage = context.storage_state()
with open("state.json", "w") as f:
    f.write(json.dumps(storage))

# 使用存储状态创建新上下文
context = browser.new_context(storage_state="state.json")
```

### API测试

```python
# 创建API请求上下文
request_context = playwright.request.new_context(
    base_url="https://api.example.com",
    extra_http_headers={"Authorization": "Bearer token"}
)

# 发送请求
response = request_context.get("/users")
response = request_context.post("/data", data={"key": "value"})
response = request_context.put("/update", json={"key": "value"})

# 处理响应
assert response.ok
data = response.json()
```
