"""
异步测试辅助模块 - 提供解决未等待协程警告的辅助函数
"""

import asyncio
import inspect
from unittest.mock import AsyncMock

import pytest


def wrap_async_mock(mock_obj):
    """
    包装异步模拟对象，解决未等待协程的警告

    Args:
        mock_obj: 要包装的AsyncMock对象

    Returns:
        包装后的AsyncMock对象
    """
    original_methods = {}

    # 保存原始方法
    for name, method in inspect.getmembers(mock_obj, inspect.ismethod):
        if not name.startswith("_"):
            original_methods[name] = method

    # 包装方法
    for name, method in original_methods.items():

        async def wrapped_method(*args, _method=method, **kwargs):
            result = _method(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result

        setattr(mock_obj, name, wrapped_method)

    return mock_obj


class AsyncMethodMocker:
    """
    异步方法模拟器，用于解决未等待协程的警告

    使用示例:
    ```python
    @pytest.mark.asyncio
    async def test_async_function():
        with AsyncMethodMocker() as mocker:
            mock_obj = mocker.create_mock()
            mock_obj.method.return_value = "result"

            # 使用mock_obj...
    ```
    """

    def __init__(self):
        self.mocks = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 清理所有模拟对象
        self.mocks.clear()

    def create_mock(self):
        """创建一个包装后的AsyncMock对象"""
        mock = AsyncMock()
        wrapped_mock = wrap_async_mock(mock)
        self.mocks.append(wrapped_mock)
        return wrapped_mock


@pytest.fixture
def event_loop():
    """
    创建一个新的事件循环，用于异步测试

    这个fixture会在每个测试前创建一个新的事件循环，并在测试后关闭它
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
async def async_mock():
    """
    创建一个包装后的AsyncMock对象，用于异步测试

    使用示例:
    ```python
    @pytest.mark.asyncio
    async def test_function(async_mock):
        mock_obj = async_mock()
        mock_obj.method.return_value = "result"

        # 使用mock_obj...
    ```
    """

    def _create_async_mock():
        mock = AsyncMock()
        return wrap_async_mock(mock)

    return _create_async_mock
