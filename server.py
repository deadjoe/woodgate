"""
MCP服务器模块 - 实现Model Context Protocol服务器
"""

import os
import sys
import logging
import asyncio
import subprocess
import importlib.util
from typing import List, Dict, Any, Optional

# 环境变量应该在运行时设置，而不是硬编码在代码中
# 例如: export REDHAT_USERNAME="your_username" && export REDHAT_PASSWORD="your_password"

# 设置日志
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stderr)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 检查并安装必要的依赖
required_packages = ['selenium', 'webdriver-manager', 'httpx']

for package in required_packages:
    if importlib.util.find_spec(package) is None:
        logger.info(f"正在安装 {package}...")
        try:
            # 尝试使用uv安装
            try:
                subprocess.check_call(['uv', 'pip', 'install', package])
                logger.info(f"{package} 使用uv安装成功")
            except Exception as e1:
                logger.warning(f"使用uv安装 {package} 失败: {e1}")
                # 尝试使用pip安装
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                    logger.info(f"{package} 使用pip安装成功")
                except Exception as e2:
                    logger.warning(f"使用pip安装 {package} 失败: {e2}")
                    # 尝试使用系统pip安装
                    subprocess.check_call(['pip', 'install', package])
                    logger.info(f"{package} 使用系统pip安装成功")
        except Exception as e:
            logger.error(f"安装 {package} 失败: {e}")
            logger.error("继续执行，但可能会导致功能不正常")

# 导入必要的模块
try:
    from mcp.server.fastmcp import FastMCP
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    import httpx
except ImportError as e:
    logger.error(f"导入错误: {e}")
    raise

# 创建MCP服务器
mcp = FastMCP("Woodgate", description="Red Hat客户门户搜索工具")

# 配置
REDHAT_PORTAL_URL = "https://access.redhat.com"
REDHAT_LOGIN_URL = "https://sso.redhat.com/auth/realms/redhat-external/login-actions/authenticate"
REDHAT_SEARCH_URL = "https://access.redhat.com/search"

# 获取凭据
def get_credentials():
    """从环境变量获取Red Hat客户门户凭据"""
    username = os.environ.get("REDHAT_USERNAME")
    password = os.environ.get("REDHAT_PASSWORD")

    if not username or not password:
        raise ValueError("未设置REDHAT_USERNAME或REDHAT_PASSWORD环境变量")

    return username, password

