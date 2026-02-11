import asyncio
import base64
import sqlite3
import uuid
from pathlib import Path

from playwright.async_api import async_playwright
from conf import LOCAL_CHROME_PATH

from myUtils.auth import check_cookie
from utils.base_social_media import set_init_script
from conf import BASE_DIR

# 抖音登录
async def douyin_cookie_gen(id,status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()
    async with async_playwright() as playwright:
        options = {
            'headless': False
        }
        if LOCAL_CHROME_PATH:
            browser = await playwright.chromium.launch(executable_path=LOCAL_CHROME_PATH, **options)
        else:
            browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.douyin.com/")
        original_url = page.url
        img_locator = page.get_by_role("img", name="二维码")
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)
        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            status_queue.put("500")
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(3, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                INSERT INTO user_info (type, filePath, userName, status)
                                VALUES (?, ?, ?, ?)
                                ''', (3, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")


# 视频号登录
async def get_tencent_cookie(id,status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,
        }
        if LOCAL_CHROME_PATH:
            browser = await playwright.chromium.launch(executable_path=LOCAL_CHROME_PATH, **options)
        else:
            browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        # Pause the page, and start recording manually.
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://channels.weixin.qq.com")
        original_url = page.url

        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        # 等待 iframe 出现（最多等 60 秒）
        iframe_locator = page.frame_locator("iframe").first

        # 获取 iframe 中的第一个 img 元素
        img_locator = iframe_locator.get_by_role("img").first

        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        print("✅ 图片地址:", src)
        status_queue.put(src)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(2,f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                INSERT INTO user_info (type, filePath, userName, status)
                                VALUES (?, ?, ?, ?)
                                ''', (2, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")

# 快手登录
async def get_ks_cookie(id,status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,
        }
        if LOCAL_CHROME_PATH:
            browser = await playwright.chromium.launch(executable_path=LOCAL_CHROME_PATH, **options)
        else:
            browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://cp.kuaishou.com")

        # 定位并点击“立即登录”按钮（类型为 link）
        await page.get_by_role("link", name="立即登录").click()
        await page.get_by_text("扫码登录").click()
        img_locator = page.get_by_role("img", name="qrcode")
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(4, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                        INSERT INTO user_info (type, filePath, userName, status)
                                        VALUES (?, ?, ?, ?)
                                        ''', (4, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")

# 小红书登录
async def xiaohongshu_cookie_gen(id,status_queue):
    url_changed_event = asyncio.Event()

    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,
        }
        if LOCAL_CHROME_PATH:
            browser = await playwright.chromium.launch(executable_path=LOCAL_CHROME_PATH, **options)
        else:
            browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.xiaohongshu.com/")
        await page.locator('img.css-wemwzq').click()

        img_locator = page.get_by_role("img").nth(2)
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(1, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           INSERT INTO user_info (type, filePath, userName, status)
                           VALUES (?, ?, ?, ?)
                           ''', (1, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")

async def tiktok_cookie_gen(id, status_queue):
    url_changed_event = asyncio.Event()

    async def on_url_change():
        if page.url != original_url:
            url_changed_event.set()

    async def capture_qr_image(target_page):
        # 依次尝试常见的 QR 选择器
        selectors = [
            "canvas[data-e2e='qr-code']",
            "div[data-e2e='qr-code'] canvas",
            "div[data-e2e='qr-code'] img",
            "canvas",
            "img[alt*='QR']",
            "img[src*='data:image']",
        ]

        async def screenshot_from_locator(locator):
            try:
                await locator.wait_for(state="visible", timeout=5000)
                # 优先尝试直接从 canvas 中获取 dataURL，避免截图时二维码尚未渲染
                if await locator.evaluate("node => node.tagName === 'CANVAS' && !!node.toDataURL"):
                    data_url = await locator.evaluate("node => node.toDataURL('image/png')")
                    if data_url and data_url.startswith("data:image"):
                        return data_url
                return await locator.screenshot()
            except Exception:
                return None

        # 页面级别先尝试
        for selector in selectors:
            selector_locator = target_page.locator(selector)
            if await selector_locator.count():
                locator = selector_locator.first
                shot = await screenshot_from_locator(locator)
                if shot:
                    return shot

        # 再尝试 iframe 内部
        for frame in target_page.frames:
            for selector in selectors:
                selector_locator = frame.locator(selector)
                if await selector_locator.count():
                    locator = selector_locator.first
                    shot = await screenshot_from_locator(locator)
                    if shot:
                        return shot

        # 兜底：截取登录容器
        container_locator = target_page.locator("div[data-e2e='qr-code']")
        if await container_locator.count():
            return await screenshot_from_locator(container_locator.first)
        return None

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,
        }
        if LOCAL_CHROME_PATH:
            browser = await playwright.chromium.launch(executable_path=LOCAL_CHROME_PATH, **options)
        else:
            browser = await playwright.chromium.launch(**options)
        context = await browser.new_context()
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://www.tiktok.com/login?lang=en")
        await page.wait_for_load_state('networkidle')
        # 优先直接跳转二维码登录页
        if "/login/qrcode" not in page.url:
            try:
                await page.goto("https://www.tiktok.com/login/qrcode")
                await page.wait_for_url("**/login/qrcode*", timeout=10000)
            except Exception as e:
                print("直接访问二维码登录页失败:", e)

        if "/login/qrcode" not in page.url:
            try:
                qr_option = page.locator("div[data-e2e='channel-item']").filter(has_text="使用二维码登录").first
                if await qr_option.count():
                    await qr_option.click()
                    await page.wait_for_url("**/login/qrcode*", timeout=10000)
                    await page.wait_for_timeout(500)
            except Exception as e:
                print("点击二维码登录入口失败:", e)

        original_url = page.url

        try:
            # 等二维码绘制完成
            await page.wait_for_function("""
                () => {
                    const selectors = [
                        "canvas[data-e2e='qr-code']",
                        "div[data-e2e='qr-code'] canvas",
                        "canvas"
                    ];
                    for (const selector of selectors) {
                        const node = document.querySelector(selector);
                        if (node && typeof node.toDataURL === 'function') {
                            const data = node.toDataURL('image/png');
                            if (data && data.length > 1000) {
                                return true;
                            }
                        }
                    }
                    return false;
                }
            """, timeout=5000)
        except Exception as e:
            print("等待 TikTok 二维码绘制完成超时:", e)

        try:
            qr_png = await capture_qr_image(page)
            if not qr_png:
                raise RuntimeError("未找到TikTok二维码区域")
            if isinstance(qr_png, str):
                qr_code = qr_png if qr_png.startswith("data:image") else f"data:image/png;base64,{qr_png}"
            else:
                qr_code = "data:image/png;base64," + base64.b64encode(qr_png).decode()
            status_queue.put(qr_code)
        except Exception as e:
            print("获取TikTok二维码失败:", e)
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None

        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)
            print("TikTok 登录跳转成功")
        except asyncio.TimeoutError:
            print("TikTok 登录等待超时")
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None

        uuid_v1 = uuid.uuid1()
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(5, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None

        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           INSERT INTO user_info (type, filePath, userName, status)
                           VALUES (?, ?, ?, ?)
                           ''', (5, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ TikTok 用户状态已记录")
        status_queue.put("200")

# a = asyncio.run(xiaohongshu_cookie_gen(4,None))
# print(a)
