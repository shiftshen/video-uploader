"""
Cookie 管理模块
负责 Cookie 的保存、加载、验证和管理
"""
import asyncio
import json
import uuid
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext
from .base_social_media import set_init_script
from .log import logger


class CookieManager:
    """Cookie 管理器"""
    
    def __init__(self, cookies_dir: Path = None):
        """
        初始化 Cookie 管理器
        
        Args:
            cookies_dir: Cookie 文件存储目录
        """
        if cookies_dir is None:
            # 默认使用项目根目录下的 cookiesFile
            self.cookies_dir = Path(__file__).parent.parent.parent / "cookiesFile"
        else:
            self.cookies_dir = Path(cookies_dir)
        
        # 确保目录存在
        self.cookies_dir.mkdir(parents=True, exist_ok=True)
        
    def get_cookie_path(self, platform: str, account_name: str = "default") -> Path:
        """
        获取 Cookie 文件路径
        
        Args:
            platform: 平台名称 (douyin, kuaishou, tiktok, tencent, xhs)
            account_name: 账号名称（用于区分同一平台的多个账号）
            
        Returns:
            Cookie 文件路径
        """
        filename = f"{platform}_{account_name}.json"
        return self.cookies_dir / filename
    
    def cookie_exists(self, platform: str, account_name: str = "default") -> bool:
        """
        检查 Cookie 文件是否存在
        
        Args:
            platform: 平台名称
            account_name: 账号名称
            
        Returns:
            是否存在
        """
        cookie_path = self.get_cookie_path(platform, account_name)
        return cookie_path.exists()
    
    async def save_cookie(self, context: BrowserContext, platform: str, account_name: str = "default"):
        """
        保存浏览器上下文的 Cookie
        
        Args:
            context: Playwright 浏览器上下文
            platform: 平台名称
            account_name: 账号名称
        """
        cookie_path = self.get_cookie_path(platform, account_name)
        await context.storage_state(path=str(cookie_path))
        logger.success(f"[Cookie] 已保存 {platform} 账号 {account_name} 的 Cookie 到 {cookie_path}")
    
    async def load_cookie(self, browser: Browser, platform: str, account_name: str = "default") -> BrowserContext:
        """
        加载 Cookie 并创建浏览器上下文
        
        Args:
            browser: Playwright 浏览器实例
            platform: 平台名称
            account_name: 账号名称
            
        Returns:
            带有 Cookie 的浏览器上下文
        """
        cookie_path = self.get_cookie_path(platform, account_name)
        
        if not cookie_path.exists():
            logger.warning(f"[Cookie] Cookie 文件不存在: {cookie_path}")
            # 返回空上下文
            context = await browser.new_context()
        else:
            # 加载 Cookie
            context = await browser.new_context(storage_state=str(cookie_path))
            logger.info(f"[Cookie] 已加载 {platform} 账号 {account_name} 的 Cookie")
        
        # 注入反检测脚本
        context = await set_init_script(context)
        return context
    
    async def verify_cookie_douyin(self, cookie_path: Path) -> bool:
        """验证抖音 Cookie 是否有效 - 使用完整浏览器环境配置"""
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,
                channel='chrome'
            )
            context = await browser.new_context(
                storage_state=str(cookie_path),
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='Asia/Shanghai',
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                },
            )
            context = await set_init_script(context)
            page = await context.new_page()
            
            try:
                await page.goto("https://creator.douyin.com/creator-micro/content/upload")
                await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload", timeout=5000)
                
                # 等待页面完全加载
                await page.wait_for_timeout(3000)
                
                # 检查是否出现登录提示
                try:
                    await page.get_by_text("扫码登录").wait_for(timeout=5000)
                    logger.error("[Cookie] 抖音 Cookie 失效")
                    return False
                except:
                    logger.success("[Cookie] 抖音 Cookie 有效")
                    return True
            except Exception as e:
                logger.error(f"[Cookie] 抖音 Cookie 验证失败: {e}")
                return False
            finally:
                await context.close()
                await browser.close()
    
    async def verify_cookie_kuaishou(self, cookie_path: Path) -> bool:
        """验证快手 Cookie 是否有效"""
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(storage_state=str(cookie_path))
            context = await set_init_script(context)
            page = await context.new_page()
            
            try:
                await page.goto("https://cp.kuaishou.com/article/publish/video")
                # 如果出现"机构服务"说明未登录
                try:
                    await page.wait_for_selector("div.names div.container div.name:text('机构服务')", timeout=5000)
                    logger.error("[Cookie] 快手 Cookie 失效")
                    return False
                except:
                    logger.success("[Cookie] 快手 Cookie 有效")
                    return True
            except Exception as e:
                logger.error(f"[Cookie] 快手 Cookie 验证失败: {e}")
                return False
            finally:
                await context.close()
                await browser.close()
    
    async def verify_cookie_tiktok(self, cookie_path: Path) -> bool:
        """验证 TikTok Cookie 是否有效"""
        async with async_playwright() as playwright:
            browser = await playwright.firefox.launch(headless=True)
            context = await browser.new_context(storage_state=str(cookie_path))
            context = await set_init_script(context)
            page = await context.new_page()
            
            try:
                await page.goto("https://www.tiktok.com/tiktokstudio/upload?lang=en")
                await page.wait_for_load_state('networkidle')
                
                # 检查是否有登录相关的 select 元素
                select_elements = await page.query_selector_all('select')
                for element in select_elements:
                    class_name = await element.get_attribute('class') or ''
                    if 'tiktok-' in class_name and 'SelectFormContainer' in class_name:
                        logger.error("[Cookie] TikTok Cookie 失效")
                        return False
                
                logger.success("[Cookie] TikTok Cookie 有效")
                return True
            except Exception as e:
                logger.error(f"[Cookie] TikTok Cookie 验证失败: {e}")
                return False
            finally:
                await context.close()
                await browser.close()
    
    async def verify_cookie_tencent(self, cookie_path: Path) -> bool:
        """验证视频号 Cookie 是否有效"""
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(storage_state=str(cookie_path))
            context = await set_init_script(context)
            page = await context.new_page()
            
            try:
                await page.goto("https://channels.weixin.qq.com/platform/post/create")
                # 如果出现"微信小店"说明未登录
                try:
                    await page.wait_for_selector('div.title-name:has-text("微信小店")', timeout=5000)
                    logger.error("[Cookie] 视频号 Cookie 失效")
                    return False
                except:
                    logger.success("[Cookie] 视频号 Cookie 有效")
                    return True
            except Exception as e:
                logger.error(f"[Cookie] 视频号 Cookie 验证失败: {e}")
                return False
            finally:
                await context.close()
                await browser.close()
    
    async def verify_cookie_xhs(self, cookie_path: Path) -> bool:
        """验证小红书 Cookie 是否有效"""
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(storage_state=str(cookie_path))
            context = await set_init_script(context)
            page = await context.new_page()
            
            try:
                await page.goto("https://creator.xiaohongshu.com/creator-micro/content/upload")
                await page.wait_for_url("https://creator.xiaohongshu.com/creator-micro/content/upload", timeout=5000)
                
                # 检查是否出现登录提示
                if await page.get_by_text('手机号登录').count() or await page.get_by_text('扫码登录').count():
                    logger.error("[Cookie] 小红书 Cookie 失效")
                    return False
                else:
                    logger.success("[Cookie] 小红书 Cookie 有效")
                    return True
            except Exception as e:
                logger.error(f"[Cookie] 小红书 Cookie 验证失败: {e}")
                return False
            finally:
                await context.close()
                await browser.close()
    
    async def verify_cookie(self, platform: str, account_name: str = "default") -> bool:
        """
        验证 Cookie 是否有效
        
        Args:
            platform: 平台名称
            account_name: 账号名称
            
        Returns:
            Cookie 是否有效
        """
        cookie_path = self.get_cookie_path(platform, account_name)
        
        if not cookie_path.exists():
            logger.warning(f"[Cookie] Cookie 文件不存在: {cookie_path}")
            return False
        
        # 根据平台调用对应的验证函数
        verify_funcs = {
            'douyin': self.verify_cookie_douyin,
            'kuaishou': self.verify_cookie_kuaishou,
            'tiktok': self.verify_cookie_tiktok,
            'tencent': self.verify_cookie_tencent,
            'xhs': self.verify_cookie_xhs,
        }
        
        verify_func = verify_funcs.get(platform)
        if verify_func is None:
            logger.error(f"[Cookie] 不支持的平台: {platform}")
            return False
        
        return await verify_func(cookie_path)
    
    async def login_and_save_cookie(self, platform: str, account_name: str = "default", timeout: int = 200):
        """
        打开浏览器让用户登录，并保存 Cookie
        
        Args:
            platform: 平台名称
            account_name: 账号名称
            timeout: 登录超时时间（秒）
        """
        login_urls = {
            'douyin': 'https://creator.douyin.com/',
            'kuaishou': 'https://cp.kuaishou.com',
            'tiktok': 'https://www.tiktok.com/tiktokstudio/upload?lang=en',
            'tencent': 'https://channels.weixin.qq.com',
            'xhs': 'https://creator.xiaohongshu.com/',
        }
        
        login_url = login_urls.get(platform)
        if login_url is None:
            logger.error(f"[Cookie] 不支持的平台: {platform}")
            return False
        
        logger.info(f"[Cookie] 打开浏览器进行 {platform} 登录...")
        
        async with async_playwright() as playwright:
            # 使用非无头模式 + 完整浏览器配置
            browser_type = playwright.firefox if platform == 'tiktok' else playwright.chromium
            
            if platform == 'tiktok':
                browser = await browser_type.launch(headless=False)
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Firefox/120.0',
                    locale='en-US',
                    timezone_id='America/New_York',
                    extra_http_headers={
                        'Accept-Language': 'en-US,en;q=0.9',
                    },
                )
            else:
                browser = await browser_type.launch(headless=False, channel='chrome')
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='Asia/Shanghai',
                    extra_http_headers={
                        'Accept-Language': 'en-US,en;q=0.9',
                    },
                )
            
            context = await set_init_script(context)
            page = await context.new_page()
            
            await page.goto(login_url)
            original_url = page.url
            
            logger.info(f"[Cookie] 请在浏览器中完成登录...")
            logger.info(f"[Cookie] 登录成功后页面会自动跳转，最多等待 {timeout} 秒")
            
            # 监听 URL 变化
            url_changed = asyncio.Event()
            
            def on_url_change(frame):
                if frame == page.main_frame and page.url != original_url:
                    url_changed.set()
            
            page.on('framenavigated', on_url_change)
            
            try:
                # 等待 URL 变化（说明登录成功）
                await asyncio.wait_for(url_changed.wait(), timeout=timeout)
                logger.success(f"[Cookie] 登录成功！")
                
                # 等待一下确保 Cookie 完全保存
                await asyncio.sleep(2)
                
                # 保存 Cookie
                cookie_path = self.get_cookie_path(platform, account_name)
                await context.storage_state(path=str(cookie_path))
                logger.success(f"[Cookie] Cookie 已保存到 {cookie_path}")
                
                # 验证 Cookie
                is_valid = await self.verify_cookie(platform, account_name)
                if is_valid:
                    logger.success(f"[Cookie] Cookie 验证成功！")
                    return True
                else:
                    logger.error(f"[Cookie] Cookie 验证失败，请重试")
                    return False
                    
            except asyncio.TimeoutError:
                logger.error(f"[Cookie] 登录超时（{timeout}秒）")
                return False
            finally:
                await context.close()
                await browser.close()
    
    def list_cookies(self) -> dict:
        """
        列出所有已保存的 Cookie
        
        Returns:
            {platform: [account_names]}
        """
        cookies = {}
        for cookie_file in self.cookies_dir.glob("*.json"):
            # 文件名格式: platform_accountname.json
            name = cookie_file.stem
            if '_' in name:
                platform, account_name = name.split('_', 1)
                if platform not in cookies:
                    cookies[platform] = []
                cookies[platform].append(account_name)
        
        return cookies
    
    def delete_cookie(self, platform: str, account_name: str = "default"):
        """
        删除 Cookie 文件
        
        Args:
            platform: 平台名称
            account_name: 账号名称
        """
        cookie_path = self.get_cookie_path(platform, account_name)
        if cookie_path.exists():
            cookie_path.unlink()
            logger.info(f"[Cookie] 已删除 {platform} 账号 {account_name} 的 Cookie")
        else:
            logger.warning(f"[Cookie] Cookie 文件不存在: {cookie_path}")


# 全局 Cookie 管理器实例
cookie_manager = CookieManager()
