"""
配置模块测试
"""

import os
from unittest.mock import patch

from woodgate.config import get_available_products, get_config, get_credentials, get_document_types


class TestConfig:
    """配置模块测试"""

    def test_get_credentials_from_env(self):
        """测试从环境变量获取凭据"""
        with patch.dict(
            os.environ, {"REDHAT_USERNAME": "test_user", "REDHAT_PASSWORD": "test_pass"}
        ):
            username, password = get_credentials()
            assert username == "test_user"
            assert password == "test_pass"

    def test_get_credentials_default(self):
        """测试获取默认凭据"""
        with patch.dict(os.environ, {"WOODGATE_TEST_MODE": "true"}, clear=True):
            username, password = get_credentials()
            assert username == ""
            assert password == ""

    def test_get_config(self):
        """测试获取配置"""
        config = get_config()
        assert "headless" in config
        assert "browser_timeout" in config
        assert "default_rows" in config
        assert "default_sort" in config
        assert "host" in config
        assert "port" in config
        assert "log_level" in config
        assert "max_retries" in config
        assert "retry_delay" in config

    def test_get_config_with_env(self):
        """测试从环境变量获取配置"""
        with patch.dict(os.environ, {"WOODGATE_HEADLESS": "false"}):
            config = get_config()
            assert config["headless"] is False

    def test_get_available_products(self):
        """测试获取可用产品列表"""
        products = get_available_products()
        assert isinstance(products, list)
        assert len(products) > 0
        assert "Red Hat Enterprise Linux" in products

    def test_get_document_types(self):
        """测试获取文档类型列表"""
        doc_types = get_document_types()
        assert isinstance(doc_types, list)
        assert len(doc_types) > 0
        assert "Solution" in doc_types
        assert "Article" in doc_types
