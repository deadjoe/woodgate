"""
MCP服务器模块测试
"""

from unittest.mock import AsyncMock, patch

import pytest

from server import (
    available_products,
    document_types,
    get_alerts,
    get_document,
    search,
    search_params,
)


def test_available_products():
    """测试可用产品列表资源"""
    products = available_products()
    assert isinstance(products, list)
    assert len(products) > 0
    assert "Red Hat Enterprise Linux" in products
    assert "Red Hat OpenShift Container Platform" in products


def test_document_types():
    """测试文档类型列表资源"""
    doc_types = document_types()
    assert isinstance(doc_types, list)
    assert len(doc_types) > 0
    assert "Solution" in doc_types
    assert "Article" in doc_types


def test_search_params():
    """测试搜索参数配置资源"""
    params = search_params()
    assert isinstance(params, dict)
    assert "sort_options" in params
    assert "products" in params
    assert "doc_types" in params
    assert "default_rows" in params
    assert "max_rows" in params


@pytest.mark.asyncio
async def test_search():
    """测试搜索工具"""
    # 模拟Playwright组件
    mock_playwright = AsyncMock()
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_results = [
        {"title": "Test Result 1", "url": "https://example.com/1"},
        {"title": "Test Result 2", "url": "https://example.com/2"},
    ]

    # 模拟函数
    with patch(
        "server.initialize_browser",
        return_value=(mock_playwright, mock_browser, mock_context, mock_page),
    ) as mock_init_browser:
        with patch("server.login_to_redhat_portal", return_value=True) as mock_login:
            with patch("server.perform_search", return_value=mock_results) as mock_search:
                with patch("server.get_credentials", return_value=("test_user", "test_pass")):
                    with patch("server.close_browser") as mock_close_browser:
                        # 调用被测试的函数
                        results = await search(
                            query="test query", products=["Test Product"], doc_types=["Test Type"]
                        )

                        # 验证结果
                        assert results == mock_results
                        assert mock_init_browser.called
                        mock_login.assert_called_once_with(
                            mock_page, mock_context, "test_user", "test_pass"
                        )
                        mock_search.assert_called_once_with(
                            mock_page,
                            query="test query",
                            products=["Test Product"],
                            doc_types=["Test Type"],
                            page_num=1,
                            rows=20,
                            sort_by="relevant",
                        )
                        mock_close_browser.assert_called_once_with(
                            mock_playwright, mock_browser, mock_context, mock_page
                        )


@pytest.mark.asyncio
async def test_get_alerts():
    """测试获取警报工具"""
    # 模拟Playwright组件
    mock_playwright = AsyncMock()
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_alerts = [
        {"title": "Test Alert 1", "severity": "Critical"},
        {"title": "Test Alert 2", "severity": "Important"},
    ]

    # 模拟函数
    with patch(
        "server.initialize_browser",
        return_value=(mock_playwright, mock_browser, mock_context, mock_page),
    ) as mock_init_browser:
        with patch("server.login_to_redhat_portal", return_value=True) as mock_login:
            with patch("server.get_product_alerts", return_value=mock_alerts) as mock_get_alerts:
                with patch("server.get_credentials", return_value=("test_user", "test_pass")):
                    with patch("server.close_browser") as mock_close_browser:
                        # 调用被测试的函数
                        alerts = await get_alerts(product="Test Product")

                        # 验证结果
                        assert alerts == mock_alerts
                        assert mock_init_browser.called
                        mock_login.assert_called_once_with(
                            mock_page, mock_context, "test_user", "test_pass"
                        )
                        mock_get_alerts.assert_called_once_with(mock_page, "Test Product")
                        mock_close_browser.assert_called_once_with(
                            mock_playwright, mock_browser, mock_context, mock_page
                        )


@pytest.mark.asyncio
async def test_get_document():
    """测试获取文档工具"""
    # 模拟Playwright组件
    mock_playwright = AsyncMock()
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_document = {
        "title": "Test Document",
        "content": "Test content",
        "url": "https://example.com/doc",
        "metadata": {"type": "Solution"},
    }

    # 模拟函数
    with patch(
        "server.initialize_browser",
        return_value=(mock_playwright, mock_browser, mock_context, mock_page),
    ) as mock_init_browser:
        with patch("server.login_to_redhat_portal", return_value=True) as mock_login:
            with patch("server.get_document_content", return_value=mock_document) as mock_get_doc:
                with patch("server.get_credentials", return_value=("test_user", "test_pass")):
                    with patch("server.close_browser") as mock_close_browser:
                        # 调用被测试的函数
                        document = await get_document(document_url="https://example.com/doc")

                        # 验证结果
                        assert document == mock_document
                        assert mock_init_browser.called
                        mock_login.assert_called_once_with(
                            mock_page, mock_context, "test_user", "test_pass"
                        )
                        mock_get_doc.assert_called_once_with(mock_page, "https://example.com/doc")
                        mock_close_browser.assert_called_once_with(
                            mock_playwright, mock_browser, mock_context, mock_page
                        )
