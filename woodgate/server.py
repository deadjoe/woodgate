"""
MCP服务器模块 - 实现Model Context Protocol服务器
"""

import logging
from typing import List, Dict, Any, Optional

from mcp.server.fastmcp import FastMCP

from .core.browser import initialize_browser
from .core.auth import login_to_redhat_portal
from .core.search import perform_search, get_product_alerts, get_document_content
from .core.utils import setup_logging
from .config import get_credentials, get_available_products, get_document_types

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

# 创建MCP服务器
mcp = FastMCP("Woodgate", description="Red Hat客户门户搜索工具")


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
    logger.info(f"执行搜索: '{query}'")

    browser = await initialize_browser()
    try:
        username, password = get_credentials()
        login_success = await login_to_redhat_portal(browser, username, password)
        if not login_success:
            return {"error": "登录失败，请检查凭据"}

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
    finally:
        await browser.quit()


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
            return {"error": "登录失败，请检查凭据"}

        alerts = await get_product_alerts(browser, product)
        return alerts
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
