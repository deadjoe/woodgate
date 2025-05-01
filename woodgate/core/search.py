"""
搜索模块 - 处理Red Hat客户门户的搜索功能
"""

import asyncio
import logging
import urllib.parse
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)

from .utils import log_step, handle_cookie_popup

logger = logging.getLogger(__name__)

# Red Hat客户门户搜索URL
SEARCH_BASE_URL = "https://access.redhat.com/search/"


async def perform_search(
    driver: webdriver.Chrome,
    query: str,
    products: List[str] = None,
    doc_types: List[str] = None,
    page: int = 1,
    rows: int = 20,
    sort_by: str = "relevant",
) -> List[Dict[str, Any]]:
    """
    在Red Hat客户门户执行搜索

    Args:
        driver (WebDriver): Selenium WebDriver实例
        query (str): 搜索关键词
        products (List[str], optional): 要搜索的产品列表. Defaults to None.
        doc_types (List[str], optional): 文档类型列表. Defaults to None.
        page (int, optional): 页码. Defaults to 1.
        rows (int, optional): 每页结果数. Defaults to 20.
        sort_by (str, optional): 排序方式. Defaults to "relevant".

    Returns:
        List[Dict[str, Any]]: 搜索结果列表
    """
    log_step(f"执行搜索: '{query}'")

    # 构建搜索URL
    search_url = build_search_url(query, products, doc_types, page, rows, sort_by)
    log_step(f"搜索URL: {search_url}")

    try:
        # 访问搜索页面
        driver.get(search_url)
        log_step("已加载搜索页面")

        # 处理可能出现的Cookie弹窗
        await handle_cookie_popup(driver)

        # 等待搜索结果加载
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".search-result, .pf-c-card"))
            )
            log_step("搜索结果已加载")
        except TimeoutException:
            log_step("等待搜索结果超时，可能没有结果或页面结构已更改")
            return []

        # 提取搜索结果
        return await extract_search_results(driver)

    except Exception as e:
        logger.error(f"执行搜索时出错: {e}")
        return []


def build_search_url(
    query: str,
    products: List[str] = None,
    doc_types: List[str] = None,
    page: int = 1,
    rows: int = 20,
    sort_by: str = "relevant",
) -> str:
    """
    构建Red Hat客户门户搜索URL

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
    # 编码查询参数
    encoded_query = urllib.parse.quote(query)

    # 构建基本URL
    url = f"{SEARCH_BASE_URL}?q={encoded_query}"

    # 添加产品过滤器
    if products and len(products) > 0:
        for product in products:
            encoded_product = urllib.parse.quote(product)
            url += f"&p={encoded_product}"

    # 添加文档类型过滤器
    if doc_types and len(doc_types) > 0:
        for doc_type in doc_types:
            encoded_doc_type = urllib.parse.quote(doc_type)
            url += f"&documentKind={encoded_doc_type}"

    # 添加分页参数
    url += f"&page={page}"
    url += f"&rows={rows}"

    # 添加排序参数
    if sort_by:
        url += f"&sort={urllib.parse.quote(sort_by)}"

    return url


async def extract_search_results(driver: webdriver.Chrome) -> List[Dict[str, Any]]:
    """
    从搜索结果页面提取结果

    Args:
        driver (WebDriver): Selenium WebDriver实例

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
            result_elements = driver.find_elements(By.CSS_SELECTOR, ".search-result, .pf-c-card")
            log_step(f"找到 {len(result_elements)} 个搜索结果")

            if not result_elements:
                # 检查是否有"无结果"消息
                try:
                    driver.find_element(By.CSS_SELECTOR, ".no-results, .pf-c-empty-state")
                    log_step("搜索没有返回结果")
                    return []
                except NoSuchElementException:
                    if attempt < max_retries - 1:
                        log_step(
                            f"未找到结果元素，将在2秒后重试... (尝试 {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(2)
                        continue
                    else:
                        log_step("多次尝试后仍未找到结果元素")
                        return []

            # 处理每个搜索结果
            for result in result_elements:
                try:
                    # 提取标题和链接
                    title_element = result.find_element(By.CSS_SELECTOR, "h2 a, .pf-c-title a")
                    title = title_element.text.strip()
                    url = title_element.get_attribute("href")

                    # 提取摘要
                    try:
                        summary_element = result.find_element(
                            By.CSS_SELECTOR, ".search-result-content, .pf-c-card__body"
                        )
                        summary = summary_element.text.strip()
                    except NoSuchElementException:
                        summary = "无摘要"

                    # 提取文档类型
                    try:
                        doc_type_element = result.find_element(
                            By.CSS_SELECTOR, ".search-result-info span, .pf-c-label"
                        )
                        doc_type = doc_type_element.text.strip()
                    except NoSuchElementException:
                        doc_type = "未知类型"

                    # 提取最后更新日期
                    try:
                        date_element = result.find_element(
                            By.CSS_SELECTOR,
                            ".search-result-info time, .pf-c-label[data-testid='date']",
                        )
                        last_updated = date_element.text.strip()
                    except NoSuchElementException:
                        last_updated = "未知日期"

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

                except (NoSuchElementException, StaleElementReferenceException) as e:
                    logger.warning(f"处理搜索结果时出错: {e}")
                    continue

            # 提取成功，跳出重试循环
            break

        except Exception as e:
            logger.error(f"提取搜索结果时出错: {e}")
            if attempt < max_retries - 1:
                log_step(f"将在2秒后重试... (尝试 {attempt + 1}/{max_retries})")
                await asyncio.sleep(2)
            else:
                log_step("多次尝试后仍出错")
                return []

    log_step(f"成功提取 {len(results)} 个搜索结果")
    return results


async def get_product_alerts(driver: webdriver.Chrome, product: str) -> List[Dict[str, Any]]:
    """
    获取特定产品的警报信息

    Args:
        driver (WebDriver): Selenium WebDriver实例
        product (str): 产品名称

    Returns:
        List[Dict[str, Any]]: 警报信息列表
    """
    log_step(f"获取产品警报: '{product}'")

    # 构建产品警报URL
    encoded_product = urllib.parse.quote(product)
    alerts_url = f"https://access.redhat.com/security/security-updates/#/?q={encoded_product}&p=1&sort=portal_publication_date%20desc&rows=10&portal_advisory_type=Security%20Advisory"

    try:
        # 访问警报页面
        driver.get(alerts_url)
        log_step("已加载警报页面")

        # 处理可能出现的Cookie弹窗
        await handle_cookie_popup(driver)

        # 等待警报结果加载
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".pf-c-card, .portal-advisory"))
            )
            log_step("警报结果已加载")
        except TimeoutException:
            log_step("等待警报结果超时，可能没有结果或页面结构已更改")
            return []

        # 提取警报结果
        alerts = []
        alert_elements = driver.find_elements(By.CSS_SELECTOR, ".pf-c-card, .portal-advisory")

        for alert in alert_elements:
            try:
                # 提取警报标题和链接
                title_element = alert.find_element(By.CSS_SELECTOR, "h2 a, .pf-c-title a")
                title = title_element.text.strip()
                url = title_element.get_attribute("href")

                # 提取警报严重性
                try:
                    severity_element = alert.find_element(
                        By.CSS_SELECTOR, ".security-severity, .pf-c-label"
                    )
                    severity = severity_element.text.strip()
                except NoSuchElementException:
                    severity = "未知严重性"

                # 提取发布日期
                try:
                    date_element = alert.find_element(
                        By.CSS_SELECTOR, ".portal-advisory-date, time"
                    )
                    published_date = date_element.text.strip()
                except NoSuchElementException:
                    published_date = "未知日期"

                # 提取摘要
                try:
                    summary_element = alert.find_element(
                        By.CSS_SELECTOR, ".portal-advisory-synopsis, .pf-c-card__body"
                    )
                    summary = summary_element.text.strip()
                except NoSuchElementException:
                    summary = "无摘要"

                # 添加到警报列表
                alerts.append(
                    {
                        "title": title,
                        "url": url,
                        "severity": severity,
                        "published_date": published_date,
                        "summary": summary,
                    }
                )

            except (NoSuchElementException, StaleElementReferenceException) as e:
                logger.warning(f"处理警报结果时出错: {e}")
                continue

        log_step(f"成功提取 {len(alerts)} 个警报")
        return alerts

    except Exception as e:
        logger.error(f"获取产品警报时出错: {e}")
        return []


