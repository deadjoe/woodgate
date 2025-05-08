"""
配置模块测试
"""

import os
from unittest.mock import patch

from woodgate.config import get_available_products, get_config, get_credentials, get_document_types


def test_get_credentials_from_env():
    """测试从环境变量获取凭据"""
    with patch.dict(os.environ, {"REDHAT_USERNAME": "test_user", "REDHAT_PASSWORD": "test_pass"}):
        username, password = get_credentials()
        assert username == "test_user"
        assert password == "test_pass"


def test_get_credentials_from_default():
    """测试从默认值获取凭据"""
    with patch.dict(os.environ, {"REDHAT_USERNAME": "", "REDHAT_PASSWORD": ""}):
        with patch.dict(
            os.environ,
            {"REDHAT_USERNAME_DEFAULT": "default_user", "REDHAT_PASSWORD_DEFAULT": "default_pass"},
        ):
            username, password = get_credentials()
            assert username == "default_user"
            assert password == "default_pass"


def test_get_credentials_warning():
    """测试凭据未设置时的警告"""
    with patch.dict(os.environ, {}, clear=True):
        with patch("woodgate.config.logger.warning") as mock_warning:
            username, password = get_credentials()
            assert username == ""
            assert password == ""
            mock_warning.assert_called_once()


def test_get_config():
    """测试获取配置"""
    with patch.dict(
        os.environ,
        {
            "WOODGATE_HEADLESS": "false",
            "WOODGATE_BROWSER_TIMEOUT": "30",
            "WOODGATE_DEFAULT_ROWS": "50",
            "WOODGATE_DEFAULT_SORT": "lastModifiedDate desc",
            "WOODGATE_HOST": "0.0.0.0",
            "WOODGATE_PORT": "9000",
            "WOODGATE_LOG_LEVEL": "DEBUG",
            "WOODGATE_MAX_RETRIES": "5",
            "WOODGATE_RETRY_DELAY": "5",
        },
    ):
        config = get_config()
        assert config["headless"] is False
        assert config["browser_timeout"] == 30
        assert config["default_rows"] == 50
        assert config["default_sort"] == "lastModifiedDate desc"
        assert config["host"] == "0.0.0.0"
        assert config["port"] == 9000
        assert config["log_level"] == "DEBUG"
        assert config["max_retries"] == 5
        assert config["retry_delay"] == 5


def test_get_config_defaults():
    """测试获取默认配置"""
    with patch.dict(os.environ, {}, clear=True):
        config = get_config()
        assert config["headless"] is True
        assert config["browser_timeout"] == 20
        assert config["default_rows"] == 20
        assert config["default_sort"] == "relevant"
        assert config["host"] == "127.0.0.1"
        assert config["port"] == 8000
        assert config["log_level"] == "INFO"
        assert config["max_retries"] == 3
        assert config["retry_delay"] == 3


def test_get_available_products():
    """测试获取可用产品列表"""
    products = get_available_products()
    assert isinstance(products, list)
    assert len(products) > 0
    assert "Red Hat Enterprise Linux" in products
    assert "Red Hat OpenShift Container Platform" in products


def test_get_document_types():
    """测试获取文档类型列表"""
    doc_types = get_document_types()
    assert isinstance(doc_types, list)
    assert len(doc_types) > 0
    assert "Solution" in doc_types
    assert "Article" in doc_types
