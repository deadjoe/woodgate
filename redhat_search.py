from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
import time
import json
import re
import traceback

# 全局配置参数
DEFAULT_RESULTS_COUNT = 20  # 默认提取的搜索结果数量，用于控制每次搜索返回的结果条数

def log_step(message):
    """打印带时间戳的日志信息
    
    Args:
        message (str): 要打印的信息
    """
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"[{current_time}] {message}")

def print_cookies(driver, step_name=""):
    """打印当前浏览器中的所有Cookie信息
    
    Args:
        driver (WebDriver): Selenium WebDriver实例
        step_name (str): 当前步骤名称，用于日志
    """
    log_step(f"===== Cookie诊断信息 ({step_name}) =====")
    cookies = driver.get_cookies()
    log_step(f"共有 {len(cookies)} 个Cookie")
    
    auth_cookies = []
    session_cookies = []
    other_cookies = []
    
    for cookie in cookies:
        cookie_info = f"名称: {cookie.get('name')}, 值: {cookie.get('value')[:10] if cookie.get('value') and len(cookie.get('value')) > 10 else cookie.get('value')}, 域: {cookie.get('domain')}"
        
        # 根据Cookie名称分类，便于诊断会话状态和认证问题
        # auth/token类Cookie关系到用户认证状态
        # session类Cookie关系到会话维持
        # 其他Cookie通常不影响关键功能
        if 'auth' in cookie.get('name', '').lower() or 'token' in cookie.get('name', '').lower():
            auth_cookies.append(cookie_info)
        elif 'session' in cookie.get('name', '').lower():
            session_cookies.append(cookie_info)
        else:
            other_cookies.append(cookie_info)
    
    if auth_cookies:
        log_step("认证相关Cookie:")
        for cookie in auth_cookies:
            log_step(f"  - {cookie}")
    
    if session_cookies:
        log_step("会话相关Cookie:")
        for cookie in session_cookies:
            log_step(f"  - {cookie}")
    
    log_step("其他Cookie数量: " + str(len(other_cookies)))
    log_step("============================")

# 搜索示例配置 - 单一示例用于测试
SEARCH_EXAMPLES = [
    {
        "query": "memory leak",
        "products": ["Red Hat Enterprise Linux", "Red Hat OpenShift"],
        "doc_types": ["Solution", "Article"],
        "page": 1,
        "rows": 20,
	"sort_by": "relevant"  # 添加排序参数，默认为相关性排序
	# "sort_by": "lastModifiedDate desc"  # 添加排序参数，默认为相关性排序
	# "sort_by": "lastModifiedDate asc"
    }
]

# 获取环境变量中的凭据
REDHAT_USERNAME = os.environ.get("REDHAT_USERNAME")
REDHAT_PASSWORD = os.environ.get("REDHAT_PASSWORD")

# 如果环境变量未设置，使用备用凭据（安全风险）
if not REDHAT_USERNAME or not REDHAT_PASSWORD:
    REDHAT_USERNAME = "smartjoe@gmail.com"  # 示例值，请替换为您的实际凭据
    REDHAT_PASSWORD = "***REMOVED***"  # 示例值，请替换为您的实际凭据
    log_step("警告：使用了硬编码的凭据。这存在安全风险，建议使用环境变量。")

def build_search_url(query, products, doc_types, page=1, rows=10, sort_by="relevant"):
    """构建搜索URL
    
    Args:
        query (str): 搜索关键词
        products (list): 产品过滤列表
        doc_types (list): 文档类型过滤列表
        page (int, optional): 页码. Defaults to 1.
        rows (int, optional): 每页结果数. Defaults to 10.
        sort_by (str, optional): 排序方式. Defaults to "relevant".
    
    Returns:
        str: 完整的搜索URL
    """
    base_url = "https://access.redhat.com/search/?"
    params = {
        "q": query.replace(" ", "+"),
        "p": page,
        "rows": rows,
        "product": "%26".join(p.replace(" ", "+") for p in products),
        "documentKind": "%26".join(d.replace(" ", "+") for d in doc_types),
        "sort": sort_by.replace(" ", "+")  # 将排序参数中的空格替换为+
    }
    return base_url + "&".join(f"{k}={v}" for k, v in params.items())

