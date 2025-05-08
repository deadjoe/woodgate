"""
Playwright浏览器模块测试
"""

from unittest.mock import AsyncMock, patch

import pytest

from server import close_browser, handle_cookie_popup, initialize_browser
from woodgate.core.search import (
    extract_search_results,
    get_document_content,
    get_product_alerts,
    perform_search,
)


@pytest.mark.asyncio
async def test_initialize_browser():
    """测试Playwright浏览器初始化函数"""
    # 模拟Playwright组件
    mock_playwright = AsyncMock()
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()

    # 设置模拟行为
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    # 模拟async_playwright函数
    with patch("server.async_playwright", return_value=AsyncMock()) as mock_async_playwright:
        # 设置模拟行为
        mock_async_playwright.return_value.start.return_value = mock_playwright

        # 调用被测试的函数
        playwright, browser, context, page = await initialize_browser()

        # 验证结果
        assert playwright == mock_playwright
        assert browser == mock_browser
        assert context == mock_context
        assert page == mock_page

        # 验证调用了正确的方法
        mock_async_playwright.return_value.start.assert_called_once()
        mock_playwright.chromium.launch.assert_called_once()
        mock_browser.new_context.assert_called_once()
        mock_context.new_page.assert_called_once()

        # 验证设置了正确的参数
        launch_args = mock_playwright.chromium.launch.call_args[1]
        assert launch_args["headless"] is True
        assert "--no-sandbox" in launch_args["args"]

        context_args = mock_browser.new_context.call_args[1]
        assert context_args["viewport"]["width"] == 1920
        assert context_args["viewport"]["height"] == 1080
        assert "user_agent" in context_args


@pytest.mark.asyncio
async def test_close_browser():
    """测试关闭Playwright浏览器函数"""
    # 模拟Playwright组件
    mock_playwright = AsyncMock()
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()

    # 调用被测试的函数
    await close_browser(mock_playwright, mock_browser, mock_context, mock_page)

    # 验证结果
    mock_page.close.assert_called_once()
    mock_context.close.assert_called_once()
    mock_browser.close.assert_called_once()
    mock_playwright.stop.assert_called_once()


@pytest.mark.asyncio
async def test_handle_cookie_popup():
    """测试处理Cookie弹窗函数"""
    # 模拟Page
    mock_page = AsyncMock()
    mock_cookie_notice = AsyncMock()

    # 场景1: 找到Cookie弹窗并成功点击
    mock_page.wait_for_selector.return_value = mock_cookie_notice

    # 调用被测试的函数
    result = await handle_cookie_popup(mock_page)

    # 验证结果
    assert result is True
    mock_page.wait_for_selector.assert_called()
    mock_cookie_notice.click.assert_called_once()

    # 场景2: 未找到Cookie弹窗，尝试通过文本查找按钮
    mock_page.wait_for_selector.side_effect = Exception("Element not found")
    mock_button = AsyncMock()
    mock_page.get_by_text.return_value.first.return_value = mock_button

    # 重置模拟对象
    mock_page.reset_mock()

    # 调用被测试的函数
    result = await handle_cookie_popup(mock_page)

    # 验证结果
    assert result is True
    mock_page.get_by_text.assert_called()
    mock_button.click.assert_called_once()

    # 场景3: 未找到任何Cookie弹窗或按钮
    mock_page.wait_for_selector.side_effect = Exception("Element not found")
    mock_page.get_by_text.return_value.first.return_value = None

    # 重置模拟对象
    mock_page.reset_mock()

    # 调用被测试的函数
    result = await handle_cookie_popup(mock_page)

    # 验证结果
    assert result is False


@pytest.mark.asyncio
async def test_extract_search_results():
    """测试提取搜索结果函数"""
    # 模拟Page和元素
    mock_page = AsyncMock()
    mock_result1 = AsyncMock()
    mock_result2 = AsyncMock()
    mock_title1 = AsyncMock()
    mock_title2 = AsyncMock()

    # 设置模拟行为
    mock_page.query_selector_all.return_value = [mock_result1, mock_result2]

    # 模拟第一个结果
    mock_result1.query_selector.side_effect = lambda selector: {
        "h2 a, .pf-c-title a": mock_title1,
        ".search-result-content, .pf-c-card__body": AsyncMock(
            text_content=AsyncMock(return_value="Summary 1")
        ),
        ".search-result-info span, .pf-c-label": AsyncMock(
            text_content=AsyncMock(return_value="Solution")
        ),
        ".search-result-info time, .pf-c-label[data-testid='date']": AsyncMock(
            text_content=AsyncMock(return_value="2023-01-01")
        ),
    }.get(selector, None)

    # 模拟第二个结果
    mock_result2.query_selector.side_effect = lambda selector: {
        "h2 a, .pf-c-title a": mock_title2,
        ".search-result-content, .pf-c-card__body": AsyncMock(
            text_content=AsyncMock(return_value="Summary 2")
        ),
        ".search-result-info span, .pf-c-label": AsyncMock(
            text_content=AsyncMock(return_value="Article")
        ),
        ".search-result-info time, .pf-c-label[data-testid='date']": AsyncMock(
            text_content=AsyncMock(return_value="2023-01-02")
        ),
    }.get(selector, None)

    # 模拟标题和URL
    mock_title1.text_content = AsyncMock(return_value="Test Result 1")
    mock_title1.get_attribute = AsyncMock(return_value="https://example.com/1")
    mock_title2.text_content = AsyncMock(return_value="Test Result 2")
    mock_title2.get_attribute = AsyncMock(return_value="https://example.com/2")

    # 调用被测试的函数
    results = await extract_search_results(mock_page)

    # 验证结果
    assert len(results) == 2
    assert results[0]["title"] == "Test Result 1"
    assert results[0]["url"] == "https://example.com/1"
    assert results[0]["summary"] == "Summary 1"
    assert results[0]["doc_type"] == "Solution"
    assert results[0]["last_updated"] == "2023-01-01"

    assert results[1]["title"] == "Test Result 2"
    assert results[1]["url"] == "https://example.com/2"
    assert results[1]["summary"] == "Summary 2"
    assert results[1]["doc_type"] == "Article"
    assert results[1]["last_updated"] == "2023-01-02"