# 初始化浏览器
async def initialize_browser():
    """初始化Chrome浏览器"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    return driver

# 处理Cookie弹窗
async def handle_cookie_popup(driver):
    """处理Cookie弹窗"""
    try:
        # 等待Cookie弹窗出现
        cookie_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "truste-consent-button"))
        )
        cookie_button.click()
        await asyncio.sleep(1)
        return True
    except Exception:
        # 如果没有Cookie弹窗，继续
        return False

# 登录到Red Hat客户门户
async def login_to_redhat_portal(driver, username, password):
    """登录到Red Hat客户门户"""
    try:
        # 访问Red Hat客户门户
        driver.get(REDHAT_PORTAL_URL)

        # 处理Cookie弹窗
        await handle_cookie_popup(driver)

        # 点击登录按钮
        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Log In"))
            )
            login_button.click()
        except Exception:
            # 可能已经在登录页面
            pass

        # 输入用户名
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_input.clear()
        username_input.send_keys(username)

        # 点击下一步
        next_button = driver.find_element(By.ID, "login-show-step2")
        next_button.click()

        # 输入密码
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        password_input.clear()
        password_input.send_keys(password)

        # 点击登录
        login_submit = driver.find_element(By.ID, "kc-login")
        login_submit.click()

        # 等待登录完成
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pf-c-page__header"))
        )

        return True
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return False

# 执行搜索
async def perform_search(driver, query, products=None, doc_types=None, page=1, rows=20, sort_by="relevant"):
    """在Red Hat客户门户执行搜索"""
    try:
        # 构建搜索URL
        search_url = f"{REDHAT_SEARCH_URL}?q={query}&p={page}&rows={rows}&sort={sort_by}"

        # 添加产品过滤
        if products:
            for product in products:
                search_url += f"&product={product}"

        # 添加文档类型过滤
        if doc_types:
            for doc_type in doc_types:
                search_url += f"&documentKind={doc_type}"

        # 访问搜索页面
        driver.get(search_url)

        # 等待搜索结果加载
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pf-c-page__main-section"))
        )

        # 检查是否有搜索结果
        try:
            results_container = driver.find_element(By.CLASS_NAME, "pf-c-card")
        except Exception:
            # 没有搜索结果
            return []

        # 提取搜索结果
        results = []
        result_elements = driver.find_elements(By.CSS_SELECTOR, ".pf-c-card__body")

        for element in result_elements:
            try:
                # 提取标题和URL
                title_element = element.find_element(By.CSS_SELECTOR, "h2 a")
                title = title_element.text.strip()
                url = title_element.get_attribute("href")

                # 提取摘要
                try:
                    summary_element = element.find_element(By.CSS_SELECTOR, ".co-search-result__description")
                    summary = summary_element.text.strip()
                except Exception:
                    summary = "无摘要"

                # 提取文档类型
                try:
                    doc_type_element = element.find_element(By.CSS_SELECTOR, ".co-search-result__kind")
                    doc_type = doc_type_element.text.strip()
                except Exception:
                    doc_type = "未知"

                # 提取最后更新时间
                try:
                    date_element = element.find_element(By.CSS_SELECTOR, ".co-search-result__date")
                    last_updated = date_element.text.strip()
                except Exception:
                    last_updated = "未知"

                results.append({
                    "title": title,
                    "url": url,
                    "summary": summary,
                    "doc_type": doc_type,
                    "last_updated": last_updated
                })
            except Exception as e:
                logger.error(f"提取搜索结果时出错: {e}")

        return results
    except Exception as e:
        logger.error(f"执行搜索时出错: {e}")
        return []

# 获取产品警报
async def get_product_alerts(driver, product):
    """获取特定产品的警报信息"""
    try:
        # 构建警报URL
        alerts_url = f"{REDHAT_PORTAL_URL}/products/{product}/alerts"

        # 访问警报页面
        driver.get(alerts_url)

        # 等待警报加载
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pf-c-page__main-section"))
        )

        # 提取警报信息
        alerts = []
        alert_elements = driver.find_elements(By.CSS_SELECTOR, ".pf-c-card")

        for element in alert_elements:
            try:
                # 提取标题和URL
                title_element = element.find_element(By.CSS_SELECTOR, "h2 a")
                title = title_element.text.strip()
                url = title_element.get_attribute("href")

                # 提取摘要
                try:
                    summary_element = element.find_element(By.CSS_SELECTOR, ".co-alert__description")
                    summary = summary_element.text.strip()
                except Exception:
                    summary = "无摘要"

                # 提取严重性
                try:
                    severity_element = element.find_element(By.CSS_SELECTOR, ".co-alert__severity")
                    severity = severity_element.text.strip()
                except Exception:
                    severity = "未知"

                # 提取发布日期
                try:
                    date_element = element.find_element(By.CSS_SELECTOR, ".co-alert__date")
                    published_date = date_element.text.strip()
                except Exception:
                    published_date = "未知"

                alerts.append({
                    "title": title,
                    "url": url,
                    "summary": summary,
                    "severity": severity,
                    "published_date": published_date
                })
            except Exception as e:
                logger.error(f"提取警报信息时出错: {e}")

        return alerts
    except Exception as e:
        logger.error(f"获取产品警报时出错: {e}")
        return []

# 获取文档内容
async def get_document_content(driver, document_url):
    """获取特定文档的详细内容"""
    try:
        # 访问文档页面
        driver.get(document_url)

        # 等待文档加载
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pf-c-page__main-section"))
        )

        # 提取文档标题
        try:
            title_element = driver.find_element(By.CSS_SELECTOR, "h1")
            title = title_element.text.strip()
        except Exception:
            title = "未知标题"

        # 提取文档内容
        try:
            content_element = driver.find_element(By.CSS_SELECTOR, ".pf-c-content")
            content = content_element.text.strip()
        except Exception:
            content = "无法提取文档内容"

        return {
            "title": title,
            "url": document_url,
            "content": content
        }
    except Exception as e:
        logger.error(f"获取文档内容时出错: {e}")
        return {
            "title": "错误",
            "url": document_url,
            "content": f"获取文档内容时出错: {e}"
        }

# 可用产品列表
def get_available_products():
    """获取可用的产品列表"""
    return [
        "Red Hat Enterprise Linux",
        "Red Hat OpenShift Container Platform",
        "Red Hat OpenStack Platform",
        "Red Hat Virtualization",
        "Red Hat Satellite",
        "Red Hat Ansible Automation Platform",
        "Red Hat JBoss Enterprise Application Platform",
        "Red Hat Ceph Storage",
        "Red Hat Gluster Storage",
        "Red Hat OpenShift Service on AWS",
        "Red Hat OpenShift Dedicated",
        "Red Hat OpenShift Online",
        "Red Hat Quay",
        "Red Hat Advanced Cluster Management",
        "Red Hat Advanced Cluster Security",
        "Red Hat Integration",
        "Red Hat Process Automation",
        "Red Hat Decision Manager",
        "Red Hat Fuse",
        "Red Hat AMQ"
    ]

# 可用文档类型
def get_document_types():
    """获取可用的文档类型"""
    return [
        "Solution",
        "Article",
        "Documentation",
        "Video",
        "Blog",
        "Book",
        "FAQ",
        "Knowledgebase",
        "Troubleshoot"
    ]

@mcp.tool()
async def search(
    query: str,
    products: Optional[List[str]] = None,
    doc_types: Optional[List[str]] = None,
    page: int = 1,
    rows: int = 20,
    sort_by: str = "relevant",
) -> List[Dict[str, Any]]:
    """
    在Red Hat客户门户中执行搜索

    Args:
        query: 搜索关键词
        products: 要搜索的产品列表，例如 ["Red Hat Enterprise Linux", "Red Hat OpenShift"]
        doc_types: 文档类型列表，例如 ["Solution", "Article"]
        page: 页码
        rows: 每页结果数
        sort_by: 排序方式，可选值: "relevant", "lastModifiedDate desc", "lastModifiedDate asc"

    Returns:
        搜索结果列表
    """
    logger.debug(f"搜索函数开始执行，参数: query='{query}', products={products}, doc_types={doc_types}, page={page}, rows={rows}, sort_by='{sort_by}'")

    try:
        logger.debug("初始化浏览器...")
        browser = await initialize_browser()
        logger.debug("浏览器初始化成功")

        try:
            logger.debug("获取凭据...")
            username, password = get_credentials()
            logger.debug(f"凭据获取成功: username='{username}'")

            logger.debug("登录到Red Hat客户门户...")
            login_success = await login_to_redhat_portal(browser, username, password)
            logger.debug(f"登录结果: {login_success}")

            if not login_success:
                logger.error("登录失败，请检查凭据")
                return [{"error": "登录失败，请检查凭据"}]

            logger.debug("执行搜索...")
            results = await perform_search(
                browser,
                query=query,
                products=products or [],
                doc_types=doc_types or [],
                page=page,
                rows=rows,
                sort_by=sort_by,
            )
            logger.debug(f"搜索完成，找到 {len(results)} 条结果")
            return results
        except Exception as e:
            logger.error(f"搜索时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return [{"error": f"搜索时出错: {e}"}]
        finally:
            logger.debug("关闭浏览器...")
            await browser.quit()
            logger.debug("浏览器已关闭")
    except Exception as e:
        logger.error(f"初始化浏览器时出错: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return [{"error": f"初始化浏览器时出错: {e}"}]


@mcp.tool()
async def get_alerts(product: str) -> List[Dict[str, Any]]:
    """
    获取特定产品的警报信息

    Args:
        product: 产品名称，例如 "Red Hat Enterprise Linux"

    Returns:
        警报信息列表
    """
    logger.info(f"获取产品警报: '{product}'")

    browser = await initialize_browser()
    try:
        username, password = get_credentials()
        login_success = await login_to_redhat_portal(browser, username, password)
        if not login_success:
            return [{"error": "登录失败，请检查凭据"}]

        alerts = await get_product_alerts(browser, product)
        return alerts
    except Exception as e:
        logger.error(f"获取警报时出错: {e}")
        return [{"error": f"获取警报时出错: {e}"}]
    finally:
        await browser.quit()


@mcp.tool()
async def get_document(document_url: str) -> Dict[str, Any]:
    """
    获取特定文档的详细内容

    Args:
        document_url: 文档URL

    Returns:
        文档内容
    """
    logger.info(f"获取文档内容: {document_url}")

    browser = await initialize_browser()
    try:
        username, password = get_credentials()
        login_success = await login_to_redhat_portal(browser, username, password)
        if not login_success:
            return {"error": "登录失败，请检查凭据"}

        document = await get_document_content(browser, document_url)
        return document
    except Exception as e:
        logger.error(f"获取文档内容时出错: {e}")
        return {"error": f"获取文档内容时出错: {e}"}
    finally:
        await browser.quit()


@mcp.resource("config://products")
def available_products() -> List[str]:
    """获取可用的产品列表"""
    return get_available_products()


@mcp.resource("config://doc-types")
def document_types() -> List[str]:
    """获取可用的文档类型"""
    return get_document_types()


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

    ## 带文档类型过滤的搜索
    ```python
    search(
        query="selinux permission denied",
        doc_types=["Solution", "Article"]
    )
    ```

    ## 完整搜索示例
    ```python
    search(
        query="performance tuning",
        products=["Red Hat Enterprise Linux"],
        doc_types=["Solution", "Article", "Documentation"],
        page=1,
        rows=50,
        sort_by="lastModifiedDate desc"
    )
    ```

    ## 获取产品警报
    ```python
    get_alerts(product="Red Hat Enterprise Linux")
    ```

    ## 获取文档内容
    ```python
    get_document(document_url="https://access.redhat.com/solutions/12345")
    ```
    """
