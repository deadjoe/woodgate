"""
MCP服务器模块 - 实现Model Context Protocol服务器（同步版本）
使用Playwright替代Selenium实现更高效的浏览器自动化
"""

import os
import sys
import logging
import subprocess
import importlib.util
import traceback
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple

# 环境变量应该在运行时设置，而不是硬编码在代码中
# 例如: export REDHAT_USERNAME="your_username" && export REDHAT_PASSWORD="your_password"

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 检查并安装必要的依赖
required_packages = ["playwright", "httpx"]

for package in required_packages:
    if importlib.util.find_spec(package) is None:
        logger.info(f"正在安装 {package}...")
        try:
            # 尝试使用uv安装
            try:
                subprocess.check_call(["uv", "pip", "install", package])
                logger.info(f"{package} 使用uv安装成功")

                # 如果是playwright，还需要安装浏览器
                if package == "playwright":
                    logger.info("安装Playwright浏览器...")
                    try:
                        subprocess.check_call(["playwright", "install", "chromium"])
                        logger.info("Playwright浏览器安装成功")
                    except Exception as e:
                        logger.warning(f"安装Playwright浏览器失败: {e}")
                        logger.warning("尝试使用Python模块安装浏览器...")
                        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
                        logger.info("Playwright浏览器安装成功")
            except Exception as e1:
                logger.warning(f"使用uv安装 {package} 失败: {e1}")
                # 尝试使用pip安装
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    logger.info(f"{package} 使用pip安装成功")

                    # 如果是playwright，还需要安装浏览器
                    if package == "playwright":
                        logger.info("安装Playwright浏览器...")
                        try:
                            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
                            logger.info("Playwright浏览器安装成功")
                        except Exception as e:
                            logger.warning(f"安装Playwright浏览器失败: {e}")
                except Exception as e2:
                    logger.warning(f"使用pip安装 {package} 失败: {e2}")
                    # 尝试使用系统pip安装
                    subprocess.check_call(["pip", "install", package])
                    logger.info(f"{package} 使用系统pip安装成功")

                    # 如果是playwright，还需要安装浏览器
                    if package == "playwright":
                        logger.info("安装Playwright浏览器...")
                        try:
                            subprocess.check_call(["playwright", "install", "chromium"])
                            logger.info("Playwright浏览器安装成功")
                        except Exception as e:
                            logger.warning(f"安装Playwright浏览器失败: {e}")
        except Exception as e:
            logger.error(f"安装 {package} 失败: {e}")
            logger.error("继续执行，但可能会导致功能不正常")

# 导入必要的模块
try:
    from mcp.server.fastmcp import FastMCP
    from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext, Playwright
except ImportError as e:
    logger.error(f"导入错误: {e}")
    raise

# 创建MCP服务器
mcp = FastMCP("Woodgate", description="Red Hat客户门户搜索工具")

# 配置
REDHAT_PORTAL_URL = "https://access.redhat.com"
REDHAT_LOGIN_URL = "https://sso.redhat.com/auth/realms/redhat-external/login-actions/authenticate"
REDHAT_SEARCH_URL = "https://access.redhat.com/search"
REDHAT_DIRECT_LOGIN_URL = "https://access.redhat.com/login"
ALERTS_BASE_URL = "https://access.redhat.com/security/security-updates/"


# 获取凭据
def get_credentials():
    """从环境变量获取Red Hat客户门户凭据"""
    username = os.environ.get("REDHAT_USERNAME")
    password = os.environ.get("REDHAT_PASSWORD")

    if not username or not password:
        raise ValueError("未设置REDHAT_USERNAME或REDHAT_PASSWORD环境变量")

    return username, password


