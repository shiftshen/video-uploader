"""
完整的浏览器环境配置模块
解决视频预览黑屏和封面无法加载的问题
"""

from playwright.async_api import Browser, BrowserContext, Playwright
from pathlib import Path
import os

# 本地 Chrome 路径（如果存在）
LOCAL_CHROME_PATH = os.environ.get("CHROME_PATH", "")

async def get_browser_context(
    playwright: Playwright,
    account_file: str,
    headless: bool = False,
    locale: str = "zh-CN",
    use_chrome: bool = True
) -> tuple[Browser, BrowserContext]:
    """
    创建完整配置的浏览器上下文
    
    Args:
        playwright: Playwright 实例
        account_file: Cookie 文件路径
        headless: 是否无头模式
        locale: 语言环境（zh-CN 或 en-US）
        use_chrome: 是否使用 Chrome（否则使用 Firefox）
    
    Returns:
        (browser, context) 元组
    """
    
    # 1. 浏览器启动参数
    launch_options = {
        "headless": headless,
        "args": [
            "--disable-blink-features=AutomationControlled",  # 禁用自动化控制标识
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-extensions",
        ]
    }
    
    # 如果有本地 Chrome 路径，使用本地 Chrome
    if use_chrome and LOCAL_CHROME_PATH and os.path.exists(LOCAL_CHROME_PATH):
        launch_options["executable_path"] = LOCAL_CHROME_PATH
    
    # 启动浏览器
    if use_chrome:
        browser = await playwright.chromium.launch(**launch_options)
    else:
        browser = await playwright.firefox.launch(**launch_options)
    
    # 2. 上下文参数（关键！）
    context_options = {
        "storage_state": account_file if os.path.exists(account_file) else None,
        "locale": locale,  # 语言环境
        "timezone_id": "Asia/Shanghai" if locale == "zh-CN" else "America/New_York",
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": get_user_agent(locale),
        "extra_http_headers": {
            "Accept-Language": get_accept_language(locale),
        },
        "permissions": ["geolocation", "notifications"],  # 预授权权限
        "geolocation": {"longitude": 116.397128, "latitude": 39.916527} if locale == "zh-CN" else None,  # 北京坐标
    }
    
    # 创建上下文
    context = await browser.new_context(**context_options)
    
    # 3. 注入 stealth.js（反检测）
    stealth_js_path = Path(__file__).parent / "stealth.min.js"
    if stealth_js_path.exists():
        await context.add_init_script(path=stealth_js_path)
    
    # 4. 注入额外的反检测脚本
    await context.add_init_script("""
        // 覆盖 navigator.webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // 覆盖 navigator.plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // 覆盖 navigator.languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en-US', 'en']
        });
        
        // 添加 window.chrome 对象
        window.chrome = {
            runtime: {}
        };
        
        // 覆盖权限查询
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)
    
    return browser, context


def get_user_agent(locale: str) -> str:
    """获取 User Agent"""
    if locale == "zh-CN":
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    else:
        return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def get_accept_language(locale: str) -> str:
    """获取 Accept-Language 头"""
    if locale == "zh-CN":
        return "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    else:
        return "en-US,en;q=0.9"


async def handle_permissions_dialog(page):
    """处理权限弹窗"""
    try:
        # 尝试关闭可能的权限弹窗
        await page.evaluate("""
            // 关闭通知权限弹窗
            if (Notification.permission === 'default') {
                Notification.requestPermission().then(() => {});
            }
        """)
    except:
        pass


async def wait_for_video_preview(page, timeout: int = 30000):
    """
    等待视频预览加载完成
    
    Args:
        page: Playwright Page 对象
        timeout: 超时时间（毫秒）
    
    Returns:
        bool: 是否加载成功
    """
    try:
        # 等待视频元素出现
        await page.wait_for_selector("video", timeout=timeout)
        
        # 等待视频加载完成
        await page.evaluate("""
            async () => {
                const video = document.querySelector('video');
                if (video) {
                    // 等待视频元数据加载
                    if (video.readyState < 1) {
                        await new Promise(resolve => {
                            video.addEventListener('loadedmetadata', resolve, { once: true });
                        });
                    }
                    // 等待至少一帧可以播放
                    if (video.readyState < 2) {
                        await new Promise(resolve => {
                            video.addEventListener('loadeddata', resolve, { once: true });
                        });
                    }
                }
            }
        """)
        
        return True
    except Exception as e:
        print(f"[警告] 视频预览加载超时: {e}")
        return False


async def capture_video_frame(page, output_path: str, timestamp: float = 0.5):
    """
    从视频中截取一帧作为封面
    
    Args:
        page: Playwright Page 对象
        output_path: 输出图片路径
        timestamp: 截取时间点（秒）
    
    Returns:
        bool: 是否成功
    """
    try:
        # 等待视频加载
        if not await wait_for_video_preview(page):
            return False
        
        # 截取视频帧
        await page.evaluate(f"""
            async () => {{
                const video = document.querySelector('video');
                if (video) {{
                    video.currentTime = {timestamp};
                    await new Promise(resolve => {{
                        video.addEventListener('seeked', resolve, {{ once: true }});
                    }});
                }}
            }}
        """)
        
        # 等待一下确保帧渲染完成
        await page.wait_for_timeout(500)
        
        # 截取视频元素
        video_element = await page.query_selector("video")
        if video_element:
            await video_element.screenshot(path=output_path)
            return True
        
        return False
    except Exception as e:
        print(f"[错误] 截取视频帧失败: {e}")
        return False
