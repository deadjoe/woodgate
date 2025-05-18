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
