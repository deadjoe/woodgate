"""
搜索模块测试
"""

from unittest.mock import AsyncMock, patch

import pytest
from playwright.async_api import ElementHandle, Page

from woodgate.core.search import (
    build_search_url,
    extract_search_results,
    get_document_content,
    get_product_alerts,
    perform_search,
)


def test_build_search_url_basic():
    """测试基本搜索URL构建"""
    url = build_search_url("memory leak")
    assert url == "https://access.redhat.com/search/?q=memory%20leak&page=1&rows=20&sort=relevant"


def test_build_search_url_with_products():
    """测试带产品过滤的搜索URL构建"""
    url = build_search_url("kubernetes", products=["Red Hat OpenShift Container Platform"])
    assert "q=kubernetes" in url
    assert "p=Red%20Hat%20OpenShift%20Container%20Platform" in url
    assert "page=1" in url
    assert "rows=20" in url


def test_build_search_url_with_doc_types():
    """测试带文档类型过滤的搜索URL构建"""
    url = build_search_url("selinux", doc_types=["Solution", "Article"])
    assert "q=selinux" in url
    assert "documentKind=Solution" in url
    assert "documentKind=Article" in url
    assert "page=1" in url
    assert "rows=20" in url


def test_build_search_url_with_pagination():
    """测试带分页的搜索URL构建"""
    url = build_search_url("memory leak", page=2, rows=50)
    assert "q=memory%20leak" in url
    assert "page=2" in url
    assert "rows=50" in url


def test_build_search_url_with_sorting():
    """测试带排序的搜索URL构建"""
    url = build_search_url("memory leak", sort_by="lastModifiedDate desc")
    assert "q=memory%20leak" in url
    assert "sort=lastModifiedDate%20desc" in url


def test_build_search_url_complete():
    """测试完整的搜索URL构建"""
    url = build_search_url(
        "performance tuning",
        products=["Red Hat Enterprise Linux"],
        doc_types=["Solution", "Article"],
        page=3,
        rows=30,
        sort_by="lastModifiedDate desc",
    )
    assert "q=performance%20tuning" in url
    assert "p=Red%20Hat%20Enterprise%20Linux" in url
    assert "documentKind=Solution" in url
    assert "documentKind=Article" in url
    assert "page=3" in url
    assert "rows=30" in url
    assert "sort=lastModifiedDate%20desc" in url


@pytest.mark.asyncio
async def test_perform_search():
    """测试执行搜索功能"""
    # 模拟Playwright Page
    mock_page = AsyncMock(spec=Page)

    # 模拟搜索结果
    mock_results = [
        {"title": "Test Result 1", "url": "https://example.com/1"},
        {"title": "Test Result 2", "url": "https://example.com/2"},
    ]

    # 模拟函数
    with patch(
        "woodgate.core.search.build_search_url", return_value="https://test-url.com"
    ) as mock_build_url:
        with patch("woodgate.core.search.handle_cookie_popup") as mock_handle_cookie:
            with patch(
                "woodgate.core.search.extract_search_results", return_value=mock_results
            ) as mock_extract:
                # 调用被测试的函数
                results = await perform_search(
                    mock_page,
                    query="test query",
                    products=["Test Product"],
                    doc_types=["Test Type"],
                )

                # 验证结果
                assert results == mock_results
                mock_build_url.assert_called_once_with(
                    "test query", ["Test Product"], ["Test Type"], 1, 20, "relevant"
                )
                mock_page.goto.assert_called_once_with(
                    "https://test-url.com", wait_until="domcontentloaded"
                )
                assert mock_handle_cookie.called
                mock_extract.assert_called_once_with(mock_page)


