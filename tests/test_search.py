"""
搜索模块测试 - 包含基本测试、扩展测试和单元测试
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from playwright.async_api import ElementHandle, Page, TimeoutError

from woodgate.core.search import (
    build_search_url,
    extract_search_results,
    get_document_content,
    get_product_alerts,
    perform_search,
)


class TestSearchBasic:
    """搜索模块基本测试"""

    def test_build_search_url_basic(self):
        """测试基本搜索URL构建"""
        url = build_search_url("memory leak")
        assert "q=memory+leak" in url
        assert "p=1" in url
        assert "rows=20" in url
        assert "sort=relevant" in url

    def test_build_search_url_with_products(self):
        """测试带产品过滤的搜索URL构建"""
        url = build_search_url("kubernetes", products=["Red Hat OpenShift Container Platform"])
        assert "q=kubernetes" in url
        assert "product=Red+Hat+OpenShift+Container+Platform" in url

    def test_build_search_url_with_doc_types(self):
        """测试带文档类型过滤的搜索URL构建"""
        url = build_search_url("memory leak", doc_types=["Article", "Solution"])
        assert "q=memory+leak" in url
        assert "documentKind=Article%26Solution" in url

    def test_build_search_url_with_pagination(self):
        """测试带分页的搜索URL构建"""
        url = build_search_url("memory leak", page=3, rows=50)
        assert "q=memory+leak" in url
        assert "p=3" in url
        assert "rows=50" in url

    def test_build_search_url_with_sorting(self):
        """测试带排序的搜索URL构建"""
        url = build_search_url("memory leak", sort_by="lastModifiedDate desc")
        assert "q=memory+leak" in url
        assert "sort=lastModifiedDate+desc" in url

    def test_build_search_url_complete(self):
        """测试完整的搜索URL构建"""
        url = build_search_url(
            "performance tuning",
            products=["Red Hat Enterprise Linux"],
            doc_types=["Article", "Solution"],
            page=2,
            rows=30,
            sort_by="lastModifiedDate desc",
        )
        assert "q=performance+tuning" in url
        assert "product=Red+Hat+Enterprise+Linux" in url
        assert "documentKind=Article%26Solution" in url
        assert "p=2" in url
        assert "rows=30" in url
        assert "sort=lastModifiedDate+desc" in url


class TestSearchUnit:
    """搜索模块单元测试"""

    @pytest.mark.asyncio
    async def test_perform_search_unit(self):
        """测试执行搜索功能"""
        # 创建模拟页面
        mock_page = AsyncMock()
        mock_selector = AsyncMock()

        # 设置模拟行为
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector.return_value = mock_selector

        # 模拟extract_search_results函数
        expected_results = [{"title": "测试结果", "url": "https://example.com"}]

        # 使用正确的方式模拟异步函数
        with patch(
            "woodgate.core.search.extract_search_results",
            new=AsyncMock(return_value=expected_results),
        ):
            with patch("woodgate.core.utils.handle_cookie_popup", new=AsyncMock()):
                # 调用被测试函数
                results = await perform_search(mock_page, "test query")

                # 验证结果
                assert results == expected_results

                # 验证调用
                mock_page.goto.assert_called_once()

    @pytest.mark.asyncio
    async def test_perform_search_no_results_unit(self):
        """测试执行搜索无结果的情况"""
        # 创建模拟页面
        mock_page = AsyncMock()

        # 设置模拟行为 - 等待选择器超时
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector.side_effect = TimeoutError("模拟超时")

        # 模拟no_results选择器
        mock_no_results = AsyncMock()

        # 设置query_selector在特定选择器时返回mock_no_results
        async def mock_query_selector(selector):
            if selector == ".no-results, .pf-c-empty-state":
                return mock_no_results
            return None

        mock_page.query_selector = AsyncMock(side_effect=mock_query_selector)

        with patch("woodgate.core.utils.handle_cookie_popup", new=AsyncMock()):
            # 调用被测试函数
            results = await perform_search(mock_page, "test query")

            # 验证结果
            assert results == []

    @pytest.mark.asyncio
    async def test_extract_search_results_unit(self):
        """测试提取搜索结果"""
        # 创建模拟页面
        mock_page = AsyncMock()

        # 模拟搜索结果元素
        mock_results = [AsyncMock(), AsyncMock()]
        mock_page.query_selector_all.return_value = mock_results

        # 设置第一个结果的属性
        async def mock_query_selector_1(selector):
            if selector == "h2 a, .pf-c-title a":
                mock = AsyncMock()
                mock.text_content = AsyncMock(return_value="测试标题1")
                mock.get_attribute = AsyncMock(return_value="https://example.com/1")
                return mock
            elif selector == ".search-result-content, .pf-c-card__body":
                mock = AsyncMock()
                mock.text_content = AsyncMock(return_value="测试摘要1")
                return mock
            elif selector == ".search-result-info span, .pf-c-label":
                mock = AsyncMock()
                mock.text_content = AsyncMock(return_value="解决方案")
                return mock
            elif selector == ".search-result-info time, .pf-c-label[data-testid='date']":
                mock = AsyncMock()
                mock.text_content = AsyncMock(return_value="2023-01-01")
                return mock
            return None

        # 设置第二个结果的属性
        async def mock_query_selector_2(selector):
            if selector == "h2 a, .pf-c-title a":
                mock = AsyncMock()
                mock.text_content = AsyncMock(return_value="测试标题2")
                mock.get_attribute = AsyncMock(return_value="https://example.com/2")
                return mock
            elif selector == ".search-result-content, .pf-c-card__body":
                mock = AsyncMock()
                mock.text_content = AsyncMock(return_value="测试摘要2")
                return mock
            elif selector == ".search-result-info span, .pf-c-label":
                mock = AsyncMock()
                mock.text_content = AsyncMock(return_value="文章")
                return mock
            elif selector == ".search-result-info time, .pf-c-label[data-testid='date']":
                mock = AsyncMock()
                mock.text_content = AsyncMock(return_value="2023-02-02")
                return mock
            return None

        mock_results[0].query_selector = AsyncMock(side_effect=mock_query_selector_1)
        mock_results[1].query_selector = AsyncMock(side_effect=mock_query_selector_2)

        # 调用被测试函数
        with patch("woodgate.core.search.log_step"):  # 忽略日志步骤
            results = await extract_search_results(mock_page)

        # 验证结果
        assert len(results) == 2
        assert results[0]["title"] == "测试标题1"
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["summary"] == "测试摘要1"

        assert results[1]["title"] == "测试标题2"
        assert results[1]["url"] == "https://example.com/2"
        assert results[1]["summary"] == "测试摘要2"

    @pytest.mark.asyncio
    async def test_get_document_content_unit(self):
        """测试获取文档内容"""
        # 创建模拟页面
        mock_page = AsyncMock()

        # 模拟文档元素
        mock_title = AsyncMock()
        mock_title.text_content = AsyncMock(return_value="文档标题")

        mock_content = AsyncMock()
        mock_content.text_content = AsyncMock(return_value="文档内容")

        # 设置模拟行为
        async def mock_query_selector(selector):
            if selector == "h1, .pf-c-title":
                return mock_title
            elif selector == ".field-item, .pf-c-content, article":
                return mock_content
            return None

        mock_page.query_selector = AsyncMock(side_effect=mock_query_selector)

        # 模拟元数据字段
        mock_metadata_fields = []
        mock_page.query_selector_all = AsyncMock(return_value=mock_metadata_fields)

        # 模拟等待选择器
        mock_page.wait_for_selector = AsyncMock()

        # 调用被测试函数
        with patch("woodgate.core.utils.handle_cookie_popup", new=AsyncMock()):
            document = await get_document_content(mock_page, "https://example.com/doc")

        # 验证结果
        assert document["title"] == "文档标题"
        assert document["content"] == "文档内容"
        assert document["url"] == "https://example.com/doc"
        assert "metadata" in document
