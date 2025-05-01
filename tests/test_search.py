"""
搜索模块测试
"""

import pytest
from unittest.mock import patch, MagicMock

from woodgate.core.search import (
    perform_search,
    build_search_url,
    extract_search_results,
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
    # 模拟Selenium WebDriver
    mock_driver = MagicMock()

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
                    mock_driver,
                    query="test query",
                    products=["Test Product"],
                    doc_types=["Test Type"],
                )

                # 验证结果
                assert results == mock_results
                mock_build_url.assert_called_once_with(
                    "test query", ["Test Product"], ["Test Type"], 1, 20, "relevant"
                )
                mock_driver.get.assert_called_once_with("https://test-url.com")
                assert mock_handle_cookie.called
                mock_extract.assert_called_once_with(mock_driver)


@pytest.mark.asyncio
async def test_extract_search_results():
    """测试提取搜索结果功能"""
    # 模拟Selenium WebDriver和元素
    mock_driver = MagicMock()
    mock_result1 = MagicMock()
    mock_result2 = MagicMock()
    mock_title1 = MagicMock()
    mock_title2 = MagicMock()
    mock_summary1 = MagicMock()
    mock_summary2 = MagicMock()
    mock_doc_type1 = MagicMock()
    mock_doc_type2 = MagicMock()
    mock_date1 = MagicMock()
    mock_date2 = MagicMock()

    # 设置模拟行为
    mock_driver.find_elements.return_value = [mock_result1, mock_result2]

    mock_result1.find_element.side_effect = lambda by, selector: {
        ".search-result-content, .pf-c-card__body": mock_summary1,
        ".search-result-info span, .pf-c-label": mock_doc_type1,
        ".search-result-info time, .pf-c-label[data-testid='date']": mock_date1,
        "h2 a, .pf-c-title a": mock_title1,
    }[selector]

    mock_result2.find_element.side_effect = lambda by, selector: {
        ".search-result-content, .pf-c-card__body": mock_summary2,
        ".search-result-info span, .pf-c-label": mock_doc_type2,
        ".search-result-info time, .pf-c-label[data-testid='date']": mock_date2,
        "h2 a, .pf-c-title a": mock_title2,
    }[selector]

    mock_title1.text = "Test Result 1"
    mock_title1.get_attribute.return_value = "https://example.com/1"
    mock_summary1.text = "Summary 1"
    mock_doc_type1.text = "Solution"
    mock_date1.text = "2023-01-01"

    mock_title2.text = "Test Result 2"
    mock_title2.get_attribute.return_value = "https://example.com/2"
    mock_summary2.text = "Summary 2"
    mock_doc_type2.text = "Article"
    mock_date2.text = "2023-01-02"

    # 调用被测试的函数
    results = await extract_search_results(mock_driver)

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