async def get_document_content(driver: webdriver.Chrome, document_url: str) -> Dict[str, Any]:
    """
    获取特定文档的详细内容

    Args:
        driver (WebDriver): Selenium WebDriver实例
        document_url (str): 文档URL

    Returns:
        Dict[str, Any]: 文档内容
    """
    log_step(f"获取文档内容: {document_url}")

    try:
        # 访问文档页面
        driver.get(document_url)
        log_step("已加载文档页面")

        # 处理可能出现的Cookie弹窗
        await handle_cookie_popup(driver)

        # 等待文档内容加载
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".field-item, .pf-c-content, article")
                )
            )
            log_step("文档内容已加载")
        except TimeoutException:
            log_step("等待文档内容超时，可能页面结构已更改")
            return {"error": "无法加载文档内容"}

        # 提取文档标题
        try:
            title_element = driver.find_element(By.CSS_SELECTOR, "h1, .pf-c-title")
            title = title_element.text.strip()
        except NoSuchElementException:
            title = "未知标题"

        # 提取文档内容
        try:
            content_element = driver.find_element(
                By.CSS_SELECTOR, ".field-item, .pf-c-content, article"
            )
            content = content_element.text.strip()
        except NoSuchElementException:
            content = "无法提取文档内容"

        # 提取文档元数据
        metadata = {}
        try:
            # 尝试提取各种可能的元数据字段
            metadata_fields = driver.find_elements(
                By.CSS_SELECTOR, ".field, .pf-c-description-list__group"
            )

            for field in metadata_fields:
                try:
                    label_element = field.find_element(
                        By.CSS_SELECTOR, ".field-label, .pf-c-description-list__term"
                    )
                    value_element = field.find_element(
                        By.CSS_SELECTOR, ".field-item, .pf-c-description-list__description"
                    )

                    label = label_element.text.strip().rstrip(":")
                    value = value_element.text.strip()

                    if label and value:
                        metadata[label] = value
                except NoSuchElementException:
                    continue
        except Exception as e:
            logger.warning(f"提取文档元数据时出错: {e}")

        return {"title": title, "content": content, "url": document_url, "metadata": metadata}

    except Exception as e:
        logger.error(f"获取文档内容时出错: {e}")
        return {"error": f"获取文档内容时出错: {str(e)}"}