@pytest.mark.asyncio
async def test_extract_search_results():
    """测试提取搜索结果功能"""
    # 模拟Playwright Page和元素
    mock_page = AsyncMock(spec=Page)
    mock_result1 = AsyncMock(spec=ElementHandle)
    mock_result2 = AsyncMock(spec=ElementHandle)
    mock_title1 = AsyncMock(spec=ElementHandle)
    mock_title2 = AsyncMock(spec=ElementHandle)
    mock_summary1 = AsyncMock(spec=ElementHandle)
    mock_summary2 = AsyncMock(spec=ElementHandle)
    mock_doc_type1 = AsyncMock(spec=ElementHandle)
    mock_doc_type2 = AsyncMock(spec=ElementHandle)
    mock_date1 = AsyncMock(spec=ElementHandle)
    mock_date2 = AsyncMock(spec=ElementHandle)

    # 设置模拟行为
    mock_page.query_selector_all.return_value = [mock_result1, mock_result2]

    # 设置第一个结果的模拟行为
    mock_result1.query_selector.side_effect = lambda selector: {
        ".search-result-content, .pf-c-card__body": mock_summary1,
        ".search-result-info span, .pf-c-label": mock_doc_type1,
        ".search-result-info time, .pf-c-label[data-testid='date']": mock_date1,
        "h2 a, .pf-c-title a": mock_title1,
    }[selector]

    # 设置第二个结果的模拟行为
    mock_result2.query_selector.side_effect = lambda selector: {
        ".search-result-content, .pf-c-card__body": mock_summary2,
        ".search-result-info span, .pf-c-label": mock_doc_type2,
        ".search-result-info time, .pf-c-label[data-testid='date']": mock_date2,
        "h2 a, .pf-c-title a": mock_title2,
    }[selector]

    # 设置文本内容
    mock_title1.text_content.return_value = "Test Result 1"
    mock_title1.get_attribute.return_value = "https://example.com/1"
    mock_summary1.text_content.return_value = "Summary 1"
    mock_doc_type1.text_content.return_value = "Solution"
    mock_date1.text_content.return_value = "2023-01-01"

    mock_title2.text_content.return_value = "Test Result 2"
    mock_title2.get_attribute.return_value = "https://example.com/2"
    mock_summary2.text_content.return_value = "Summary 2"
    mock_doc_type2.text_content.return_value = "Article"
    mock_date2.text_content.return_value = "2023-01-02"

    # 调用被测试的函数
    results = await extract_search_results(mock_page)

    # 验证结果
    assert len(results) == 2
    assert results[0]["title"] == "Test Result 1"
    assert results[0]["url"] == "https://example.com/1"
    assert results[0]["summary"] == "Summary 1"
    assert results[0]["doc_type"] == "Solution"
    assert results[0]["last_updated"] == "2023-01-01"

    assert results[1]["title"] == "Test Result 2"
    assert results[1]["url"] == "https://example.com/2"
    assert results[1]["summary"] == "Summary 2"
    assert results[1]["doc_type"] == "Article"
    assert results[1]["last_updated"] == "2023-01-02"


@pytest.mark.asyncio
async def test_get_product_alerts():
    """测试获取产品警报功能"""
    # 模拟Playwright Page和元素
    mock_page = AsyncMock(spec=Page)
    mock_alert1 = AsyncMock(spec=ElementHandle)
    mock_alert2 = AsyncMock(spec=ElementHandle)
    mock_title1 = AsyncMock(spec=ElementHandle)
    mock_title2 = AsyncMock(spec=ElementHandle)
    mock_severity1 = AsyncMock(spec=ElementHandle)
    mock_severity2 = AsyncMock(spec=ElementHandle)
    mock_date1 = AsyncMock(spec=ElementHandle)
    mock_date2 = AsyncMock(spec=ElementHandle)
    mock_summary1 = AsyncMock(spec=ElementHandle)
    mock_summary2 = AsyncMock(spec=ElementHandle)

    # 设置模拟行为
    mock_page.query_selector_all.return_value = [mock_alert1, mock_alert2]

    # 设置第一个警报的模拟行为
    mock_alert1.query_selector.side_effect = lambda selector: {
        "h2 a, .pf-c-title a": mock_title1,
        ".security-severity, .pf-c-label": mock_severity1,
        ".portal-advisory-date, time": mock_date1,
        ".portal-advisory-synopsis, .pf-c-card__body": mock_summary1,
    }[selector]

    # 设置第二个警报的模拟行为
    mock_alert2.query_selector.side_effect = lambda selector: {
        "h2 a, .pf-c-title a": mock_title2,
        ".security-severity, .pf-c-label": mock_severity2,
        ".portal-advisory-date, time": mock_date2,
        ".portal-advisory-synopsis, .pf-c-card__body": mock_summary2,
    }[selector]

    # 设置文本内容
    mock_title1.text_content.return_value = "Critical Security Alert 1"
    mock_title1.get_attribute.return_value = "https://example.com/alert1"
    mock_severity1.text_content.return_value = "Critical"
    mock_date1.text_content.return_value = "2023-01-01"
    mock_summary1.text_content.return_value = "Critical security issue"

    mock_title2.text_content.return_value = "Important Security Alert 2"
    mock_title2.get_attribute.return_value = "https://example.com/alert2"
    mock_severity2.text_content.return_value = "Important"
    mock_date2.text_content.return_value = "2023-01-02"
    mock_summary2.text_content.return_value = "Important security issue"

    # 模拟函数
    with patch("woodgate.core.search.handle_cookie_popup") as mock_handle_cookie:
        # 调用被测试的函数
        alerts = await get_product_alerts(mock_page, "Red Hat Enterprise Linux")

        # 验证结果
        assert len(alerts) == 2
        assert alerts[0]["title"] == "Critical Security Alert 1"
        assert alerts[0]["url"] == "https://example.com/alert1"
        assert alerts[0]["severity"] == "Critical"
        assert alerts[0]["published_date"] == "2023-01-01"
        assert alerts[0]["summary"] == "Critical security issue"

        assert alerts[1]["title"] == "Important Security Alert 2"
        assert alerts[1]["url"] == "https://example.com/alert2"
        assert alerts[1]["severity"] == "Important"
        assert alerts[1]["published_date"] == "2023-01-02"
        assert alerts[1]["summary"] == "Important security issue"

        # 验证页面导航
        mock_page.goto.assert_called_once()
        assert "Red%20Hat%20Enterprise%20Linux" in mock_page.goto.call_args[0][0]
        assert mock_handle_cookie.called


