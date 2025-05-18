"""
MCP模拟模块 - 提供MCP类的模拟实现，用于测试
"""


class MCP:
    """
    MCP类的模拟实现，用于测试
    """

    def __init__(self):
        self.tools = {}
        self.resources = {}
        self.prompts = {}
        self.name = "Woodgate"
        self.description = "Red Hat客户门户搜索工具"
        self.version = "1.0.0"

        # 添加settings属性，用于兼容FastMCP
        class Settings:
            def __init__(self):
                self.host = "127.0.0.1"
                self.port = 8000
                self.log_level = "INFO"

        self.settings = Settings()

    def tool(self, *args, **kwargs):
        """
        工具装饰器
        """

        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator

    def resource(self, path):
        """
        资源装饰器
        """

        def decorator(func):
            self.resources[path] = func
            return func

        return decorator

    def prompt(self, *args, **kwargs):
        """
        提示装饰器
        """

        def decorator(func):
            self.prompts[func.__name__] = func
            return func

        return decorator

    def run(self, transport=None):
        """
        模拟运行MCP服务器

        Args:
            transport: 传输方式，例如 "sse"
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"模拟MCP服务器启动 (transport={transport}, host={self.settings.host}, port={self.settings.port})"
        )
        logger.info("这是一个模拟实现，不会真正启动服务器")
        print(
            f"模拟MCP服务器启动 (transport={transport}, host={self.settings.host}, port={self.settings.port})"
        )
        print("这是一个模拟实现，不会真正启动服务器")
