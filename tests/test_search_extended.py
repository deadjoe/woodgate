"""
搜索模块扩展测试
"""

import pytest
from unittest.mock import patch, MagicMock
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from woodgate.core.search import (
    extract_search_results,
    perform_search,
    get_product_alerts,
    get_document_content,
)


@pytest.mark.asyncio
async def test_perform_search_error_handling():
    """测试执行搜索 - 错误处理"""
    mock_browser = MagicMock()
    mock_browser.get.side_effect = Exception("Connection error")

    with patch("woodgate.core.search.logger.error") as mock_error:
        with patch("woodgate.core.search.log_step"):
            with patch(
                "woodgate.core.search.build_search_url", return_value="https://example.com/search"
            ):
                results = await perform_search(mock_browser, "test query")

                assert isinstance(results, list)
                assert len(results) == 0
                assert mock_error.called


@pytest.mark.asyncio
async def test_perform_search_no_results():
    """测试执行搜索 - 无结果"""
    mock_browser = MagicMock()
    mock_wait = MagicMock()

    # 模拟页面加载但没有结果
    with patch("woodgate.core.search.WebDriverWait", return_value=mock_wait):
        with patch("woodgate.core.search.log_step"):
            with patch(
                "woodgate.core.search.build_search_url", return_value="https://example.com/search"
            ):
                with patch("woodgate.core.search.handle_cookie_popup"):
                    with patch("woodgate.core.search.extract_search_results", return_value=[]):
                        results = await perform_search(mock_browser, "test query")

                        assert isinstance(results, list)
                        assert len(results) == 0


@pytest.mark.asyncio
async def test_get_product_alerts_error_handling():
    """测试获取产品警报 - 错误处理"""
    mock_browser = MagicMock()
    mock_browser.get.side_effect = Exception("Connection error")

    with patch("woodgate.core.search.logger.error") as mock_error:
        with patch("woodgate.core.search.log_step"):
            alerts = await get_product_alerts(mock_browser, "Red Hat Enterprise Linux")

            assert isinstance(alerts, list)
            assert len(alerts) == 0
            assert mock_error.called


@pytest.mark.asyncio
async def test_get_document_content_error_handling():
    """测试获取文档内容 - 错误处理"""
    mock_browser = MagicMock()
    mock_browser.get.side_effect = Exception("Connection error")

    with patch("woodgate.core.search.logger.error") as mock_error:
        with patch("woodgate.core.search.log_step"):
            document = await get_document_content(mock_browser, "https://example.com/doc")

            assert isinstance(document, dict)
            assert "error" in document
            assert mock_error.called


@pytest.mark.asyncio
async def test_extract_search_results_empty():
    """测试提取搜索结果 - 空页面"""
    mock_driver = MagicMock()
    mock_driver.find_elements.return_value = []

    # 模拟找到"无结果"消息
    mock_driver.find_element.return_value = MagicMock()

    with patch("woodgate.core.search.log_step"):
        with patch("woodgate.core.search.asyncio.sleep"):
            results = await extract_search_results(mock_driver)

            assert isinstance(results, list)
            assert len(results) == 0