# 初始化浏览器 - 同步版本
def initialize_browser() -> Tuple[Playwright, Browser, BrowserContext, Page]:
    """
    初始化Playwright浏览器 - 同步版本

    Returns:
        Tuple[Playwright, Browser, BrowserContext, Page]: 包含Playwright实例、浏览器实例、浏览器上下文和页面的元组
    """
    logger.debug("初始化Playwright浏览器...")

    try:
        # 启动Playwright
        playwright = sync_playwright().start()

        # 启动浏览器，配置优化选项
        browser = playwright.chromium.launch(
            headless=True,  # 启用无头模式，不显示浏览器窗口，提高运行效率
            args=[
                "--no-sandbox",  # 禁用沙箱，解决某些环境下的权限问题
                "--disable-dev-shm-usage",  # 解决在低内存环境中的崩溃问题
                "--disable-extensions",  # 禁用扩展，减少资源占用和干扰
                "--disable-gpu",  # 禁用GPU加速，提高在服务器环境下的兼容性
                "--disable-notifications",  # 禁用通知，避免弹窗干扰
            ]
        )

        # 创建浏览器上下文，配置视口大小和其他选项
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},  # 设置窗口大小，模拟标准显示器分辨率
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",  # 设置用户代理
            ignore_https_errors=True,  # 忽略HTTPS错误，提高兼容性
            java_script_enabled=True,  # 启用JavaScript
            has_touch=False,  # 禁用触摸，模拟桌面环境
        )

        # 创建页面
        page = context.new_page()

        # 配置页面选项
        page.route("**/*.{png,jpg,jpeg,gif,svg}", lambda route: route.abort())  # 阻止加载图片，提高性能
        page.set_default_timeout(20000)  # 设置默认超时时间为20秒
        page.set_default_navigation_timeout(30000)  # 设置导航超时时间为30秒

        logger.debug("浏览器初始化完成")
        return playwright, browser, context, page
    except Exception as e:
        logger.error(f"浏览器初始化失败: {e}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        raise


# 关闭浏览器 - 同步版本
def close_browser(
    playwright: Optional[Playwright] = None,
    browser: Optional[Browser] = None,
    context: Optional[BrowserContext] = None,
    page: Optional[Page] = None
) -> None:
    """
    安全关闭浏览器及相关资源 - 同步版本

    Args:
        playwright: Playwright实例
        browser: 浏览器实例
        context: 浏览器上下文
        page: 页面实例
    """
    try:
        if page:
            page.close()
            logger.debug("页面已关闭")

        if context:
            context.close()
            logger.debug("浏览器上下文已关闭")

        if browser:
            browser.close()
            logger.debug("浏览器已关闭")

        if playwright:
            playwright.stop()
            logger.debug("Playwright已停止")

        logger.debug("浏览器资源已完全释放")
    except Exception as e:
        logger.warning(f"关闭浏览器时出错: {e}")
        logger.debug(f"错误堆栈: {traceback.format_exc()}")


# 处理Cookie弹窗 - 同步版本
def handle_cookie_popup(page: Page, timeout: float = 1.0) -> bool:
    """
    处理网页上出现的cookie或隐私弹窗 - 同步版本

    Args:
        page (Page): Playwright页面实例
        timeout (float, optional): 等待弹窗出现的超时时间(秒). Defaults to 1.0.

    Returns:
        bool: 如果成功处理了弹窗返回True，否则返回False
    """
    logger.debug("检查是否存在cookie通知...")

    try:
        # 设置较短的超时时间，避免在没有弹窗的情况下等待太久
        original_timeout = page.get_default_timeout()
        page.set_default_timeout(timeout * 1000)  # 转换为毫秒

        # 优化：使用更高效的CSS选择器，减少DOM查询次数
        popup_selectors = [
            "#truste-consent-button",  # Red Hat特有的
            "#onetrust-banner-sdk",  # 最常见的
            ".pf-c-modal-box",  # Red Hat特有的
            "[role='dialog'][aria-modal='true']",  # 通用备选
            ".cookie-banner",  # 通用cookie横幅
            "#cookie-notice",  # 另一种常见的cookie通知
        ]

        # 检查是否存在cookie通知
        for selector in popup_selectors:
            try:
                # 使用waitForSelector而不是等待元素可见，提高效率
                cookie_notice = page.wait_for_selector(selector, timeout=timeout * 1000, state="attached")
                if cookie_notice:
                    logger.debug(f"发现cookie通知，使用选择器: {selector}")
                    cookie_notice.click()
                    logger.debug("已点击关闭按钮")
                    # 恢复默认超时时间
                    page.set_default_timeout(original_timeout)
                    return True
            except Exception:
                continue

        # 尝试通过文本内容查找按钮
        for button_text in ["Accept", "I agree", "Close", "OK", "接受", "同意", "关闭"]:
            try:
                # 使用text=按钮文本定位
                button = page.get_by_text(button_text, exact=False).first()
                if button:
                    button.click(timeout=1000)
                    logger.debug(f"找到并点击了文本为'{button_text}'的按钮")
                # 恢复默认超时时间
                page.set_default_timeout(original_timeout)
                return True
            except Exception:
                continue

        # 恢复默认超时时间
        page.set_default_timeout(original_timeout)
        logger.debug("未发现cookie通知")
        return False

    except Exception as e:
        # 恢复默认超时时间
        page.set_default_timeout(30000)
        logger.debug(f"处理cookie通知时出错: {e}")
        return False


# 登录到Red Hat客户门户 - 同步版本
def login_to_redhat_portal(page: Page, context: BrowserContext, username: str, password: str) -> bool:
    """
    登录到Red Hat客户门户 - 同步版本

    Args:
        page (Page): Playwright页面实例
        context (BrowserContext): Playwright浏览器上下文
        username (str): Red Hat账号用户名
        password (str): Red Hat账号密码

    Returns:
        bool: 登录成功返回True，否则返回False
    """
    try:
        # 访问Red Hat客户门户
        page.goto(REDHAT_PORTAL_URL, wait_until="networkidle")
        logger.debug("已加载Red Hat客户门户首页")

        # 处理Cookie弹窗
        handle_cookie_popup(page)

        # 点击登录按钮
        try:
            login_button = page.get_by_text("Log In", exact=True).first()
            if login_button:
                login_button.click()
                logger.debug("已点击登录按钮")
            else:
                # 尝试使用链接选择器
                login_locator = page.locator("a[href*='login']")
                if login_locator.count() > 0:
                    login_locator.first().click()
                    logger.debug("已点击登录链接")
        except Exception as e:
            logger.debug(f"点击登录按钮时出错: {e}，可能已经在登录页面")
            # 可能已经在登录页面，尝试直接访问登录页面
            page.goto(REDHAT_DIRECT_LOGIN_URL, wait_until="networkidle")

        # 输入用户名
        username_field = page.wait_for_selector("#username", state="visible", timeout=10000)
        if username_field:
            username_field.fill("")  # 清空
            username_field.fill(username)  # 输入
            logger.debug("已输入用户名")
        else:
            logger.warning("未找到用户名输入框")
            return False

        # 点击下一步按钮（如果存在）
        try:
            next_button = page.wait_for_selector("#login-show-step2", state="visible", timeout=3000)
            if next_button:
                next_button.click()
                logger.debug("已点击下一步按钮")
        except Exception:
            logger.debug("未找到下一步按钮，可能是单步登录页面")

        # 输入密码
        password_field = page.wait_for_selector("#password", state="visible", timeout=10000)
        if password_field:
            password_field.fill("")  # 清空
            password_field.fill(password)  # 输入
            logger.debug("已输入密码")
        else:
            logger.warning("未找到密码输入框")
            return False

        # 点击登录按钮
        login_button = page.wait_for_selector("#kc-login", state="visible", timeout=5000)
        if login_button:
            login_button.click()
            logger.debug("已点击登录按钮")
        else:
            logger.warning("未找到登录按钮")
            return False

        # 等待登录完成
        try:
            page.wait_for_selector(".pf-c-page__header", state="visible", timeout=20000)
            logger.debug("登录成功！已检测到页面头部")
            return True
        except Exception as e:
            logger.error(f"等待登录完成时出错: {e}")

            # 检查是否有错误消息
            try:
                error_selector = ".kc-feedback-text, .alert-error, .pf-c-alert__title"
                error_element = page.wait_for_selector(error_selector, state="visible", timeout=3000)
                if error_element:
                    error_text = error_element.text_content()
                    logger.error(f"登录失败: {error_text}")
            except Exception:
                pass

            return False

    except Exception as e:
        logger.error(f"登录过程中出错: {e}")
        logger.debug(f"错误堆栈: {traceback.format_exc()}")
        return False


# 执行搜索 - 同步版本
def perform_search(
    page: Page, query: str, products=None, doc_types=None, page_num: int = 1, rows: int = 20, sort_by: str = "relevant"
) -> List[Dict[str, Any]]:
    """
    在Red Hat客户门户执行搜索 - 同步版本

    Args:
        page (Page): Playwright页面实例
        query (str): 搜索关键词
        products (List[str], optional): 要搜索的产品列表. Defaults to None.
        doc_types (List[str], optional): 文档类型列表. Defaults to None.
        page_num (int, optional): 页码. Defaults to 1.
        rows (int, optional): 每页结果数. Defaults to 20.
        sort_by (str, optional): 排序方式. Defaults to "relevant".

    Returns:
        List[Dict[str, Any]]: 搜索结果列表
    """
    try:
        # 构建搜索URL
        encoded_query = urllib.parse.quote(query)
        search_url = f"{REDHAT_SEARCH_URL}?q={encoded_query}&p={page_num}&rows={rows}&sort={sort_by}"

        # 添加产品过滤
        if products:
            for product in products:
                encoded_product = urllib.parse.quote(product)
                search_url += f"&product={encoded_product}"

        # 添加文档类型过滤
        if doc_types:
            for doc_type in doc_types:
                encoded_doc_type = urllib.parse.quote(doc_type)
                search_url += f"&documentKind={encoded_doc_type}"

        logger.debug(f"搜索URL: {search_url}")

        # 访问搜索页面
        page.goto(search_url, wait_until="networkidle")
        logger.debug("已加载搜索页面")

        # 处理可能出现的Cookie弹窗
        handle_cookie_popup(page)

        # 等待搜索结果加载
        try:
            page.wait_for_selector(".pf-c-page__main-section", state="visible", timeout=20000)
            logger.debug("页面主体已加载")
        except Exception as e:
            logger.error(f"等待页面加载时出错: {e}")
            return []

        # 检查是否有搜索结果
        try:
            result_count = page.query_selector_all(".pf-c-card, .search-result")
            if not result_count:
                logger.debug("未找到搜索结果")
                return []
            logger.debug(f"找到 {len(result_count)} 个搜索结果")
        except Exception as e:
            logger.error(f"检查搜索结果时出错: {e}")
            return []

        # 提取搜索结果
        results = []
        result_elements = page.query_selector_all(".pf-c-card, .search-result")

        for element in result_elements:
            try:
                # 提取标题和URL
                title_element = element.query_selector("h2 a, .pf-c-title a")
                if not title_element:
                    continue

                title = title_element.text_content()
                title = title.strip() if title else "未知标题"
                url = title_element.get_attribute("href")

                # 提取摘要
                summary = "无摘要"
                summary_element = element.query_selector(
                    ".co-search-result__description, .search-result-content, .pf-c-card__body"
                )
                if summary_element:
                    summary_text = summary_element.text_content()
                    summary = summary_text.strip() if summary_text else "无摘要"

                # 提取文档类型
                doc_type = "未知类型"
                doc_type_element = element.query_selector(
                    ".co-search-result__kind, .search-result-info span, .pf-c-label"
                )
                if doc_type_element:
                    doc_type_text = doc_type_element.text_content()
                    doc_type = doc_type_text.strip() if doc_type_text else "未知类型"

                # 提取最后更新时间
                last_updated = "未知日期"
                date_element = element.query_selector(
                    ".co-search-result__date, .search-result-info time, .pf-c-label[data-testid='date']"
                )
                if date_element:
                    date_text = date_element.text_content()
                    last_updated = date_text.strip() if date_text else "未知日期"

                results.append(
                    {
                        "title": title,
                        "url": url,
                        "summary": summary,
                        "doc_type": doc_type,
                        "last_updated": last_updated,
                    }
                )
            except Exception as e:
                logger.error(f"提取搜索结果时出错: {e}")
                logger.debug(f"错误堆栈: {traceback.format_exc()}")
                continue

        logger.debug(f"成功提取 {len(results)} 个搜索结果")
        return results
    except Exception as e:
        logger.error(f"执行搜索时出错: {e}")
        logger.debug(f"错误堆栈: {traceback.format_exc()}")
        return []


# 获取产品警报 - 同步版本
def get_product_alerts(page: Page, product: str) -> List[Dict[str, Any]]:
    """
    获取特定产品的警报信息 - 同步版本

    Args:
        page (Page): Playwright页面实例
        product (str): 产品名称

    Returns:
        List[Dict[str, Any]]: 警报信息列表
    """
    try:
        # 构建警报URL
        encoded_product = urllib.parse.quote(product)
        alerts_url = f"{REDHAT_PORTAL_URL}/products/{encoded_product}/alerts"
        logger.debug(f"警报URL: {alerts_url}")

        # 访问警报页面
        page.goto(alerts_url, wait_until="networkidle")
        logger.debug("已加载警报页面")

        # 处理可能出现的Cookie弹窗
        handle_cookie_popup(page)

        # 等待警报加载
        try:
            page.wait_for_selector(".pf-c-page__main-section", state="visible", timeout=20000)
            logger.debug("页面主体已加载")
        except Exception as e:
            logger.error(f"等待页面加载时出错: {e}")
            return []

        # 提取警报信息
        alerts = []
        alert_elements = page.query_selector_all(".pf-c-card, .portal-advisory")
        logger.debug(f"找到 {len(alert_elements)} 个警报元素")

        for element in alert_elements:
            try:
                # 提取标题和URL
                title_element = element.query_selector("h2 a, .pf-c-title a")
                if not title_element:
                    continue

                title = title_element.text_content()
                title = title.strip() if title else "未知标题"
                url = title_element.get_attribute("href")

                # 提取摘要
                summary = "无摘要"
                summary_element = element.query_selector(
                    ".co-alert__description, .portal-advisory-synopsis, .pf-c-card__body"
                )
                if summary_element:
                    summary_text = summary_element.text_content()
                    summary = summary_text.strip() if summary_text else "无摘要"

                # 提取严重性
                severity = "未知严重性"
                severity_element = element.query_selector(
                    ".co-alert__severity, .security-severity, .pf-c-label"
                )
                if severity_element:
                    severity_text = severity_element.text_content()
                    severity = severity_text.strip() if severity_text else "未知严重性"

                # 提取发布日期
                published_date = "未知日期"
                date_element = element.query_selector(
                    ".co-alert__date, .portal-advisory-date, time"
                )
                if date_element:
                    date_text = date_element.text_content()
                    published_date = date_text.strip() if date_text else "未知日期"

                alerts.append(
                    {
                        "title": title,
                        "url": url,
                        "summary": summary,
                        "severity": severity,
                        "published_date": published_date,
                    }
                )
            except Exception as e:
                logger.error(f"提取警报信息时出错: {e}")
                logger.debug(f"错误堆栈: {traceback.format_exc()}")
                continue

        logger.debug(f"成功提取 {len(alerts)} 个警报")
        return alerts
    except Exception as e:
        logger.error(f"获取产品警报时出错: {e}")
        logger.debug(f"错误堆栈: {traceback.format_exc()}")
        return []


# 获取文档内容 - 同步版本
def get_document_content(page: Page, document_url: str) -> Dict[str, Any]:
    """
    获取特定文档的详细内容 - 同步版本

    Args:
        page (Page): Playwright页面实例
        document_url (str): 文档URL

    Returns:
        Dict[str, Any]: 文档内容
    """
    try:
        # 访问文档页面
        page.goto(document_url, wait_until="networkidle")
        logger.debug("已加载文档页面")

        # 处理可能出现的Cookie弹窗
        handle_cookie_popup(page)

        # 等待文档加载
        try:
            page.wait_for_selector(".pf-c-page__main-section", state="visible", timeout=20000)
            logger.debug("页面主体已加载")
        except Exception as e:
            logger.error(f"等待页面加载时出错: {e}")
            return {"error": "无法加载文档内容"}

        # 提取文档标题
        title = "未知标题"
        title_element = page.query_selector("h1, .pf-c-title")
        if title_element:
            title_text = title_element.text_content()
            title = title_text.strip() if title_text else "未知标题"

        # 提取文档内容
        content = "无法提取文档内容"
        content_element = page.query_selector(".pf-c-content, .field-item, article")
        if content_element:
            content_text = content_element.text_content()
            content = content_text.strip() if content_text else "无法提取文档内容"

        # 提取文档元数据
        metadata = {}
        try:
            # 尝试提取各种可能的元数据字段
            metadata_fields = page.query_selector_all(".field, .pf-c-description-list__group")

            for field in metadata_fields:
                try:
                    label_element = field.query_selector(".field-label, .pf-c-description-list__term")
                    value_element = field.query_selector(".field-item, .pf-c-description-list__description")

                    if label_element and value_element:
                        label_text = label_element.text_content()
                        value_text = value_element.text_content()

                        label = label_text.strip().rstrip(":") if label_text else ""
                        value = value_text.strip() if value_text else ""

                        if label and value:
                            metadata[label] = value
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"提取文档元数据时出错: {e}")

        return {"title": title, "url": document_url, "content": content, "metadata": metadata}
    except Exception as e:
        logger.error(f"获取文档内容时出错: {e}")
        logger.debug(f"错误堆栈: {traceback.format_exc()}")
        return {"title": "错误", "url": document_url, "content": f"获取文档内容时出错: {str(e)}"}


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
        "Red Hat AMQ",
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
        "Troubleshoot",
    ]