def handle_cookie_popup(driver, timeout=0.5):
    """处理网页上出现的cookie或隐私弹窗
    
    Args:
        driver (WebDriver): Selenium WebDriver实例
        timeout (float, optional): 等待弹窗出现的超时时间. Defaults to 0.5.
        
    Returns:
        bool: 如果成功处理了弹窗返回True，否则返回False
    
    注意:
        此函数使用优化的选择器和更短的超时时间，提高处理效率
    """
    log_step("检查是否存在cookie通知...")

    try:
        # 优化：使用更高效的CSS选择器，减少DOM查询次数
        popup_selectors = [
            "#onetrust-banner-sdk",        # 最常见的
            ".pf-c-modal-box",            # Red Hat特有的
            "[role='dialog'][aria-modal='true']"  # 通用备选
        ]

        cookie_notice = None
        for selector in popup_selectors:
            try:
                cookie_notice = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                log_step(f"发现cookie通知，使用选择器: {selector}")
                break
            except:
                continue

        if not cookie_notice:
            log_step("未发现cookie通知")
            return False

        # 优化：减少选择器数量，优先使用更常见的按钮选择器
        close_buttons = [
            "button.pf-c-button[aria-label='Close']",
            "#onetrust-accept-btn-handler",
            "button.pf-c-button.pf-m-primary",
            ".close-button",
            "button[aria-label='Close']"
        ]

        # 先尝试在cookie通知元素内查找关闭按钮
        for selector in close_buttons:
            try:
                close_button = cookie_notice.find_element(By.CSS_SELECTOR, selector)
                log_step(f"在cookie通知中找到关闭按钮，使用选择器: {selector}")
                # 使用JavaScript点击避免元素被拦截问题
                driver.execute_script("arguments[0].click();", close_button)
                log_step("已使用JavaScript点击关闭按钮")
                return True
            except:
                continue

        # 尝试通过文本内容查找按钮
        for button_text in ["Accept", "I agree", "Close", "OK", "接受", "同意", "关闭"]:
            try:
                button = driver.find_element(By.XPATH, f"//button[contains(text(), '{button_text}')]")
                log_step(f"找到文本为'{button_text}'的按钮")
                driver.execute_script("arguments[0].click();", button)
                log_step("已使用JavaScript点击按钮")
                return True
            except:
                continue

        log_step("无法找到关闭按钮，可能需要手动关闭")
        return False

    except Exception as e:
        log_step(f"处理cookie通知时出错: {e}")
        return False

