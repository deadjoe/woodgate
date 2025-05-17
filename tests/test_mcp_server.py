"""
MCP服务器测试
"""

from unittest.mock import patch

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


class TestMCPServer:
    """MCP服务器测试"""

    def test_mcp_name(self):
        """测试MCP名称"""
        assert mcp.name == "Woodgate"

    def test_mcp_instance(self):
        """测试MCP实例"""
        assert mcp is not None
        assert hasattr(mcp, "name")
        assert mcp.name == "Woodgate"
        # 注意：FastMCP对象可能不会直接暴露version属性，所以我们不检查它

    def test_mcp_tool_decorator(self):
        """测试MCP工具装饰器"""
        # 验证工具装饰器存在
        assert hasattr(mcp, "tool")
        assert callable(mcp.tool)

    def test_search_function(self):
        """测试搜索函数"""
        # 验证搜索函数是可调用的
        assert callable(search)

    def test_get_alerts_function(self):
        """测试获取警报函数"""
        # 验证获取警报函数是可调用的
        assert callable(get_alerts)

    def test_get_document_function(self):
        """测试获取文档函数"""
        # 验证获取文档函数是可调用的
        assert callable(get_document)

    def test_available_products_function(self):
        """测试获取可用产品函数"""
        with patch("woodgate.server.get_available_products", return_value=["RHEL", "OpenShift"]):
            products = available_products()
            assert products == ["RHEL", "OpenShift"]

    def test_document_types_function(self):
        """测试获取文档类型函数"""
        with patch("woodgate.server.get_document_types", return_value=["Solution", "Article"]):
            doc_types = document_types()
            assert doc_types == ["Solution", "Article"]

    def test_search_params_function(self):
        """测试获取搜索参数函数"""
        with patch("woodgate.server.get_available_products", return_value=["RHEL", "OpenShift"]):
            with patch("woodgate.server.get_document_types", return_value=["Solution", "Article"]):
                params = search_params()
                assert "sort_options" in params
                assert "default_rows" in params
                assert "max_rows" in params
                assert "products" in params
                assert "doc_types" in params

    def test_search_help_function(self):
        """测试获取搜索帮助函数"""
        help_text = search_help()
        assert "Red Hat 客户门户搜索帮助" in help_text
        assert "query" in help_text
        assert "products" in help_text

    def test_search_example_function(self):
        """测试获取搜索示例函数"""
        example_text = search_example()
        assert "Red Hat 客户门户搜索示例" in example_text
        assert "基本搜索" in example_text
        assert "带产品过滤的搜索" in example_text
