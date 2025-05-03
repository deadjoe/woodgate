# Playwright for Python – Comprehensive Developer Guide  
*Consolidated from the official Playwright documentation – last verified **May 4 2025***

> Use this file as a single‑source knowledge base when instructing an LLM to migrate from Selenium to Playwright. All links point to the canonical docs at <https://playwright.dev/python> unless otherwise stated.

---

## Table of Contents
1. [Introduction & Key Benefits](#introduction--key-benefits)  
2. [Version Matrix](#version-matrix)  
3. [Installation](#installation)  
4. [First Steps](#first-steps)  
5. [Core Concepts](#core-concepts)  
6. [API Cheatsheet](#api-cheatsheet)  
7. [Testing with Pytest](#testing-with-pytest)  
8. [Debugging & Observability](#debugging--observability)  
9. [Migrating from Selenium](#migrating-from-selenium)  
10. [CI & Docker](#ci--docker)  
11. [Advanced Topics](#advanced-topics)  
12. [Recipes](#recipes)  
13. [Troubleshooting](#troubleshooting)  
14. [Additional Resources](#additional-resources)  

---

## Introduction  &  Key Benefits
Playwright is a next‑gen browser automation library from Microsoft that controls **Chromium**, **Firefox**, and **WebKit** with a single API.  
Why migrate from Selenium:
- **Drivers included** – no external WebDriver binaries.  
- **Built‑in auto‑waiting** removes explicit sleeps.  
- **Network control & HAR tracing** out‑of‑the‑box.  
- **Headless & headed** modes, device emulation, downloads, video, tracing.  
- **Deterministic** – each action validated for visibility/receiving events.

---

## Version Matrix
| Library | Latest stable | Requires Python | Notes |
|---------|---------------|-----------------|-------|
| playwright | **1.44.2** (Apr 2025) | 3.8 – 3.12 | Core sync/async APIs |
| pytest‑playwright | **0.5.0** (Mar 2025) | 3.8 – 3.12 | Pytest fixtures & CLI |
| Browsers | Chromium 136, Firefox 137, WebKit 18.4 | auto‑installed | Use `python -m playwright install` |

---

## Installation
```bash
# 1. Library
pip install --upgrade playwright          # or poetry add playwright

# 2. Download browsers (≈ 300 MB)
python -m playwright install              # all three
python -m playwright install chromium     # single
python -m playwright install --with-deps  # CI Linux deps

# Optional: test runner
pip install pytest-playwright
```

Verify:
```bash
python -m playwright --version
playwright codegen --help
```

---

## First Steps
### Synchronous example
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")
    print(page.title())
    browser.close()
```

### Asynchronous example
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

### Scaffold with Codegen
```bash
playwright codegen https://example.com      # launches inspector & records script
```
Generated code is available in **Python sync** & **async** flavours.

---

## Core Concepts
### Browsers & Launch Options
- `p.chromium`, `p.firefox`, `p.webkit`
- Important options: `headless`, `slow_mo`, `proxy`, `channel="chrome"`.

### BrowserContexts
- Lightweight, incognito‑style profiles.
- Use `browser.new_context()`; close to free vs launching another browser.

### Pages
- Generated via `context.new_page()`.
- Each tab inherits context permissions, cookies, geolocation, etc.

### Locators & Auto‑waiting
```python
page.locator("text=Login").click()
page.get_by_role("button", name="Submit").click()
```
Every action waits for:
1. Element attached & visible  
2. Stable (not animating)  
3. Receives events (not covered)  

### Events & Listeners
```python
page.on("download", lambda d: d.save_as("file.zip"))
```

### Handling Popups, Frames, Downloads
- `page.expect_popup()` as async context manager.
- `page.frame_locator("iframe[name=editor]")`.
- `context.expect_download()`.

---

## API Cheatsheet
### `BrowserType`
| Method | Description |
|--------|-------------|
| `launch(**kw)` | Start browser process |
| `launch_persistent_context(user_data_dir, **kw)` | Reusable profile |

### `Page`
| Action | Example |
|--------|---------|
| Navigate | `page.goto(url, wait_until="domcontentloaded")` |
| Click | `page.locator("#login").click()` |
| Fill | `page.fill("input[name=q]", "search")` |
| Evaluate JS | `page.evaluate("window.scrollTo(0, document.body.scrollHeight)")` |
| Screenshot | `page.screenshot(path="shot.png", full_page=True)` |
| PDF (Chromium) | `page.pdf(path="out.pdf")` |

### Assertions (Pytest‑style)
```python
from playwright.sync_api import expect
expect(page.locator("h1")).to_have_text("Welcome")
```

---

## Testing with Pytest
Install: `pip install pytest-playwright`.

Key fixtures:
| Fixture | Scope | Description |
|---------|-------|-------------|
| `browser` | session | Pre‑launched browser |
| `context` | function | Isolated context per test |
| `page` | function | New page |

Run:
```bash
pytest --browser firefox --headed -q
```
Parallel workers:
```bash
pytest -n auto                 # uses pytest‑xdist automatically
```

Config (`pytest.ini`):
```ini
[pytest]
addopts = --browser chromium --headed --base-url https://staging.example.com
```

---

## Debugging & Observability
| Tool | Command / API |
|------|---------------|
| **Inspector** | `PWDEBUG=1 pytest tests/test_login.py::test_basic` |
| **Tracing** | ```context.tracing.start(screenshots=True, snapshots=True)
# …actions…
context.tracing.stop(path="trace.zip")``` |
| **Trace Viewer** | `playwright show-trace trace.zip` or <https://trace.playwright.dev/> |
| **Video** | `context = browser.new_context(record_video_dir="videos")` |
| **Verbose Logs** | `DEBUG=pw:api` |

---

## Migrating from Selenium
| Selenium | Playwright (sync) |
|----------|------------------|
| `driver = webdriver.Chrome()` | `browser = p.chromium.launch()` |
| `driver.get(url)` | `page.goto(url)` |
| `driver.find_element(By.CSS_SELECTOR, "#id")` | `page.locator("#id")` |
| `element.click()` | `locator.click()` |
| Explicit waits (`WebDriverWait`) | **Not needed** – Playwright auto‑waits |
| Screenshots: `driver.save_screenshot` | `page.screenshot` |
| Parallel via Selenium Grid | Native **parallel contexts/pages** |

**Migration Tips**
- Remove sleeps; rely on locators or `expect` assertions.  
- Replace driver management with `playwright install`.  
- Use `page.route()` for network stubbing previously done with proxies.  

---

## CI & Docker
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

### Docker (headless)
```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.44-noble
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["pytest", "-q"]
```
Image already bundles browsers & OS deps.

---

## Advanced Topics
- **Device emulation:** `context = browser.new_context(is_mobile=True, viewport={"width":375,"height":667}, user_agent=iPhoneUA)`  
- **Network interception:** `page.route("**/api/**", lambda route: route.abort())`  
- **HAR recording:** `context = browser.new_context(record_har_path="log.har")`  
- **Offline / geolocation / permissions:** built‑in context options.  
- **Component Testing (alpha):** <https://playwright.dev/python/docs/component-testing>  

---

## Recipes
```python
# File upload
page.set_input_files("input[type=file]", Path("resume.pdf"))

# Wait for navigation after click
with page.expect_navigation():
    page.locator("text=Save").click()

# Handle basic auth
context = browser.new_context(http_credentials={"username":"u", "password":"p"})
```

---

## Troubleshooting
| Symptom | Resolution |
|---------|------------|
| `Executable doesn't exist` | Run `python -m playwright install` |
| Timeout waiting for element | Use correct locator, ensure network idle, enlarge `timeout` |
| Works locally, fails CI | Add `--with-deps`, use xvfb or Docker image |

---

## Additional Resources
- Official docs root: <https://playwright.dev/python>  
- API reference: <https://playwright.dev/python/docs/api/class-page>  
- Codegen: <https://playwright.dev/python/docs/codegen>  
- Tracing & viewer: <https://playwright.dev/python/docs/trace-viewer>  
- Locators guide: <https://playwright.dev/python/docs/locators>  
- Migration blog: Browserless “Migrating from Selenium to Playwright”  
- Community Discord: <https://aka.ms/playwright-discord>  

---

*End of Guide*