def extract_search_results(driver, num_results=DEFAULT_RESULTS_COUNT):
    """从搜索结果页面提取前n条结果
    
    Args:
        driver (WebDriver): Selenium WebDriver实例
        num_results (int, optional): 要提取的结果数量. Defaults to DEFAULT_RESULTS_COUNT.
    
    Returns:
        list: 包含结果信息的字典列表，每个字典包含标题、URL、类型和描述
    """
    log_step(f"开始提取前{num_results}条搜索结果...")
    
    # 记录当前URL和页面标题，帮助诊断
    log_step(f"当前URL: {driver.current_url}")
    log_step(f"当前页面标题: {driver.title}")
    
    # 输出提取结果前的Cookie状态，用于诊断可能的会话问题
    print_cookies(driver, "提取搜索结果前")
    
    # 处理可能的认证重定向
    if "Login - Red Hat Customer Portal" in driver.title or "scribe" in driver.current_url:
        log_step("检测到重定向到登录页面，等待重定向完成...")
        time.sleep(3)
        
        # 如果仍在登录页面，尝试通过刷新页面解决
        if "Login" in driver.title:
            log_step("尝试刷新页面...")
            driver.refresh()
            time.sleep(3)
            log_step(f"刷新后页面标题: {driver.title}")
    
    # 等待页面加载
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        log_step("页面主体已加载")
    except Exception as e:
        log_step(f"等待页面加载时出错: {e}")
        return []
    
    # 尝试滚动页面以触发懒加载
    try:
        driver.execute_script("window.scrollTo(0, 300)")
        time.sleep(1)  # 短暂等待加载
    except Exception as e:
        log_step(f"滚动页面时出错: {e}")
    
    # 尝试获取result-item元素
    try:
        result_items = driver.find_elements(By.TAG_NAME, "result-item")
        log_step(f"找到{len(result_items)}个result-item元素")
        
        if not result_items:
            # 尝试其他可能的选择器
            result_items = driver.find_elements(By.CSS_SELECTOR, "[data-testid='result-item']")
            log_step(f"使用data-testid选择器找到{len(result_items)}个元素")
    except Exception as e:
        log_step(f"查找result-item元素时出错: {e}")
        return []
    
    if not result_items:
        log_step("未找到搜索结果元素")
        return []
    
    # 提取数据
    results = []
    for i, item in enumerate(result_items[:num_results]):
        try:
            # 获取data属性
            data_json = item.get_attribute("data")
            if not data_json:
                log_step(f"结果{i+1}没有data属性")
                continue
            
            # 解析JSON数据
            data = json.loads(data_json)
            card_data = data.get("cardData", {})
            
            # 按JSON中字段顺序提取所有字段，保持原始数据不变
            result = {
                # 保留cardData中所有原始字段和值
                "snippet": card_data.get("snippet", ""),
                "documentKind": card_data.get("documentKind", "未知类型"),
                "publishedTitle": card_data.get("publishedTitle", "无标题"),
                "lastModifiedDate": card_data.get("lastModifiedDate", ""),
                "publishedAbstract": card_data.get("publishedAbstract", ""),
                "abstract": card_data.get("abstract", ""),
                "ModerationState": card_data.get("ModerationState", ""),
                "uri": card_data.get("uri", ""),
                "requires_subscription": card_data.get("requires_subscription", False),
                "standard_product": card_data.get("standard_product", []),
                "allTitle": card_data.get("allTitle", ""),
                "id": card_data.get("id", ""),
                "view_uri": card_data.get("view_uri", ""),
                "highlightedText": card_data.get("highlightedText", []),
                "position": card_data.get("position", 0),
                "displayFeature": card_data.get("displayFeature", ""),
                # 保留顶层字段
                "isAuthenticated": data.get("isAuthenticated", False)
            }
            
            results.append(result)
            
            log_step(f"已提取第{i+1}条结果: {result.get('publishedTitle', '无标题')}")
        except Exception as e:
            log_step(f"提取第{i+1}条结果时出错: {e}")
            
            # 记录错误详细信息以便调试
            log_step(f"错误详情: {traceback.format_exc()}")
    
    log_step(f"成功提取了{len(results)}条搜索结果")
    return results

