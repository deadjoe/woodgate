"""
MCP服务器模块 - 实现Model Context Protocol服务器
"""

import logging
from typing import Any, Dict, List, Optional, Union

from .config import get_available_products, get_credentials, get_document_types
from .core.auth import login_to_redhat_portal
from .core.browser import initialize_browser
from .core.search import get_document_content, get_product_alerts, perform_search

# 由于 MCP 导入问题，使用模拟的 MCP 类
try:
    from mcp import MCP  # type: ignore
except ImportError:
    from .mcp_mock import MCP

logger = logging.getLogger(__name__)
mcp = MCP()


class SearchResult:
    """搜索结果类型"""

    def __init__(
        self,
        title: str,
        url: str,
        description: Optional[str] = None,
        doc_type: Optional[str] = None,
        last_modified: Optional[str] = None,
        score: Optional[float] = None,
    ):
        self.title = title
        self.url = url
        self.description = description
        self.doc_type = doc_type
        self.last_modified = last_modified
        self.score = score


class AlertInfo:
    """警报信息类型"""

    def __init__(
        self,
        title: str,
        severity: str,
        issued: Optional[str] = None,
        cve: Optional[str] = None,
        url: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.title = title
        self.severity = severity
        self.issued = issued
        self.cve = cve
        self.url = url
        self.description = description


class DocumentContent:
    """文档内容类型"""

    def __init__(
        self,
        title: str,
        content: str,
        url: str,
        doc_type: Optional[str] = None,
        last_modified: Optional[str] = None,
    ):
        self.title = title
        self.content = content
        self.url = url
        self.doc_type = doc_type
        self.last_modified = last_modified


class ErrorResponse:
    """错误响应类型"""

    def __init__(self, error: str):
        self.error = error


# 组合类型
SearchResults = List[Union[SearchResult, ErrorResponse]]
AlertResults = List[Union[AlertInfo, ErrorResponse]]
DocumentResult = Union[DocumentContent, ErrorResponse]


@mcp.tool()
async def search(
    query: str,
    products: Optional[List[str]] = None,
    doc_types: Optional[List[str]] = None,
    page_num: int = 1,
    rows: int = 20,
    sort_by: str = "relevant",
) -> SearchResults:
    """
    在Red Hat客户门户中执行搜索

    Args:
        query: 搜索关键词
        products: 要搜索的产品列表，例如 ["Red Hat Enterprise Linux", "Red Hat OpenShift"]
        doc_types: 文档类型列表，例如 ["Solution", "Article"]
        page_num: 页码
        rows: 每页结果数
        sort_by: 排序方式，可选值: "relevant", "lastModifiedDate desc", "lastModifiedDate asc"

    Returns:
        搜索结果列表
    """
    logger.info(f"执行搜索: '{query}'")

    browser_resources = None
    try:
        # 并行初始化浏览器和获取凭据
        import asyncio

        # 使用asyncio.to_thread将同步函数转换为异步操作
        browser_task = asyncio.create_task(initialize_browser())
        credentials_task = asyncio.to_thread(get_credentials)

        # 等待两个任务完成
        browser_resources, credentials_result = await asyncio.gather(browser_task, credentials_task)
        username, password = credentials_result

        # 解包浏览器资源
        playwright, browser, context, page_obj = browser_resources
        page = page_obj  # 重命名变量，避免与函数参数冲突

        # 检查浏览器初始化是否成功
        if page is None:
            logger.error("浏览器初始化失败")
            return [ErrorResponse(error="浏览器初始化失败，无法执行搜索")]

        # 执行登录
        login_success = await login_to_redhat_portal(page, context, username, password)
        if not login_success:
            return [ErrorResponse(error="登录失败，请检查凭据")]

        # 执行搜索
        results = await perform_search(
            page,
            query=query,
            products=products or [],
            doc_types=doc_types or [],
            page_num=page_num,
            rows=rows,
            sort_by=sort_by,
        )
        # 将结果转换为SearchResult对象列表
        search_results: List[Union[SearchResult, ErrorResponse]] = []
        for result in results:
            if "error" in result:
                search_results.append(ErrorResponse(error=result["error"]))
            else:
                search_results.append(
                    SearchResult(
                        title=result.get("title", "未知标题"),
                        url=result.get("url", ""),
                        description=result.get("summary", ""),
                        doc_type=result.get("doc_type", ""),
                        last_modified=result.get("last_updated", ""),
                    )
                )
        return search_results
    except Exception as e:
        logger.error(f"搜索过程中出错: {e}")
        import traceback

        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return [ErrorResponse(error=f"搜索过程中出错: {str(e)}")]
    finally:
        try:
            # 安全地关闭浏览器
            if browser_resources:
                playwright, browser, context, page_obj = browser_resources
                from .core.browser import close_browser

                await close_browser(playwright, browser, context, page_obj)
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

    browser_resources = None
    try:
        # 并行初始化浏览器和获取凭据
        import asyncio

        # 使用asyncio.to_thread将同步函数转换为异步操作
        browser_task = asyncio.create_task(initialize_browser())
        credentials_task = asyncio.to_thread(get_credentials)

        # 等待两个任务完成
        browser_resources, credentials_result = await asyncio.gather(browser_task, credentials_task)
        username, password = credentials_result

        # 解包浏览器资源
        playwright, browser, context, page_obj = browser_resources
        page = page_obj  # 重命名变量，避免与函数参数冲突

        # 检查浏览器初始化是否成功
        if page is None:
            logger.error("浏览器初始化失败")
            return [ErrorResponse(error="浏览器初始化失败，无法获取警报")]

        # 执行登录
        login_success = await login_to_redhat_portal(page, context, username, password)
        if not login_success:
            return [ErrorResponse(error="登录失败，请检查凭据")]

        # 获取产品警报
        alerts_data = await get_product_alerts(page, product)
        # 将结果转换为AlertInfo对象列表
        alert_results: List[Union[AlertInfo, ErrorResponse]] = []
        for alert in alerts_data:
            if "error" in alert:
                alert_results.append(ErrorResponse(error=alert["error"]))
            else:
                alert_results.append(
                    AlertInfo(
                        title=alert.get("title", "未知警报"),
                        severity=alert.get("severity", "未知"),
                        issued=alert.get("issued", ""),
                        cve=alert.get("cve", ""),
                        url=alert.get("url", ""),
                        description=alert.get("description", ""),
                    )
                )
        return alert_results
    except Exception as e:
        logger.error(f"获取警报过程中出错: {e}")
        import traceback

        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return [ErrorResponse(error=f"获取警报过程中出错: {str(e)}")]
    finally:
        try:
            # 安全地关闭浏览器
            if browser_resources:
                playwright, browser, context, page_obj = browser_resources
                from .core.browser import close_browser

                await close_browser(playwright, browser, context, page_obj)
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

    browser_resources = None
    try:
        # 并行初始化浏览器和获取凭据
        import asyncio

        # 使用asyncio.to_thread将同步函数转换为异步操作
        browser_task = asyncio.create_task(initialize_browser())
        credentials_task = asyncio.to_thread(get_credentials)

        # 等待两个任务完成
        browser_resources, credentials_result = await asyncio.gather(browser_task, credentials_task)
        username, password = credentials_result

        # 解包浏览器资源
        playwright, browser, context, page_obj = browser_resources
        page = page_obj  # 重命名变量，避免与函数参数冲突

        # 检查浏览器初始化是否成功
        if page is None:
            logger.error("浏览器初始化失败")
            return ErrorResponse(error="浏览器初始化失败，无法获取文档内容")

        # 执行登录
        login_success = await login_to_redhat_portal(page, context, username, password)
        if not login_success:
            return ErrorResponse(error="登录失败，请检查凭据")

        # 获取文档内容
        document_data = await get_document_content(page, document_url)
        # 将结果转换为DocumentContent对象
        if "error" in document_data:
            return ErrorResponse(error=document_data["error"])
        else:
            return DocumentContent(
                title=document_data.get("title", "未知标题"),
                content=document_data.get("content", ""),
                url=document_url,
                doc_type=document_data.get("metadata", {}).get("Document Type", ""),
                last_modified=document_data.get("metadata", {}).get("Last Modified", ""),
            )
    except Exception as e:
        logger.error(f"获取文档内容过程中出错: {e}")
        import traceback

        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return ErrorResponse(error=f"获取文档内容过程中出错: {str(e)}")
    finally:
        try:
            # 安全地关闭浏览器
            if browser_resources:
                playwright, browser, context, page_obj = browser_resources
                from .core.browser import close_browser

                await close_browser(playwright, browser, context, page_obj)
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
    - **page_num**: 页码，默认为1
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
        page_num=1,
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