@mcp.tool()
def search(
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
    logger.debug(
        f"搜索函数开始执行，参数: query='{query}', products={products}, doc_types={doc_types}, page={page}, rows={rows}, sort_by='{sort_by}'"
    )

    playwright = None
    browser = None
    context = None
    page_obj = None

    try:
        logger.debug("初始化浏览器...")
        playwright, browser, context, page_obj = initialize_browser()
        logger.debug("浏览器初始化成功")

        logger.debug("获取凭据...")
        username, password = get_credentials()
        logger.debug(f"凭据获取成功: username='{username}'")

        logger.debug("登录到Red Hat客户门户...")
        login_success = login_to_redhat_portal(page_obj, context, username, password)
        logger.debug(f"登录结果: {login_success}")

        if not login_success:
            logger.error("登录失败，请检查凭据")
            return [{"error": "登录失败，请检查凭据"}]

        logger.debug("执行搜索...")
        results = perform_search(
            page_obj,
            query=query,
            products=products or [],
            doc_types=doc_types or [],
            page_num=page,
            rows=rows,
            sort_by=sort_by,
        )
        logger.debug(f"搜索完成，找到 {len(results)} 条结果")
        return results
    except Exception as e:
        logger.error(f"搜索过程中出错: {e}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return [{"error": f"搜索过程中出错: {str(e)}"}]
    finally:
        try:
            # 安全地关闭浏览器
            logger.debug("关闭浏览器...")
            close_browser(playwright, browser, context, page_obj)
            logger.debug("浏览器已关闭")
        except Exception as e:
            logger.warning(f"关闭浏览器时出错: {e}")


@mcp.tool()
def get_alerts(product: str) -> List[Dict[str, Any]]:
    """
    获取特定产品的警报信息

    Args:
        product: 产品名称，例如 "Red Hat Enterprise Linux"

    Returns:
        警报信息列表
    """
    logger.info(f"获取产品警报: '{product}'")

    playwright = None
    browser = None
    context = None
    page_obj = None

    try:
        playwright, browser, context, page_obj = initialize_browser()
        username, password = get_credentials()
        login_success = login_to_redhat_portal(page_obj, context, username, password)
        if not login_success:
            return [{"error": "登录失败，请检查凭据"}]

        alerts = get_product_alerts(page_obj, product)
        return alerts
    except Exception as e:
        logger.error(f"获取警报过程中出错: {e}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return [{"error": f"获取警报过程中出错: {str(e)}"}]
    finally:
        try:
            # 安全地关闭浏览器
            close_browser(playwright, browser, context, page_obj)
        except Exception as e:
            logger.warning(f"关闭浏览器时出错: {e}")


@mcp.tool()
def get_document(document_url: str) -> Dict[str, Any]:
    """
    获取特定文档的详细内容

    Args:
        document_url: 文档URL

    Returns:
        文档内容
    """
    logger.info(f"获取文档内容: {document_url}")

    playwright = None
    browser = None
    context = None
    page_obj = None

    try:
        playwright, browser, context, page_obj = initialize_browser()
        username, password = get_credentials()
        login_success = login_to_redhat_portal(page_obj, context, username, password)
        if not login_success:
            return {"error": "登录失败，请检查凭据"}

        document = get_document_content(page_obj, document_url)
        return document
    except Exception as e:
        logger.error(f"获取文档内容过程中出错: {e}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return {"error": f"获取文档内容过程中出错: {str(e)}"}
    finally:
        try:
            # 安全地关闭浏览器
            close_browser(playwright, browser, context, page_obj)
        except Exception as e:
            logger.warning(f"关闭浏览器时出错: {e}")


@mcp.resource("config://products")
def available_products() -> List[str]:
    """获取可用的产品列表"""
    return get_available_products()


@mcp.resource("config://doc-types")
def document_types() -> List[str]:
    """获取可用的文档类型"""
    return get_document_types()


@mcp.resource("config://search-params")
def search_params() -> Dict[str, Any]:
    """获取搜索参数配置"""
    return {
        "sort_options": [
            {"value": "relevant", "label": "相关性"},
            {"value": "lastModifiedDate desc", "label": "最新更新"},
            {"value": "lastModifiedDate asc", "label": "最早更新"},
            {"value": "portal_publication_date desc", "label": "最新发布"},
            {"value": "portal_publication_date asc", "label": "最早发布"},
        ],
        "default_rows": 20,
        "max_rows": 100,
        "products": get_available_products(),
        "doc_types": get_document_types(),
    }


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