@pytest.mark.asyncio
async def test_perform_search():
    """测试执行搜索函数"""
    # 模拟Page
    mock_page = AsyncMock()

    # 模拟搜索结果
    mock_results = [
        {"title": "Test Result 1", "url": "https://example.com/1"},
        {"title": "Test Result 2", "url": "https://example.com/2"},
    ]

    # 模拟函数
    with patch("woodgate.core.search.handle_cookie_popup") as mock_handle_cookie:
        with patch(
            "woodgate.core.search.extract_search_results", return_value=mock_results
        ) as mock_extract:
            # 调用被测试的函数
            results = await perform_search(
                mock_page,
                query="test query",
                products=["Test Product"],
                doc_types=["Test Type"],
            )

            # 验证结果
            assert results == mock_results
            mock_page.goto.assert_called_once()
            assert mock_handle_cookie.called
            mock_extract.assert_called_once_with(mock_page)


@pytest.mark.asyncio
async def test_get_product_alerts():
    """测试获取产品警报函数"""
    # 模拟Page
    mock_page = AsyncMock()

    # 模拟警报元素
    mock_alert1 = AsyncMock()
    mock_alert2 = AsyncMock()

    # 设置模拟行为
    mock_page.query_selector_all.return_value = [mock_alert1, mock_alert2]

    # 模拟第一个警报
    mock_alert1.query_selector.side_effect = lambda selector: {
        "h2 a, .pf-c-title a": AsyncMock(
            text_content=AsyncMock(return_value="Alert 1"),
            get_attribute=AsyncMock(return_value="https://example.com/alert1"),
        ),
        ".security-severity, .pf-c-label": AsyncMock(
            text_content=AsyncMock(return_value="Critical")
        ),
        ".portal-advisory-date, time": AsyncMock(text_content=AsyncMock(return_value="2023-01-01")),
        ".portal-advisory-synopsis, .pf-c-card__body": AsyncMock(
            text_content=AsyncMock(return_value="Alert 1 summary")
        ),
    }.get(selector, None)

    # 模拟第二个警报
    mock_alert2.query_selector.side_effect = lambda selector: {
        "h2 a, .pf-c-title a": AsyncMock(
            text_content=AsyncMock(return_value="Alert 2"),
            get_attribute=AsyncMock(return_value="https://example.com/alert2"),
        ),
        ".security-severity, .pf-c-label": AsyncMock(
            text_content=AsyncMock(return_value="Important")
        ),
        ".portal-advisory-date, time": AsyncMock(text_content=AsyncMock(return_value="2023-01-02")),
        ".portal-advisory-synopsis, .pf-c-card__body": AsyncMock(
            text_content=AsyncMock(return_value="Alert 2 summary")
        ),
    }.get(selector, None)

    # 调用被测试的函数
    with patch("woodgate.core.search.handle_cookie_popup"):
        alerts = await get_product_alerts(mock_page, "Red Hat Enterprise Linux")

    # 验证结果
    assert len(alerts) == 2
    assert alerts[0]["title"] == "Alert 1"
    assert alerts[0]["url"] == "https://example.com/alert1"
    assert alerts[0]["severity"] == "Critical"
    assert alerts[0]["published_date"] == "2023-01-01"
    assert alerts[0]["summary"] == "Alert 1 summary"

    assert alerts[1]["title"] == "Alert 2"
    assert alerts[1]["url"] == "https://example.com/alert2"
    assert alerts[1]["severity"] == "Important"
    assert alerts[1]["published_date"] == "2023-01-02"
    assert alerts[1]["summary"] == "Alert 2 summary"


@pytest.mark.asyncio
async def test_get_document_content():
    """测试获取文档内容函数"""
    # 模拟Page
    mock_page = AsyncMock()

    # 模拟文档元素
    mock_title = AsyncMock(text_content=AsyncMock(return_value="Document Title"))
    mock_content = AsyncMock(text_content=AsyncMock(return_value="Document Content"))

    # 模拟元数据字段
    mock_field = AsyncMock()
    mock_field.query_selector.side_effect = lambda selector: {
        ".field-label, .pf-c-description-list__term": AsyncMock(
            text_content=AsyncMock(return_value="Type:")
        ),
        ".field-item, .pf-c-description-list__description": AsyncMock(
            text_content=AsyncMock(return_value="Solution")
        ),
    }.get(selector, None)

    # 设置模拟行为
    mock_page.query_selector.side_effect = lambda selector: {
        "h1, .pf-c-title": mock_title,
        ".pf-c-content, .field-item, article": mock_content,
    }.get(selector, None)

    mock_page.query_selector_all.return_value = [mock_field]

    # 调用被测试的函数
    with patch("woodgate.core.search.handle_cookie_popup"):
        document = await get_document_content(mock_page, "https://example.com/doc")

    # 验证结果
    assert document["title"] == "Document Title"
    assert document["content"] == "Document Content"
    assert document["url"] == "https://example.com/doc"
    assert document["metadata"]["Type"] == "Solution"
