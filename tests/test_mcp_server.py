"""
测试MCP服务器模块
"""

import os



def test_mcp_server_exists():
    """测试MCP服务器文件存在"""
    assert os.path.exists("mcp_server.py")


def test_mcp_server_imports():
    """测试MCP服务器导入语句"""
    with open("mcp_server.py", "r") as f:
        content = f.read()

    # 验证导入语句
    assert "import os" in content
    assert "import sys" in content
    assert "import logging" in content
    assert "import subprocess" in content
    assert "import importlib.util" in content


def test_mcp_server_package_check():
    """测试MCP服务器包检查功能"""
    with open("mcp_server.py", "r") as f:
        content = f.read()

    # 验证包检查逻辑
    assert "required_packages" in content
    assert "playwright" in content
    assert "importlib.util.find_spec" in content
    assert "subprocess.check_call" in content


def test_mcp_server_import_logic():
    """测试MCP服务器导入逻辑"""
    with open("mcp_server.py", "r") as f:
        content = f.read()

    # 验证导入逻辑
    assert "from woodgate.server import mcp" in content
    assert "import server" in content
    assert "mcp = server.mcp" in content


def test_mcp_server_run():
    """测试MCP服务器运行逻辑"""
    with open("mcp_server.py", "r") as f:
        content = f.read()

    # 验证运行逻辑
    assert 'if __name__ == "__main__":' in content
    assert "mcp.run" in content
    assert 'transport="sse"' in content
