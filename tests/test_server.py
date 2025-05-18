"""
服务器模块测试 - 包含基本测试、扩展测试和单元测试
"""

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
        # 检查mcp对象是否存在
        assert mcp is not None
        # 检查基本属性
        assert mcp.name == "Woodgate"
        # 注意：FastMCP对象可能不会直接暴露version和dependencies属性，所以我们不检查它们

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
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_browser_resources = (mock_playwright, mock_browser, mock_context, mock_page)
        mock_results = [{"title": "测试结果", "url": "https://example.com"}]

        # 模拟依赖函数
        with patch(
            "woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser_resources)
        ):
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
                        assert isinstance(results, list)
                        assert len(results) == 1
                        assert "title" in results[0] and "url" in results[0]
                        assert results[0]["title"] == mock_results[0]["title"]
                        assert results[0]["url"] == mock_results[0]["url"]

    @pytest.mark.asyncio
    async def test_search_login_failure(self):
        """测试搜索功能登录失败的情况"""
        # 模拟浏览器
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_browser_resources = (mock_playwright, mock_browser, mock_context, mock_page)

        # 模拟依赖函数
        with patch(
            "woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser_resources)
        ):
            with patch("woodgate.server.get_credentials", return_value=("test_user", "test_pass")):
                with patch(
                    "woodgate.server.login_to_redhat_portal", new=AsyncMock(return_value=False)
                ):
                    # 调用被测试函数
                    results = await search(query="test query")

                    # 验证结果 - 结果是一个列表，包含一个错误对象
                    assert isinstance(results, list)
                    assert len(results) == 1
                    assert "error" in results[0]
                    assert results[0]["error"] is not None
                    assert "登录失败" in results[0]["error"]

    @pytest.mark.asyncio
    async def test_search_exception(self):
        """测试搜索功能出现异常的情况"""
        # 模拟浏览器
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_browser_resources = (mock_playwright, mock_browser, mock_context, mock_page)

        # 模拟依赖函数
        with patch(
            "woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser_resources)
        ):
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
                        assert results[0]["error"] is not None
                        assert "测试异常" in results[0]["error"]

    @pytest.mark.asyncio
    async def test_search_browser_close_exception(self):
        """测试搜索功能关闭浏览器异常的情况"""
        # 模拟浏览器
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        # 设置quit抛出异常，确保同步和异步方法都抛出异常
        mock_browser.quit = MagicMock(side_effect=Exception("浏览器关闭异常"))
        mock_browser.quit.__await__ = MagicMock(side_effect=Exception("浏览器异步关闭异常"))
        mock_browser_resources = (mock_playwright, mock_browser, mock_context, mock_page)

        # 模拟依赖函数
        with patch(
            "woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser_resources)
        ):
            with patch("woodgate.server.get_credentials", return_value=("test_user", "test_pass")):
                with patch(
                    "woodgate.server.login_to_redhat_portal", new=AsyncMock(return_value=True)
                ):
                    with patch(
                        "woodgate.server.perform_search",
                        new=AsyncMock(return_value=[{"title": "测试结果"}]),
                    ):
                        with patch(
                            "woodgate.core.browser.close_browser",
                            side_effect=Exception("浏览器关闭异常"),
                        ):
                            with patch("woodgate.server.logger") as mock_logger:
                                # 调用被测试函数
                                results = await search(query="test query")

                                # 验证结果
                                assert isinstance(results, list)
                                assert len(results) == 1
                                assert "title" in results[0]
                                assert results[0]["title"] == "测试结果"

                                # 验证日志调用 - 使用assert_called而不是assert_called_once
                                assert mock_logger.warning.called

    @pytest.mark.asyncio
    async def test_get_alerts_success(self):
        """测试获取警报功能成功的情况"""
        # 模拟浏览器和警报结果
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_browser_resources = (mock_playwright, mock_browser, mock_context, mock_page)
        mock_alerts = [{"title": "测试警报", "severity": "严重"}]

        # 模拟依赖函数
        with patch(
            "woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser_resources)
        ):
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
                        assert isinstance(alerts, list)
                        assert len(alerts) == 1
                        assert "title" in alerts[0] and "severity" in alerts[0]
                        assert alerts[0]["title"] == mock_alerts[0]["title"]
                        assert alerts[0]["severity"] == mock_alerts[0]["severity"]

    @pytest.mark.asyncio
    async def test_get_alerts_login_failure(self):
        """测试获取警报功能登录失败的情况"""
        # 模拟浏览器
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_browser_resources = (mock_playwright, mock_browser, mock_context, mock_page)

        # 模拟依赖函数
        with patch(
            "woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser_resources)
        ):
            with patch("woodgate.server.get_credentials", return_value=("test_user", "test_pass")):
                with patch(
                    "woodgate.server.login_to_redhat_portal", new=AsyncMock(return_value=False)
                ):
                    # 调用被测试函数
                    result = await get_alerts("Red Hat Enterprise Linux")

                    # 验证结果
                    assert isinstance(result, list)
                    assert len(result) == 1
                    assert "error" in result[0]
                    assert result[0]["error"] is not None
                    assert "登录失败" in result[0]["error"]

    @pytest.mark.asyncio
    async def test_get_alerts_exception(self):
        """测试获取警报功能出现异常的情况"""
        # 模拟浏览器
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_browser_resources = (mock_playwright, mock_browser, mock_context, mock_page)

        # 模拟依赖函数
        with patch(
            "woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser_resources)
        ):
            with patch("woodgate.server.get_credentials", return_value=("test_user", "test_pass")):
                with patch(
                    "woodgate.server.login_to_redhat_portal", new=AsyncMock(return_value=True)
                ):
                    with patch(
                        "woodgate.server.get_product_alerts", side_effect=Exception("测试警报异常")
                    ):
                        # 调用被测试函数
                        result = await get_alerts("Red Hat Enterprise Linux")

                        # 验证结果
                        assert isinstance(result, list)
                        assert len(result) == 1
                        assert "error" in result[0]
                        assert result[0]["error"] is not None
                        assert "测试警报异常" in result[0]["error"]

    @pytest.mark.asyncio
    async def test_get_alerts_browser_close_exception(self):
        """测试获取警报功能关闭浏览器异常的情况"""
        # 模拟浏览器
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        # 设置quit抛出异常，确保同步和异步方法都抛出异常
        mock_browser.quit = MagicMock(side_effect=Exception("浏览器关闭异常"))
        mock_browser.quit.__await__ = MagicMock(side_effect=Exception("浏览器异步关闭异常"))
        mock_browser_resources = (mock_playwright, mock_browser, mock_context, mock_page)

        # 模拟依赖函数
        with patch(
            "woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser_resources)
        ):
            with patch("woodgate.server.get_credentials", return_value=("test_user", "test_pass")):
                with patch(
                    "woodgate.server.login_to_redhat_portal", new=AsyncMock(return_value=True)
                ):
                    with patch(
                        "woodgate.server.get_product_alerts",
                        new=AsyncMock(return_value=[{"title": "测试警报"}]),
                    ):
                        with patch(
                            "woodgate.core.browser.close_browser",
                            side_effect=Exception("浏览器关闭异常"),
                        ):
                            with patch("woodgate.server.logger") as mock_logger:
                                # 调用被测试函数
                                result = await get_alerts("Red Hat Enterprise Linux")

                                # 验证结果
                                assert isinstance(result, list)
                                assert len(result) == 1
                                assert "title" in result[0]
                                assert result[0]["title"] == "测试警报"

                                # 验证日志调用
                                assert mock_logger.warning.called

    @pytest.mark.asyncio
    async def test_get_document_success(self):
        """测试获取文档内容功能成功的情况"""
        # 模拟浏览器和文档内容
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_browser_resources = (mock_playwright, mock_browser, mock_context, mock_page)
        mock_document = {"title": "测试文档", "content": "测试内容"}

        # 模拟依赖函数
        with patch(
            "woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser_resources)
        ):
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
                        assert "title" in document and "content" in document
                        assert document["title"] == mock_document["title"]
                        assert document["content"] == mock_document["content"]

    @pytest.mark.asyncio
    async def test_get_document_login_failure(self):
        """测试获取文档内容功能登录失败的情况"""
        # 模拟浏览器
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_browser_resources = (mock_playwright, mock_browser, mock_context, mock_page)

        # 模拟依赖函数
        with patch(
            "woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser_resources)
        ):
            with patch("woodgate.server.get_credentials", return_value=("test_user", "test_pass")):
                with patch(
                    "woodgate.server.login_to_redhat_portal", new=AsyncMock(return_value=False)
                ):
                    # 调用被测试函数
                    result = await get_document("https://example.com/doc")

                    # 验证结果
                    assert "error" in result
                    assert result["error"] is not None
                    assert "登录失败" in result["error"]

    @pytest.mark.asyncio
    async def test_get_document_exception(self):
        """测试获取文档内容功能出现异常的情况"""
        # 模拟浏览器
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_browser_resources = (mock_playwright, mock_browser, mock_context, mock_page)

        # 模拟依赖函数
        with patch(
            "woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser_resources)
        ):
            with patch("woodgate.server.get_credentials", return_value=("test_user", "test_pass")):
                with patch(
                    "woodgate.server.login_to_redhat_portal", new=AsyncMock(return_value=True)
                ):
                    with patch(
                        "woodgate.server.get_document_content",
                        side_effect=Exception("测试文档异常"),
                    ):
                        # 调用被测试函数
                        result = await get_document("https://example.com/doc")

                        # 验证结果
                        assert "error" in result
                        assert result["error"] is not None
                        assert "测试文档异常" in result["error"]

    @pytest.mark.asyncio
    async def test_get_document_browser_close_exception(self):
        """测试获取文档内容功能关闭浏览器异常的情况"""
        # 模拟浏览器
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        # 设置quit抛出异常，确保同步和异步方法都抛出异常
        mock_browser.quit = MagicMock(side_effect=Exception("浏览器关闭异常"))
        mock_browser.quit.__await__ = MagicMock(side_effect=Exception("浏览器异步关闭异常"))
        mock_browser_resources = (mock_playwright, mock_browser, mock_context, mock_page)

        # 模拟依赖函数
        with patch(
            "woodgate.server.initialize_browser", new=AsyncMock(return_value=mock_browser_resources)
        ):
            with patch("woodgate.server.get_credentials", return_value=("test_user", "test_pass")):
                with patch(
                    "woodgate.server.login_to_redhat_portal", new=AsyncMock(return_value=True)
                ):
                    with patch(
                        "woodgate.server.get_document_content",
                        new=AsyncMock(return_value={"title": "测试文档"}),
                    ):
                        with patch(
                            "woodgate.core.browser.close_browser",
                            side_effect=Exception("浏览器关闭异常"),
                        ):
                            with patch("woodgate.server.logger") as mock_logger:
                                # 调用被测试函数
                                result = await get_document("https://example.com/doc")

                                # 验证结果
                                assert "title" in result
                                assert result["title"] == "测试文档"

                                # 验证日志调用
                                assert mock_logger.warning.called
