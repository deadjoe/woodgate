"""
配置模块 - 管理应用程序配置和环境变量
"""

import logging
import os
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


def get_credentials() -> Tuple[str, str]:
    """
    获取Red Hat客户门户的登录凭据

    优先使用环境变量，否则使用固定凭据

    Returns:
        Tuple[str, str]: 用户名和密码
    """
    # 从环境变量获取凭据
    username = os.environ.get("REDHAT_USERNAME")
    password = os.environ.get("REDHAT_PASSWORD")

    # 如果环境变量未设置，使用固定凭据
    if not username or not password:
        # 固定凭据，用于生产环境
        username = "smartjoe@gmail.com"
        password = "***REMOVED***"
        logger.info("使用固定凭据")
    else:
        logger.info("使用环境变量中的凭据")

    logger.debug(f"凭据获取成功: username='{username}'")
    return username, password


def get_config() -> Dict[str, Any]:
    """
    获取应用程序配置

    从环境变量和默认值构建配置字典

    Returns:
        Dict[str, Any]: 配置字典
    """
    config = {
        # 浏览器配置
        "headless": os.environ.get("WOODGATE_HEADLESS", "true").lower() == "true",
        "browser_timeout": int(os.environ.get("WOODGATE_BROWSER_TIMEOUT", "20")),
        # 搜索配置
        "default_rows": int(os.environ.get("WOODGATE_DEFAULT_ROWS", "20")),
        "default_sort": os.environ.get("WOODGATE_DEFAULT_SORT", "relevant"),
        # 服务器配置
        "host": os.environ.get("WOODGATE_HOST", "127.0.0.1"),
        "port": int(os.environ.get("WOODGATE_PORT", "8000")),
        # 日志配置
        "log_level": os.environ.get("WOODGATE_LOG_LEVEL", "INFO"),
        # 重试配置
        "max_retries": int(os.environ.get("WOODGATE_MAX_RETRIES", "3")),
        "retry_delay": int(os.environ.get("WOODGATE_RETRY_DELAY", "3")),
    }

    return config


def get_available_products() -> list[str]:
    """
    获取可用的产品列表

    Returns:
        list[str]: 产品列表
    """
    return [
        "Red Hat Enterprise Linux",
        "Red Hat OpenShift Container Platform",
        "Red Hat Virtualization",
        "Red Hat JBoss Enterprise Application Platform",
        "Red Hat Satellite",
        "Red Hat Ansible Automation Platform",
        "Red Hat OpenStack Platform",
        "Red Hat Ceph Storage",
        "Red Hat Gluster Storage",
        "Red Hat Decision Manager",
        "Red Hat Process Automation Manager",
        "Red Hat Data Grid",
        "Red Hat AMQ",
        "Red Hat Fuse",
        "Red Hat 3scale API Management",
        "Red Hat Single Sign-On",
        "Red Hat OpenShift Dedicated",
        "Red Hat OpenShift Online",
        "Red Hat OpenShift Service on AWS",
        "Red Hat Advanced Cluster Management for Kubernetes",
        "Red Hat Advanced Cluster Security for Kubernetes",
        "Red Hat Quay",
        "Red Hat CodeReady Containers",
        "Red Hat CodeReady Workspaces",
        "Red Hat Integration",
        "Red Hat Runtimes",
        "Red Hat Application Services",
        "Red Hat Middleware",
        "Red Hat Insights",
        "Red Hat Satellite Capsule",
        "Red Hat Directory Server",
        "Red Hat Certificate System",
        "Red Hat Identity Management",
        "Red Hat Enterprise Linux for SAP Solutions",
        "Red Hat Enterprise Linux for Real Time",
        "Red Hat Enterprise Linux for IBM Z",
        "Red Hat Enterprise Linux for Power",
        "Red Hat Enterprise Linux for ARM",
        "Red Hat Software Collections",
        "Red Hat Developer Toolset",
    ]


def get_document_types() -> list[str]:
    """
    获取可用的文档类型

    Returns:
        list[str]: 文档类型列表
    """
    return [
        "Solution",
        "Article",
        "Documentation",
        "Video",
        "Blog",
        "Product Documentation",
        "Knowledgebase",
        "Security Advisory",
        "Bug Fix",
        "Enhancement",
        "Reference Architecture",
        "Technical Brief",
        "White Paper",
        "FAQ",
        "Getting Started",
        "Installation Guide",
        "Administration Guide",
        "Developer Guide",
        "Release Notes",
        "Troubleshooting Guide",
    ]