def test_redhat_portal_login():
    log_step("开始测试红帽门户登录和搜索功能...")
    
    # 配置Chrome选项 - 优化浏览器性能
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 启用无头模式，不显示浏览器窗口，提高运行效率
    chrome_options.add_argument("--no-sandbox")  # 禁用沙箱，解决某些环境下的权限问题
    chrome_options.add_argument("--disable-dev-shm-usage")  # 解决在低内存环境中的崩溃问题
    chrome_options.add_argument("--window-size=1920,1080")  # 设置窗口大小，模拟标准显示器分辨率
    
    # 优化：添加性能优化选项
    chrome_options.add_argument("--disable-extensions")  # 禁用扩展，减少资源占用和干扰
    chrome_options.add_argument("--disable-gpu")  # 禁用GPU加速，提高在服务器环境下的兼容性
    chrome_options.add_argument("--disable-infobars")  # 禁用信息栏，避免干扰自动化操作
    chrome_options.add_argument("--disable-notifications")  # 禁用通知，避免弹窗干扰
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # 禁用图片加载，加快页面处理速度
    chrome_options.page_load_strategy = 'eager'  # 使用eager加载策略，DOM就绪后立即返回，不等待所有资源
    
    log_step("初始化Chrome浏览器...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                              options=chrome_options)
    
    # 设置页面加载超时时间
    driver.set_page_load_timeout(20)
    # 设置脚本执行超时时间
    driver.set_script_timeout(10)

    try:
        # 访问登录页面
        log_step("访问红帽登录页面...")
        driver.get("https://access.redhat.com/login")

        # 优化：使用显式等待替代固定等待
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # 输出登录页面的Cookie状态，用于诊断潜在的会话问题和跟踪认证流程
        print_cookies(driver, "登录页面")

        # 处理cookie通知
        handle_cookie_popup(driver)

        # 使用全局变量中的用户名和密码 (避免重复获取逻辑)
        username = REDHAT_USERNAME
        password = REDHAT_PASSWORD

        # 输入用户名 - 使用更精确的选择器
        log_step("尝试输入用户名...")
        username_field = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='text'], input[name='username'], input#username"))
        )
        username_field.clear()
        username_field.send_keys(username)
        log_step("已输入用户名")

        # 点击Next按钮 - 优化选择器
        log_step("点击Next按钮...")
        next_button_selectors = [
            "//button[text()='Next']",
            "//button[contains(text(), 'Next')]",
            "//button[@type='submit']"
        ]
        
        next_button = None
        for selector in next_button_selectors:
            try:
                next_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                break
            except:
                continue
                
        if next_button:
            driver.execute_script("arguments[0].click();", next_button)
            log_step("已点击Next按钮")
        else:
            log_step("未找到Next按钮")
            
        # 优化：等待密码字段出现，而不是固定等待
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password'], input[name='password']"))
        )

        # 输出密码页面的Cookie状态，用于诊断可能的会话问题和跟踪认证流程
        print_cookies(driver, "密码页面")

        # 再次处理cookie通知
        handle_cookie_popup(driver)

        # 输入密码 - 使用更精确的选择器
        log_step("尝试输入密码...")
        password_field = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password'], input[name='password'], input#password"))
        )
        password_field.clear()
        password_field.send_keys(password)
        log_step("已输入密码")

        # 点击登录按钮
        log_step("尝试点击登录按钮...")

        # 优化：减少选择器数量，使用更精确的选择器
        login_selectors = [
            "//button[@type='submit']",    # 最常用的
            "//button[text()='Log in']",   # 精确匹配
            "//input[@type='submit']"      # 备选方案
        ]

        login_button = None

        for selector in login_selectors:
            try:
                login_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                log_step(f"找到登录按钮，使用选择器: {selector}")
                break
            except:
                continue

        if login_button:
            # 使用JavaScript点击，避免被覆盖的问题
            driver.execute_script("arguments[0].click();", login_button)
            log_step("已使用JavaScript点击登录按钮")
        else:
            log_step("未找到登录按钮")

        # 输出登录后的Cookie状态，用于诊断可能的会话问题和跟踪认证流程
        print_cookies(driver, "登录后")

        # 使用域名变化检测登录状态
        log_step("等待登录完成并验证登录状态...")
        try:
            # 尝试多种方式验证登录状态
            success = False
            
            # 方法1：检查URL变化
            try:
                WebDriverWait(driver, 15).until(
                    lambda d: "access.redhat.com" in d.current_url
                )
                log_step("检测到域名已切换到access.redhat.com，登录成功！")
                success = True
            except Exception as e:
                log_step(f"通过URL检测登录失败: {e}")
            
            # 方法2：检查页面元素
            if not success:
                try:
                    # 尝试找到登录后才会出现的元素
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".pf-c-page__header, .rh-header, .rh-user-menu"))
                    )
                    log_step("检测到登录后的页面元素，登录成功！")
                    success = True
                except Exception as e:
                    log_step(f"通过页面元素检测登录失败: {e}")
            
            # 方法3：检查Cookie
            if not success:
                cookies = driver.get_cookies()
                rh_sso_cookie = any("rh_sso" in cookie.get('name', '') for cookie in cookies)
                if rh_sso_cookie:
                    log_step("检测到rh_sso Cookie，登录成功！")
                    success = True
            
            # 登录未成功，尝试直接访问搜索页面
            if not success:
                log_step("未能通过标准方式确认登录状态，尝试直接访问搜索页面...")
                # 直接跳转到搜索页面
                driver.get("https://access.redhat.com/search")
                
                # 等待页面加载
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 检查当前URL是否包含sso（表示被重定向回登录页面）
                if "sso.redhat.com" in driver.current_url:
                    log_step("被重定向回登录页面，登录失败")
                    return False
                
                log_step("已直接导航至搜索页面")
                success = True
            
            if not success:
                log_step("所有登录验证方法均失败")
                return False
        except Exception as e:
            log_step(f"登录验证过程中出错: {e}")
            log_step(f"当前URL: {driver.current_url}")
            log_step(f"当前页面标题: {driver.title}")
            log_step("登录失败，请检查用户名密码是否正确")
            return False

        log_step("\n开始执行搜索测试...")
        # 访问搜索主页
        driver.get("https://access.redhat.com/search")
        log_step("已进入搜索页面")

        # 输出搜索页面的Cookie状态，用于诊断可能的会话问题和跟踪认证流程
        print_cookies(driver, "搜索页面")

        # 执行示例搜索
        for i, example in enumerate(SEARCH_EXAMPLES, 1):
            log_step(f"\n执行第{i}个搜索示例：{example['query']}")
            search_url = build_search_url(
                example["query"],
                example["products"],
                example["doc_types"],
                page=example.get("page", 1),    # 使用配置中的分页，默认为1
                rows=example.get("rows", 10),   # 使用配置中的行数，默认为10
                sort_by=example.get("sort_by", "relevant")  # 使用配置中的排序，默认为相关性排序
            )
            log_step(f"已构建搜索URL: {search_url}")
            driver.get(search_url)
            
            # 等待页面加载完成
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 输出搜索结果页面的Cookie状态，用于诊断可能的会话问题和跟踪认证流程
            print_cookies(driver, "搜索结果页面")

            # 处理可能出现的cookie弹窗
            handle_cookie_popup(driver)
            
            log_step(f"已完成第{i}个搜索，当前URL：{driver.current_url}")
            
            # 提取搜索结果（增加重试机制）
            # 设置最大重试次数，防止因网络波动、页面加载延迟或DOM结构变化导致的提取失败
            # 在每次重试前会刷新页面并等待，增加成功率
            max_retries = 3  # 最大重试次数，防止网络波动或页面加载延迟导致的提取失败
            search_results = []
            
            for retry in range(max_retries):
                # 尝试提取搜索结果，直接使用全局默认值
                search_results = extract_search_results(driver, DEFAULT_RESULTS_COUNT)
                
                # 检查是否成功提取结果
                if search_results and len(search_results) > 0:
                    log_step(f"成功提取到{len(search_results)}条搜索结果")
                    break
                
                # 如果未提取到结果且未达到最大重试次数，则等待后重试
                if retry < max_retries - 1:
                    log_step(f"第{retry+1}次提取搜索结果失败，等待3秒后重试...")
                    time.sleep(3)
                    
                    # 尝试刷新页面以解决可能的页面加载问题或会话状态问题
                    log_step("尝试刷新页面...")
                    driver.refresh()
                    time.sleep(3)
                    
                    # 等待页面加载
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    # 处理可能出现的cookie弹窗
                    handle_cookie_popup(driver)
            
            log_step("\n===== 搜索结果详情 =====")
            for j, result in enumerate(search_results, 1):
                log_step(f"结果 {j}:")
                
                # 使用原始JSON字段名作为标签按顺序输出所有字段
                log_step(f"snippet: {result['snippet']}")
                log_step(f"documentKind: {result['documentKind']}")
                log_step(f"publishedTitle: {result['publishedTitle']}")
                log_step(f"lastModifiedDate: {result['lastModifiedDate']}")
                log_step(f"publishedAbstract: {result['publishedAbstract']}")
                log_step(f"abstract: {result['abstract']}")
                log_step(f"ModerationState: {result['ModerationState']}")
                log_step(f"uri: {result['uri']}")
                log_step(f"requires_subscription: {result['requires_subscription']}")
                log_step(f"standard_product: {result['standard_product']}")
                log_step(f"allTitle: {result['allTitle']}")
                log_step(f"id: {result['id']}")
                log_step(f"view_uri: {result['view_uri']}")
                log_step(f"highlightedText: {result['highlightedText']}")
                log_step(f"position: {result['position']}")
                log_step(f"displayFeature: {result['displayFeature']}")
                log_step(f"isAuthenticated: {result['isAuthenticated']}")
                log_step("---")

        log_step("\n搜索测试完成！")
        return True

    except Exception as e:
        log_step(f"测试失败: {e}")
        return False

    finally:
        log_step("关闭浏览器...")
        driver.quit()

if __name__ == "__main__":
    test_redhat_portal_login()
