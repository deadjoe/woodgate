"""
服务器模块测试 - 包含基本测试、扩展测试和单元测试
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from woodgate.server import (
    available_products,
    document_types,
    get_alerts,
    get_document,
    mcp,
    search,
    search_example,
    search_help,
    search_params,
)


class TestServerBasic:
    """服务器模块基本测试"""

    def test_mcp_server_initialization(self):
        """测试MCP服务器初始化"""
        # 只检查name属性，因为FastMCP对象可能没有其他属性
        assert mcp.name == "Woodgate"
        # 检查mcp对象是否存在
        assert mcp is not None

    def test_available_products(self):
        """测试获取可用产品列表"""
        with patch("woodgate.server.get_available_products", return_value=["RHEL", "OpenShift"]):
            products = available_products()
            assert products == ["RHEL", "OpenShift"]

    def test_document_types(self):
        """测试获取文档类型列表"""
        with patch("woodgate.server.get_document_types", return_value=["Solution", "Article"]):
            doc_types = document_types()
            assert doc_types == ["Solution", "Article"]

    def test_search_params(self):
        """测试获取搜索参数配置"""
        with patch("woodgate.server.get_available_products", return_value=["RHEL", "OpenShift"]):
            with patch("woodgate.server.get_document_types", return_value=["Solution", "Article"]):
                params = search_params()
                assert "sort_options" in params
                assert "default_rows" in params
                assert "max_rows" in params
                assert "products" in params
                assert "doc_types" in params
                assert params["products"] == ["RHEL", "OpenShift"]
                assert params["doc_types"] == ["Solution", "Article"]

    def test_search_help(self):
        """测试获取搜索帮助信息"""
        help_text = search_help()
        assert "Red Hat 客户门户搜索帮助" in help_text
        assert "query" in help_text
        assert "products" in help_text
        assert "doc_types" in help_text
        assert "page" in help_text
        assert "rows" in help_text
        assert "sort_by" in help_text

    def test_search_example(self):
        """测试获取搜索示例"""
        example_text = search_example()
        assert "Red Hat 客户门户搜索示例" in example_text
        assert "基本搜索" in example_text
        assert "带产品过滤的搜索" in example_text
        assert "带文档类型过滤的搜索" in example_text
        assert "完整搜索示例" in example_text
        assert "获取产品警报" in example_text
        assert "获取文档内容" in example_text


class TestServerUnit:
    """服务器模块单元测试"""

    @pytest.mark.asyncio
    async def test_search_success(self):
        """测试搜索功能成功的情况"""
        # 模拟浏览器和搜索结果
        mock_browser = AsyncMock()
        mock_results = [{"title": "测试结果", "url": "https://example.com"}]

        # 模拟依赖函数
        with patch("woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser)):
            with patch("woodgate.server.get_credentials", return_value=("test_user", "test_pass")):
                with patch(
                    "woodgate.server.login_to_redhat_portal", new=AsyncMock(return_value=True)
                ):
                    with patch(
                        "woodgate.server.perform_search", new=AsyncMock(return_value=mock_results)
                    ):
                        # 调用被测试函数
                        results = await search(query="test query")

                        # 验证结果
                        assert results == mock_results

    @pytest.mark.asyncio
    async def test_search_login_failure(self):
        """测试搜索功能登录失败的情况"""
        # 模拟浏览器
        mock_browser = AsyncMock()

        # 模拟依赖函数
        with patch("woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser)):
            with patch("woodgate.server.get_credentials", return_value=("test_user", "test_pass")):
                with patch(
                    "woodgate.server.login_to_redhat_portal", new=AsyncMock(return_value=False)
                ):
                    # 调用被测试函数
                    results = await search(query="test query")

                    # 验证结果 - 结果是一个字典，不是列表
                    assert isinstance(results, dict)
                    assert "error" in results
                    assert "登录失败" in results["error"]

    @pytest.mark.asyncio
    async def test_search_exception(self):
        """测试搜索功能出现异常的情况"""
        # 模拟浏览器
        mock_browser = AsyncMock()

        # 模拟依赖函数
        with patch("woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser)):
            with patch("woodgate.server.get_credentials", return_value=("test_user", "test_pass")):
                with patch(
                    "woodgate.server.login_to_redhat_portal", new=AsyncMock(return_value=True)
                ):
                    with patch("woodgate.server.perform_search", side_effect=Exception("测试异常")):
                        # 调用被测试函数
                        results = await search(query="test query")

                        # 验证结果
                        assert isinstance(results, list)
                        assert len(results) == 1
                        assert "error" in results[0]
                        assert "测试异常" in results[0]["error"]

    @pytest.mark.asyncio
    async def test_get_alerts_success(self):
        """测试获取警报功能成功的情况"""
        # 模拟浏览器和警报结果
        mock_browser = AsyncMock()
        mock_alerts = [{"title": "测试警报", "severity": "严重"}]

        # 模拟依赖函数
        with patch("woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser)):
            with patch("woodgate.server.get_credentials", return_value=("test_user", "test_pass")):
                with patch(
                    "woodgate.server.login_to_redhat_portal", new=AsyncMock(return_value=True)
                ):
                    with patch(
                        "woodgate.server.get_product_alerts",
                        new=AsyncMock(return_value=mock_alerts),
                    ):
                        # 调用被测试函数
                        alerts = await get_alerts("Red Hat Enterprise Linux")

                        # 验证结果
                        assert alerts == mock_alerts

    @pytest.mark.asyncio
    async def test_get_document_success(self):
        """测试获取文档内容功能成功的情况"""
        # 模拟浏览器和文档内容
        mock_browser = AsyncMock()
        mock_document = {"title": "测试文档", "content": "测试内容"}

        # 模拟依赖函数
        with patch("woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser)):
            with patch("woodgate.server.get_credentials", return_value=("test_user", "test_pass")):
                with patch(
                    "woodgate.server.login_to_redhat_portal", new=AsyncMock(return_value=True)
                ):
                    with patch(
                        "woodgate.server.get_document_content",
                        new=AsyncMock(return_value=mock_document),
                    ):
                        # 调用被测试函数
                        document = await get_document("https://example.com/doc")

                        # 验证结果
                        assert document == mock_document