@pytest.mark.asyncio
async def test_extract_search_results_with_data():
    """测试提取搜索结果 - 有数据"""
    mock_driver = MagicMock()

    # 创建模拟的标题元素
    mock_title1 = MagicMock()
    mock_title1.text = "Title 1"
    mock_title1.get_attribute.return_value = "https://example.com/1"

    mock_title2 = MagicMock()
    mock_title2.text = "Title 2"
    mock_title2.get_attribute.return_value = "https://example.com/2"

    # 创建模拟的摘要元素
    mock_summary1 = MagicMock()
    mock_summary1.text = "Description 1"

    mock_summary2 = MagicMock()
    mock_summary2.text = "Description 2"

    # 创建模拟的文档类型元素
    mock_doctype1 = MagicMock()
    mock_doctype1.text = "Solution"

    mock_doctype2 = MagicMock()
    mock_doctype2.text = "Article"

    # 创建模拟的日期元素
    mock_date1 = MagicMock()
    mock_date1.text = "2023-01-01"

    mock_date2 = MagicMock()
    mock_date2.text = "2023-01-02"

    # 模拟搜索结果项
    mock_item1 = MagicMock()
    mock_item1.find_element.side_effect = lambda by, selector: {
        (By.CSS_SELECTOR, "h2 a, .pf-c-title a"): mock_title1,
        (By.CSS_SELECTOR, ".search-result-content, .pf-c-card__body"): mock_summary1,
        (By.CSS_SELECTOR, ".search-result-info span, .pf-c-label"): mock_doctype1,
        (By.CSS_SELECTOR, ".search-result-info time, .pf-c-label[data-testid='date']"): mock_date1,
    }.get((by, selector), None)

    mock_item2 = MagicMock()
    mock_item2.find_element.side_effect = lambda by, selector: {
        (By.CSS_SELECTOR, "h2 a, .pf-c-title a"): mock_title2,
        (By.CSS_SELECTOR, ".search-result-content, .pf-c-card__body"): mock_summary2,
        (By.CSS_SELECTOR, ".search-result-info span, .pf-c-label"): mock_doctype2,
        (By.CSS_SELECTOR, ".search-result-info time, .pf-c-label[data-testid='date']"): mock_date2,
    }.get((by, selector), None)

    # 设置模拟的搜索结果列表
    mock_driver.find_elements.return_value = [mock_item1, mock_item2]

    # 模拟日志和异步函数
    with patch("woodgate.core.search.log_step"):
        with patch("woodgate.core.search.asyncio.sleep"):
            # 调用被测试的函数
            results = await extract_search_results(mock_driver)

    # 验证结果
    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0]["title"] == "Title 1"
    assert results[0]["url"] == "https://example.com/1"
    assert results[0]["summary"] == "Description 1"
    assert results[0]["doc_type"] == "Solution"
    assert results[1]["title"] == "Title 2"


@pytest.mark.asyncio
async def test_get_document_content_detailed():
    """测试获取文档内容 - 详细测试"""
    mock_driver = MagicMock()
    mock_wait = MagicMock()

    # 创建模拟的标题元素
    mock_title = MagicMock()
    mock_title.text = "Document Title"

    # 创建模拟的内容元素
    mock_content = MagicMock()
    mock_content.text = "Document Content"

    # 创建模拟的元数据标签元素
    mock_label = MagicMock()
    mock_label.text = "Type:"

    # 创建模拟的元数据值元素
    mock_value = MagicMock()
    mock_value.text = "Solution"

    # 创建模拟的元数据字段
    mock_field = MagicMock()
    mock_field.find_element.side_effect = lambda by, selector: {
        (By.CSS_SELECTOR, ".field-label, .pf-c-description-list__term"): mock_label,
        (By.CSS_SELECTOR, ".field-item, .pf-c-description-list__description"): mock_value,
    }.get((by, selector), None)

    # 设置模拟的元素查找
    mock_driver.find_element.side_effect = lambda by, selector: {
        (By.CSS_SELECTOR, "h1, .pf-c-title"): mock_title,
        (By.CSS_SELECTOR, ".field-item, .pf-c-content, article"): mock_content,
    }.get((by, selector), None)

    mock_driver.find_elements.return_value = [mock_field]

    # 模拟WebDriverWait
    with patch("woodgate.core.search.WebDriverWait", return_value=mock_wait):
        # 模拟handle_cookie_popup
        with patch("woodgate.core.search.handle_cookie_popup"):
            # 模拟日志
            with patch("woodgate.core.search.log_step"):
                # 调用被测试的函数
                document = await get_document_content(mock_driver, "https://example.com/doc")

    # 验证结果
    assert document["title"] == "Document Title"
    assert document["content"] == "Document Content"
    assert document["url"] == "https://example.com/doc"
    assert document["metadata"]["Type"] == "Solution"


@pytest.mark.asyncio
async def test_get_document_content_missing_elements():
    """测试获取文档内容 - 缺少元素"""
    mock_driver = MagicMock()
    mock_wait = MagicMock()

    # 模拟找不到元素
    mock_driver.find_element.side_effect = NoSuchElementException("Element not found")
    mock_driver.find_elements.return_value = []

    # 模拟WebDriverWait
    with patch("woodgate.core.search.WebDriverWait", return_value=mock_wait):
        # 模拟handle_cookie_popup
        with patch("woodgate.core.search.handle_cookie_popup"):
            # 模拟日志
            with patch("woodgate.core.search.log_step"):
                # 调用被测试的函数
                document = await get_document_content(mock_driver, "https://example.com/doc")

    # 验证结果
    assert document["title"] == "未知标题"
    assert document["content"] == "无法提取文档内容"
    assert document["url"] == "https://example.com/doc"
    assert document["metadata"] == {}
