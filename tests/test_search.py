"""
搜索模块测试 - 包含基本测试、扩展测试和单元测试
"""

from unittest.mock import AsyncMock, patch

import pytest
from playwright.async_api import TimeoutError

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
    async def test_extract_search_results_exception(self):
        """测试提取搜索结果时的异常处理"""
        # 创建模拟页面
        mock_page = AsyncMock()

        # 设置query_selector_all抛出异常
        mock_page.query_selector_all = AsyncMock(side_effect=Exception("模拟异常"))
        mock_page.reload = AsyncMock()

        # 调用被测试函数
        with patch("woodgate.core.search.log_step"):  # 忽略日志步骤
            with patch("woodgate.core.search.logger"):  # 忽略日志
                with patch("woodgate.core.search.asyncio.sleep", new=AsyncMock()):  # 忽略sleep
                    results = await extract_search_results(mock_page)

        # 验证结果
        assert results == []
        assert mock_page.query_selector_all.call_count == 3  # 应该尝试3次
        assert mock_page.reload.call_count == 2  # 应该重新加载2次

    @pytest.mark.asyncio
    async def test_extract_search_results_no_results(self):
        """测试提取搜索结果时没有结果的情况"""
        # 创建模拟页面
        mock_page = AsyncMock()

        # 设置query_selector_all返回空列表
        mock_page.query_selector_all = AsyncMock(return_value=[])

        # 设置no_results选择器
        mock_no_results = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=mock_no_results)

        # 调用被测试函数
        with patch("woodgate.core.search.log_step"):  # 忽略日志步骤
            results = await extract_search_results(mock_page)

        # 验证结果
        assert results == []
        assert mock_page.query_selector_all.call_count == 1
        assert mock_page.query_selector.call_count == 1

    @pytest.mark.asyncio
    async def test_extract_search_results_retry_success(self):
        """测试提取搜索结果时重试成功的情况"""
        # 创建模拟页面
        mock_page = AsyncMock()

        # 设置query_selector_all第一次返回空列表，第二次返回结果
        mock_result = AsyncMock()

        # 设置结果的属性
        mock_title = AsyncMock()
        mock_title.text_content = AsyncMock(return_value="测试标题")
        mock_title.get_attribute = AsyncMock(return_value="https://example.com")

        mock_summary = AsyncMock()
        mock_summary.text_content = AsyncMock(return_value="测试摘要")

        mock_doc_type = AsyncMock()
        mock_doc_type.text_content = AsyncMock(return_value="解决方案")

        mock_date = AsyncMock()
        mock_date.text_content = AsyncMock(return_value="2023-01-01")

        async def mock_query_selector(selector):
            if selector == "h2 a, .pf-c-title a":
                return mock_title
            elif selector == ".search-result-content, .pf-c-card__body":
                return mock_summary
            elif selector == ".search-result-info span, .pf-c-label":
                return mock_doc_type
            elif selector == ".search-result-info time, .pf-c-label[data-testid='date']":
                return mock_date
            return None

        mock_result.query_selector = AsyncMock(side_effect=mock_query_selector)

        # 设置第一次调用返回空列表，第二次调用返回结果
        mock_page.query_selector_all = AsyncMock(side_effect=[[], [mock_result]])

        # 设置no_results选择器为None
        mock_page.query_selector = AsyncMock(return_value=None)
        mock_page.reload = AsyncMock()

        # 调用被测试函数
        with patch("woodgate.core.search.log_step"):  # 忽略日志步骤
            with patch("woodgate.core.search.asyncio.sleep", new=AsyncMock()):  # 忽略sleep
                results = await extract_search_results(mock_page)

        # 验证结果
        assert len(results) == 1
        assert results[0]["title"] == "测试标题"
        assert results[0]["url"] == "https://example.com"
        assert results[0]["summary"] == "测试摘要"
        assert results[0]["doc_type"] == "解决方案"
        assert results[0]["last_updated"] == "2023-01-01"

        assert mock_page.query_selector_all.call_count == 2
        assert mock_page.reload.call_count == 1

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
        mock_metadata_fields: list = []
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

    @pytest.mark.asyncio
    async def test_get_document_content_timeout(self):
        """测试获取文档内容时超时的情况"""
        # 创建模拟页面
        mock_page = AsyncMock()

        # 设置wait_for_selector抛出超时异常
        mock_page.wait_for_selector = AsyncMock(side_effect=TimeoutError("模拟超时"))

        # 调用被测试函数
        with patch("woodgate.core.utils.handle_cookie_popup", new=AsyncMock()):
            with patch("woodgate.core.search.log_step"):  # 忽略日志步骤
                document = await get_document_content(mock_page, "https://example.com/doc")

        # 验证结果
        assert "error" in document
        assert document["error"] == "无法加载文档内容"

    @pytest.mark.asyncio
    async def test_get_document_content_exception(self):
        """测试获取文档内容时出现异常的情况"""
        # 创建模拟页面
        mock_page = AsyncMock()

        # 设置goto抛出异常
        mock_page.goto = AsyncMock(side_effect=Exception("模拟异常"))

        # 调用被测试函数
        with patch("woodgate.core.search.log_step"):  # 忽略日志步骤
            with patch("woodgate.core.search.logger"):  # 忽略日志
                document = await get_document_content(mock_page, "https://example.com/doc")

        # 验证结果
        assert "error" in document
        assert "模拟异常" in document["error"]

    @pytest.mark.asyncio
    async def test_get_document_content_with_metadata(self):
        """测试获取带元数据的文档内容"""
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
        mock_field1 = AsyncMock()
        mock_field2 = AsyncMock()

        # 设置第一个字段的标签和值
        mock_label1 = AsyncMock()
        mock_label1.text_content = AsyncMock(return_value="产品")

        mock_value1 = AsyncMock()
        mock_value1.text_content = AsyncMock(return_value="Red Hat Enterprise Linux")

        async def mock_field1_query_selector(selector):
            if selector == ".field-label, .pf-c-description-list__term":
                return mock_label1
            elif selector == ".field-item, .pf-c-description-list__description":
                return mock_value1
            return None

        mock_field1.query_selector = AsyncMock(side_effect=mock_field1_query_selector)

        # 设置第二个字段的标签和值
        mock_label2 = AsyncMock()
        mock_label2.text_content = AsyncMock(return_value="版本")

        mock_value2 = AsyncMock()
        mock_value2.text_content = AsyncMock(return_value="8.0")

        async def mock_field2_query_selector(selector):
            if selector == ".field-label, .pf-c-description-list__term":
                return mock_label2
            elif selector == ".field-item, .pf-c-description-list__description":
                return mock_value2
            return None

        mock_field2.query_selector = AsyncMock(side_effect=mock_field2_query_selector)

        # 设置元数据字段列表
        mock_metadata_fields = [mock_field1, mock_field2]
        mock_page.query_selector_all = AsyncMock(return_value=mock_metadata_fields)

        # 模拟等待选择器
        mock_page.wait_for_selector = AsyncMock()

        # 调用被测试函数
        with patch("woodgate.core.utils.handle_cookie_popup", new=AsyncMock()):
            with patch("woodgate.core.search.log_step"):  # 忽略日志步骤
                document = await get_document_content(mock_page, "https://example.com/doc")

        # 验证结果
        assert document["title"] == "文档标题"
        assert document["content"] == "文档内容"
        assert document["url"] == "https://example.com/doc"
        assert "metadata" in document
        assert document["metadata"]["产品"] == "Red Hat Enterprise Linux"
        assert document["metadata"]["版本"] == "8.0"

    @pytest.mark.asyncio
    async def test_get_document_content_metadata_exception(self):
        """测试获取文档元数据时出现异常的情况"""
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

        # 设置query_selector_all抛出异常
        mock_page.query_selector_all = AsyncMock(side_effect=Exception("模拟元数据异常"))

        # 模拟等待选择器
        mock_page.wait_for_selector = AsyncMock()

        # 调用被测试函数
        with patch("woodgate.core.utils.handle_cookie_popup", new=AsyncMock()):
            with patch("woodgate.core.search.log_step"):  # 忽略日志步骤
                with patch("woodgate.core.search.logger"):  # 忽略日志
                    document = await get_document_content(mock_page, "https://example.com/doc")

        # 验证结果
        assert document["title"] == "文档标题"
        assert document["content"] == "文档内容"
        assert document["url"] == "https://example.com/doc"
        assert "metadata" in document
        assert document["metadata"] == {}

    @pytest.mark.asyncio
    async def test_get_product_alerts(self):
        """测试获取产品警报（已弃用的函数）"""
        # 创建模拟页面
        mock_page = AsyncMock()

        # 调用被测试函数
        with patch("woodgate.core.search.logger"):  # 忽略日志
            alerts = await get_product_alerts(mock_page, "Red Hat Enterprise Linux")

        # 验证结果 - 应该返回空列表，因为函数已弃用
        assert alerts == []

    @pytest.mark.asyncio
    async def test_perform_search_exception(self):
        """测试执行搜索时出现异常的情况"""
        # 创建模拟页面
        mock_page = AsyncMock()

        # 设置goto抛出异常
        mock_page.goto = AsyncMock(side_effect=Exception("模拟搜索异常"))

        # 调用被测试函数
        with patch("woodgate.core.search.log_step"):  # 忽略日志步骤
            with patch("woodgate.core.search.logger"):  # 忽略日志
                results = await perform_search(mock_page, "test query")

        # 验证结果
        assert results == []
        mock_page.goto.assert_called_once()
