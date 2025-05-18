"""
搜索模块 - 处理Red Hat客户门户的搜索功能
使用Playwright替代Selenium实现更高效的浏览器自动化
"""

import asyncio
import logging
import traceback
from typing import Any, Dict, List, Optional

from playwright.async_api import Error, Page, TimeoutError

from .utils import handle_cookie_popup, log_step

logger = logging.getLogger(__name__)

# Red Hat客户门户搜索URL
SEARCH_BASE_URL = "https://access.redhat.com/search/"
ALERTS_BASE_URL = "https://access.redhat.com/security/security-updates/"  # 已弃用，保留用于兼容性


async def perform_search(
    page: Page,
    query: str,
    products: Optional[List[str]] = None,
    doc_types: Optional[List[str]] = None,
    page_num: int = 1,
    rows: int = 20,
    sort_by: str = "relevant",
) -> List[Dict[str, Any]]:
    """
    在Red Hat客户门户执行搜索

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
    log_step(f"执行搜索: '{query}'")

    # 构建搜索URL
    search_url = build_search_url(query, products, doc_types, page_num, rows, sort_by)
    log_step(f"搜索URL: {search_url}")

    try:
        # 访问搜索页面
        await page.goto(search_url, wait_until="domcontentloaded")
        log_step("已加载搜索页面")

        # 处理可能出现的Cookie弹窗
        await handle_cookie_popup(page)

        # 等待搜索结果加载
        try:
            await page.wait_for_selector(
                ".search-result, .pf-c-card", state="visible", timeout=15000
            )
            log_step("搜索结果已加载")
        except TimeoutError:
            log_step("等待搜索结果超时，可能没有结果或页面结构已更改")

            # 检查是否有"无结果"消息
            try:
                no_results = await page.query_selector(".no-results, .pf-c-empty-state")
                if no_results:
                    log_step("搜索没有返回结果")
                    return []
            except Exception:
                pass

            return []

        # 提取搜索结果
        return await extract_search_results(page)

    except Exception as e:
        logger.error(f"执行搜索时出错: {e}")
        logger.debug(f"错误堆栈: {traceback.format_exc()}")
        return []


def build_search_url(
    query: str,
    products: Optional[List[str]] = None,
    doc_types: Optional[List[str]] = None,
    page: int = 1,
    rows: int = 20,
    sort_by: str = "relevant",
) -> str:
    """
    构建Red Hat客户门户搜索URL，与老代码保持一致

    Args:
        query (str): 搜索关键词
        products (List[str], optional): 要搜索的产品列表. Defaults to None.
        doc_types (List[str], optional): 文档类型列表. Defaults to None.
        page (int, optional): 页码. Defaults to 1.
        rows (int, optional): 每页结果数. Defaults to 20.
        sort_by (str, optional): 排序方式. Defaults to "relevant".

    Returns:
        str: 构建好的搜索URL
    """
    # 构建基本URL
    base_url = f"{SEARCH_BASE_URL}?"

    # 构建参数字典
    params = {
        "q": query.replace(" ", "+"),
        "p": page,
        "rows": rows,
    }

    # 添加产品过滤器 - 使用%26连接多个产品，与老代码一致
    if products and len(products) > 0:
        product_param = "%26".join(p.replace(" ", "+") for p in products)
        params["product"] = product_param

    # 添加文档类型过滤器 - 使用%26连接多个文档类型，与老代码一致
    if doc_types and len(doc_types) > 0:
        doc_type_param = "%26".join(d.replace(" ", "+") for d in doc_types)
        params["documentKind"] = doc_type_param

    # 添加排序参数
    if sort_by:
        params["sort"] = sort_by.replace(" ", "+")

    # 构建完整URL
    url = base_url + "&".join(f"{k}={v}" for k, v in params.items())

    logger.debug(f"构建的搜索URL: {url}")
    return url


async def extract_search_results(page: Page) -> List[Dict[str, Any]]:
    """
    从搜索结果页面提取结果

    Args:
        page (Page): Playwright页面实例

    Returns:
        List[Dict[str, Any]]: 搜索结果列表
    """
    log_step("提取搜索结果...")
    results = []

    # 重试机制，处理可能的页面加载问题
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 查找所有搜索结果元素
            result_elements = await page.query_selector_all(".search-result, .pf-c-card")
            log_step(f"找到 {len(result_elements)} 个搜索结果")

            if not result_elements:
                # 检查是否有"无结果"消息
                no_results = await page.query_selector(".no-results, .pf-c-empty-state")
                if no_results:
                    log_step("搜索没有返回结果")
                    return []

                if attempt < max_retries - 1:
                    log_step(f"未找到结果元素，将在2秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    await asyncio.sleep(2)
                    await page.reload()
                    continue
                else:
                    log_step("多次尝试后仍未找到结果元素")
                    return []

            # 处理每个搜索结果
            for result in result_elements:
                try:
                    # 提取标题和链接
                    title_element = await result.query_selector("h2 a, .pf-c-title a")
                    if not title_element:
                        continue

                    title = await title_element.text_content()
                    title = title.strip() if title else "未知标题"
                    url = await title_element.get_attribute("href")

                    # 提取摘要
                    summary = "无摘要"
                    summary_element = await result.query_selector(
                        ".search-result-content, .pf-c-card__body"
                    )
                    if summary_element:
                        summary_text = await summary_element.text_content()
                        summary = summary_text.strip() if summary_text else "无摘要"

                    # 提取文档类型
                    doc_type = "未知类型"
                    doc_type_element = await result.query_selector(
                        ".search-result-info span, .pf-c-label"
                    )
                    if doc_type_element:
                        doc_type_text = await doc_type_element.text_content()
                        doc_type = doc_type_text.strip() if doc_type_text else "未知类型"

                    # 提取最后更新日期
                    last_updated = "未知日期"
                    date_element = await result.query_selector(
                        ".search-result-info time, .pf-c-label[data-testid='date']"
                    )
                    if date_element:
                        date_text = await date_element.text_content()
                        last_updated = date_text.strip() if date_text else "未知日期"

                    # 添加到结果列表
                    results.append(
                        {
                            "title": title,
                            "url": url,
                            "summary": summary,
                            "doc_type": doc_type,
                            "last_updated": last_updated,
                        }
                    )

                except Error as e:
                    logger.warning(f"处理搜索结果时出错: {e}")
                    continue

            # 提取成功，跳出重试循环
            break

        except Exception as e:
            logger.error(f"提取搜索结果时出错: {e}")
            logger.debug(f"错误堆栈: {traceback.format_exc()}")
            if attempt < max_retries - 1:
                log_step(f"将在2秒后重试... (尝试 {attempt + 1}/{max_retries})")
                await asyncio.sleep(2)
                await page.reload()
            else:
                log_step("多次尝试后仍出错")
                return []

    log_step(f"成功提取 {len(results)} 个搜索结果")
    return results


async def get_product_alerts(page: Page, product: str) -> List[Dict[str, Any]]:
    """
    获取特定产品的警报信息（已弃用）

    此功能已弃用，因为未来使用都是通过Claude Desktop的chat来完成

    Args:
        page (Page): Playwright页面实例
        product (str): 产品名称

    Returns:
        List[Dict[str, Any]]: 空列表
    """
    logger.warning("get_product_alerts 函数已弃用，因为未来使用都是通过Claude Desktop的chat来完成")
    return []


async def get_document_content(page: Page, document_url: str) -> Dict[str, Any]:
    """
    获取特定文档的详细内容

    Args:
        page (Page): Playwright页面实例
        document_url (str): 文档URL

    Returns:
        Dict[str, Any]: 文档内容
    """
    log_step(f"获取文档内容: {document_url}")

    try:
        # 访问文档页面
        await page.goto(document_url, wait_until="domcontentloaded")
        log_step("已加载文档页面")

        # 处理可能出现的Cookie弹窗
        await handle_cookie_popup(page)

        # 等待文档内容加载
        try:
            await page.wait_for_selector(
                ".field-item, .pf-c-content, article", state="visible", timeout=15000
            )
            log_step("文档内容已加载")
        except TimeoutError:
            log_step("等待文档内容超时，可能页面结构已更改")
            return {"error": "无法加载文档内容"}

        # 提取文档标题
        title = "未知标题"
        title_element = await page.query_selector("h1, .pf-c-title")
        if title_element:
            title_text = await title_element.text_content()
            title = title_text.strip() if title_text else "未知标题"

        # 提取文档内容
        content = "无法提取文档内容"
        content_element = await page.query_selector(".field-item, .pf-c-content, article")
        if content_element:
            content_text = await content_element.text_content()
            content = content_text.strip() if content_text else "无法提取文档内容"

        # 提取文档元数据
        metadata = {}
        try:
            # 尝试提取各种可能的元数据字段
            metadata_fields = await page.query_selector_all(".field, .pf-c-description-list__group")

            for field in metadata_fields:
                try:
                    label_element = await field.query_selector(
                        ".field-label, .pf-c-description-list__term"
                    )
                    value_element = await field.query_selector(
                        ".field-item, .pf-c-description-list__description"
                    )

                    if label_element and value_element:
                        label_text = await label_element.text_content()
                        value_text = await value_element.text_content()

                        label = label_text.strip().rstrip(":") if label_text else ""
                        value = value_text.strip() if value_text else ""

                        if label and value:
                            metadata[label] = value
                except Error:
                    continue
        except Exception as e:
            logger.warning(f"提取文档元数据时出错: {e}")
            logger.debug(f"错误堆栈: {traceback.format_exc()}")

        return {
            "title": title,
            "content": content,
            "url": document_url,
            "metadata": metadata,
        }

    except Exception as e:
        logger.error(f"获取文档内容时出错: {e}")
        logger.debug(f"错误堆栈: {traceback.format_exc()}")
        return {"error": f"获取文档内容时出错: {str(e)}"}