@pytest.mark.asyncio
async def test_get_document_content():
    """测试获取文档内容功能"""
    # 模拟Playwright Page和元素
    mock_page = AsyncMock(spec=Page)
    mock_title = AsyncMock(spec=ElementHandle)
    mock_content = AsyncMock(spec=ElementHandle)
    mock_metadata_field1 = AsyncMock(spec=ElementHandle)
    mock_metadata_field2 = AsyncMock(spec=ElementHandle)
    mock_label1 = AsyncMock(spec=ElementHandle)
    mock_value1 = AsyncMock(spec=ElementHandle)
    mock_label2 = AsyncMock(spec=ElementHandle)
    mock_value2 = AsyncMock(spec=ElementHandle)

    # 设置模拟行为
    mock_page.query_selector.side_effect = lambda selector: {
        "h1, .pf-c-title": mock_title,
        ".field-item, .pf-c-content, article": mock_content,
    }[selector]

    mock_page.query_selector_all.return_value = [mock_metadata_field1, mock_metadata_field2]

    # 设置元数据字段的模拟行为
    mock_metadata_field1.query_selector.side_effect = lambda selector: {
        ".field-label, .pf-c-description-list__term": mock_label1,
        ".field-item, .pf-c-description-list__description": mock_value1,
    }[selector]

    mock_metadata_field2.query_selector.side_effect = lambda selector: {
        ".field-label, .pf-c-description-list__term": mock_label2,
        ".field-item, .pf-c-description-list__description": mock_value2,
    }[selector]

    # 设置文本内容
    mock_title.text_content.return_value = "Test Document Title"
    mock_content.text_content.return_value = "This is the document content."
    mock_label1.text_content.return_value = "Document Type:"
    mock_value1.text_content.return_value = "Solution"
    mock_label2.text_content.return_value = "Last Updated:"
    mock_value2.text_content.return_value = "2023-01-01"

    # 模拟函数
    with patch("woodgate.core.search.handle_cookie_popup") as mock_handle_cookie:
        # 调用被测试的函数
        document = await get_document_content(mock_page, "https://example.com/document")

        # 验证结果
        assert document["title"] == "Test Document Title"
        assert document["content"] == "This is the document content."
        assert document["url"] == "https://example.com/document"
        assert document["metadata"]["Document Type"] == "Solution"
        assert document["metadata"]["Last Updated"] == "2023-01-01"

        # 验证页面导航
        mock_page.goto.assert_called_once_with(
            "https://example.com/document", wait_until="domcontentloaded"
        )
        assert mock_handle_cookie.called
