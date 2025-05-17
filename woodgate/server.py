"""
MCP服务器模块 - 实现Model Context Protocol服务器
"""

import logging
from typing import Any, Dict, List, Optional, TypedDict, Union

from mcp.server.fastmcp import FastMCP

# 定义结构化类型
class SearchResult(TypedDict):
    """搜索结果类型"""
    title: str
    url: str
    description: Optional[str]
    doc_type: Optional[str]
    last_modified: Optional[str]
    score: Optional[float]

class AlertInfo(TypedDict):
    """警报信息类型"""
    title: str
    severity: str
    issued: Optional[str]
    cve: Optional[str]
    url: Optional[str]
    description: Optional[str]

class DocumentContent(TypedDict):
    """文档内容类型"""
    title: str
    content: str
    url: str
    doc_type: Optional[str]
    last_modified: Optional[str]

class ErrorResponse(TypedDict):
    """错误响应类型"""
    error: str

# 组合类型
SearchResults = List[Union[SearchResult, ErrorResponse]]
AlertResults = List[Union[AlertInfo, ErrorResponse]]
DocumentResult = Union[DocumentContent, ErrorResponse]

from .config import get_available_products, get_credentials, get_document_types
from .core.auth import login_to_redhat_portal
from .core.browser import initialize_browser
from .core.search import get_document_content, get_product_alerts, perform_search
from .core.utils import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

# 创建MCP服务器
mcp = FastMCP(
    "Woodgate",
    description="Red Hat客户门户搜索工具",
    version="1.0.0",  # 添加版本号
    host="0.0.0.0",  # 默认监听所有接口
    port=8000,  # 默认端口
    log_level="INFO",  # 默认日志级别
    dependencies=["playwright", "httpx"],  # 声明依赖
    stateless_http=True,  # 支持无状态HTTP传输
)


@mcp.tool()
async def search(
    query: str,
    products: Optional[List[str]] = None,
    doc_types: Optional[List[str]] = None,
    page: int = 1,
    rows: int = 20,
    sort_by: str = "relevant",
) -> SearchResults:
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
    logger.info(f"执行搜索: '{query}'")

    browser = None
    try:
        # 并行初始化浏览器和获取凭据
        import asyncio

        # 使用asyncio.to_thread将同步函数转换为异步操作
        browser_task = asyncio.create_task(initialize_browser())
        credentials_task = asyncio.to_thread(get_credentials)

        # 等待两个任务完成
        browser, credentials_result = await asyncio.gather(browser_task, credentials_task)
        username, password = credentials_result

        # 检查浏览器初始化是否成功
        if browser is None:
            logger.error("浏览器初始化失败")
            return [{"error": "浏览器初始化失败，无法执行搜索"}]

        # 执行登录
        login_success = await login_to_redhat_portal(browser, username, password)
        if not login_success:
            return [{"error": "登录失败，请检查凭据"}]

        # 执行搜索
        results = await perform_search(
            browser,
            query=query,
            products=products or [],
            doc_types=doc_types or [],
            page=page,
            rows=rows,
            sort_by=sort_by,
        )
        return results
    except Exception as e:
        logger.error(f"搜索过程中出错: {e}")
        import traceback

        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return [{"error": f"搜索过程中出错: {str(e)}"}]
    finally:
        try:
            # 安全地关闭浏览器
            if browser:
                try:
                    await browser.quit()
                except Exception:
                    # 如果异步关闭失败，尝试同步关闭
                    browser.quit()
        except Exception as e:
            logger.warning(f"关闭浏览器时出错: {e}")


@mcp.tool()
async def get_alerts(product: str) -> AlertResults:
    """
    获取特定产品的警报信息

    Args:
        product: 产品名称，例如 "Red Hat Enterprise Linux"

    Returns:
        警报信息列表
    """
    logger.info(f"获取产品警报: '{product}'")

    browser = None
    try:
        # 并行初始化浏览器和获取凭据
        import asyncio

        # 使用asyncio.to_thread将同步函数转换为异步操作
        browser_task = asyncio.create_task(initialize_browser())
        credentials_task = asyncio.to_thread(get_credentials)

        # 等待两个任务完成
        browser, credentials_result = await asyncio.gather(browser_task, credentials_task)
        username, password = credentials_result

        # 检查浏览器初始化是否成功
        if browser is None:
            logger.error("浏览器初始化失败")
            return [{"error": "浏览器初始化失败，无法获取警报"}]

        # 执行登录
        login_success = await login_to_redhat_portal(browser, username, password)
        if not login_success:
            return [{"error": "登录失败，请检查凭据"}]

        # 获取产品警报
        alerts = await get_product_alerts(browser, product)
        return alerts
    except Exception as e:
        logger.error(f"获取警报过程中出错: {e}")
        import traceback

        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return [{"error": f"获取警报过程中出错: {str(e)}"}]
    finally:
        try:
            # 安全地关闭浏览器
            if browser:
                try:
                    await browser.quit()
                except Exception:
                    # 如果异步关闭失败，尝试同步关闭
                    browser.quit()
        except Exception as e:
            logger.warning(f"关闭浏览器时出错: {e}")


@mcp.tool()
async def get_document(document_url: str) -> DocumentResult:
    """
    获取特定文档的详细内容

    Args:
        document_url: 文档URL

    Returns:
        文档内容
    """
    logger.info(f"获取文档内容: {document_url}")

    browser = None
    try:
        # 并行初始化浏览器和获取凭据
        import asyncio

        # 使用asyncio.to_thread将同步函数转换为异步操作
        browser_task = asyncio.create_task(initialize_browser())
        credentials_task = asyncio.to_thread(get_credentials)

        # 等待两个任务完成
        browser, credentials_result = await asyncio.gather(browser_task, credentials_task)
        username, password = credentials_result

        # 检查浏览器初始化是否成功
        if browser is None:
            logger.error("浏览器初始化失败")
            return {"error": "浏览器初始化失败，无法获取文档内容"}

        # 执行登录
        login_success = await login_to_redhat_portal(browser, username, password)
        if not login_success:
            return {"error": "登录失败，请检查凭据"}

        # 获取文档内容
        document = await get_document_content(browser, document_url)
        return document
    except Exception as e:
        logger.error(f"获取文档内容过程中出错: {e}")
        import traceback

        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return {"error": f"获取文档内容过程中出错: {str(e)}"}
    finally:
        try:
            # 安全地关闭浏览器
            if browser:
                try:
                    await browser.quit()
                except Exception:
                    # 如果异步关闭失败，尝试同步关闭
                    browser.quit()
        except Exception as e:
            logger.warning(f"关闭浏览器时出错: {e}")


@mcp.resource("redhat://products")
def available_products() -> List[str]:
    """获取可用的产品列表"""
    return get_available_products()


@mcp.resource("redhat://doc-types")
def document_types() -> List[str]:
    """获取可用的文档类型"""
    return get_document_types()


@mcp.resource("redhat://search-params")
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
