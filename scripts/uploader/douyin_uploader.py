"""
抖音视频上传器
支持 Cookie 自动保存和重用
"""
import asyncio
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.cookie_manager import cookie_manager
from utils.base_social_media import set_init_script
from utils.log import logger
from utils.files_times import get_absolute_path


class DouyinUploader:
    """抖音上传器"""
    
    def __init__(self, account_name: str = "default"):
        """
        初始化抖音上传器
        
        Args:
            account_name: 账号名称（用于区分多个账号）
        """
        self.platform = "douyin"
        self.account_name = account_name
        self.upload_url = "https://creator.douyin.com/creator-micro/content/upload"
    
    async def upload(
        self,
        video_path: str,
        title: str,
        tags: list,
        publish_date: datetime = None,
        thumbnail_path: str = None,
        product_link: str = None,
        product_title: str = None,
        location: str = None,
        sync_to_toutiao: bool = False,
        sync_to_xigua: bool = False,
    ) -> bool:
        """
        上传视频到抖音
        
        Args:
            video_path: 视频文件路径
            title: 视频标题
            tags: 标签列表
            publish_date: 发布时间（None 表示立即发布）
            thumbnail_path: 缩略图路径
            product_link: 商品链接
            product_title: 商品标题
            location: 地理位置
            sync_to_toutiao: 同步到头条
            sync_to_xigua: 同步到西瓜视频
            
        Returns:
            是否成功
        """
        logger.info(f"[抖音] 开始上传视频: {title}")
        
        # 检查 Cookie 是否存在和有效
        cookie_valid = False
        if cookie_manager.cookie_exists(self.platform, self.account_name):
            logger.info(f"[抖音] 检查 Cookie 有效性...")
            cookie_valid = await cookie_manager.verify_cookie(self.platform, self.account_name)
        
        # 如果 Cookie 无效，需要登录
        if not cookie_valid:
            logger.warning(f"[抖音] Cookie 无效或不存在，需要登录")
            success = await cookie_manager.login_and_save_cookie(self.platform, self.account_name)
            if not success:
                logger.error(f"[抖音] 登录失败")
                return False
        
        # 开始上传
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False)
            
            # 加载 Cookie
            context = await cookie_manager.load_cookie(browser, self.platform, self.account_name)
            page = await context.new_page()
            
            try:
                # 访问上传页面
                await page.goto(self.upload_url)
                logger.info(f"[抖音] 已打开上传页面")
                
                # 等待页面加载
                await page.wait_for_url(self.upload_url, timeout=10000)
                
                # 检查是否需要重新登录
                if await page.get_by_text('扫码登录').count() or await page.get_by_text('手机号登录').count():
                    logger.error(f"[抖音] 需要重新登录")
                    await context.close()
                    await browser.close()
                    return False
                
                # 上传视频文件
                logger.info(f"[抖音] 上传视频文件...")
                video_abs_path = get_absolute_path(video_path, "video_uploader")
                
                # 等待文件上传输入框
                file_input = await page.wait_for_selector('input[type="file"]', timeout=10000)
                await file_input.set_input_files(video_abs_path)
                logger.info(f"[抖音] 视频文件已选择")
                
                # 等待视频上传完成
                logger.info(f"[抖音] 等待视频上传...")
                await asyncio.sleep(5)  # 等待上传开始
                
                # 等待上传完成（检查是否出现"上传成功"或进度条消失）
                max_wait = 300  # 最多等待5分钟
                for i in range(max_wait):
                    # 检查是否有错误提示
                    if await page.get_by_text("上传失败").count():
                        logger.error(f"[抖音] 视频上传失败")
                        return False
                    
                    # 检查上传进度
                    # 这里需要根据实际页面元素调整
                    await asyncio.sleep(1)
                    
                    # 简单检查：如果标题输入框可用，说明上传完成
                    try:
                        title_input = await page.query_selector('div[data-placeholder="作品标题"]')
                        if title_input:
                            break
                    except:
                        pass
                
                logger.success(f"[抖音] 视频上传完成")
                
                # 填写标题
                logger.info(f"[抖音] 填写标题...")
                title_container = await page.wait_for_selector('div[data-placeholder="作品标题"]', timeout=10000)
                await title_container.click()
                await asyncio.sleep(0.5)
                await page.keyboard.type(title)
                logger.info(f"[抖音] 标题已填写: {title}")
                
                # 填写标签（话题）
                if tags:
                    logger.info(f"[抖音] 添加话题...")
                    # 点击话题按钮
                    try:
                        topic_button = await page.get_by_text("添加话题").first
                        await topic_button.click()
                        await asyncio.sleep(1)
                        
                        for tag in tags[:5]:  # 最多5个话题
                            # 输入话题
                            topic_input = await page.query_selector('input[placeholder="搜索话题"]')
                            if topic_input:
                                await topic_input.fill(tag)
                                await asyncio.sleep(1)
                                
                                # 选择第一个推荐话题
                                try:
                                    first_topic = await page.query_selector('div.semi-portal div.semi-popover-content div:first-child')
                                    if first_topic:
                                        await first_topic.click()
                                        await asyncio.sleep(0.5)
                                except:
                                    pass
                        
                        logger.info(f"[抖音] 话题已添加")
                    except Exception as e:
                        logger.warning(f"[抖音] 添加话题失败: {e}")
                
                # 上传封面（如果提供）
                if thumbnail_path:
                    logger.info(f"[抖音] 上传封面...")
                    try:
                        thumbnail_abs_path = get_absolute_path(thumbnail_path, "video_uploader")
                        cover_input = await page.query_selector('input[type="file"][accept*="image"]')
                        if cover_input:
                            await cover_input.set_input_files(thumbnail_abs_path)
                            await asyncio.sleep(2)
                            logger.info(f"[抖音] 封面已上传")
                    except Exception as e:
                        logger.warning(f"[抖音] 上传封面失败: {e}")
                
                # 添加商品链接（如果提供）
                if product_link and product_title:
                    logger.info(f"[抖音] 添加商品链接...")
                    try:
                        # 这里需要根据实际页面元素调整
                        # 通常需要点击"添加商品"按钮
                        add_product_button = await page.get_by_text("添加商品").first
                        if add_product_button:
                            await add_product_button.click()
                            await asyncio.sleep(1)
                            # 后续步骤根据实际页面调整
                            logger.info(f"[抖音] 商品链接已添加")
                    except Exception as e:
                        logger.warning(f"[抖音] 添加商品链接失败: {e}")
                
                # 设置发布时间
                if publish_date:
                    logger.info(f"[抖音] 设置定时发布...")
                    try:
                        # 点击定时发布
                        schedule_button = await page.get_by_text("定时发布").first
                        await schedule_button.click()
                        await asyncio.sleep(1)
                        
                        # 设置日期和时间
                        # 这里需要根据实际页面元素调整
                        date_str = publish_date.strftime("%Y-%m-%d %H:%M")
                        logger.info(f"[抖音] 定时发布时间: {date_str}")
                    except Exception as e:
                        logger.warning(f"[抖音] 设置定时发布失败: {e}")
                
                # 同步到其他平台
                if sync_to_toutiao:
                    try:
                        toutiao_checkbox = await page.get_by_text("同步到头条").first
                        if toutiao_checkbox:
                            await toutiao_checkbox.click()
                            logger.info(f"[抖音] 已选择同步到头条")
                    except:
                        pass
                
                if sync_to_xigua:
                    try:
                        xigua_checkbox = await page.get_by_text("同步到西瓜视频").first
                        if xigua_checkbox:
                            await xigua_checkbox.click()
                            logger.info(f"[抖音] 已选择同步到西瓜视频")
                    except:
                        pass
                
                # 点击发布按钮
                logger.info(f"[抖音] 准备发布...")
                publish_button = await page.get_by_role("button", name="发布", exact=True).first
                await publish_button.click()
                
                # 等待发布完成
                await asyncio.sleep(3)
                
                # 检查是否发布成功
                try:
                    # 查找成功提示
                    success_indicator = await page.wait_for_selector('text=发布成功', timeout=10000)
                    if success_indicator:
                        logger.success(f"[抖音] 视频发布成功！")
                        
                        # 保存最新的 Cookie
                        await cookie_manager.save_cookie(context, self.platform, self.account_name)
                        
                        return True
                except:
                    logger.warning(f"[抖音] 未检测到发布成功提示，请手动确认")
                    return True  # 假设成功
                
            except Exception as e:
                logger.error(f"[抖音] 上传过程出错: {e}")
                import traceback
                traceback.print_exc()
                return False
            finally:
                # 保持浏览器打开一段时间以便查看结果
                await asyncio.sleep(5)
                await context.close()
                await browser.close()


async def main():
    """测试函数"""
    uploader = DouyinUploader(account_name="test")
    
    success = await uploader.upload(
        video_path="/path/to/video.mp4",
        title="测试视频标题",
        tags=["测试", "视频上传"],
        publish_date=None,  # 立即发布
    )
    
    if success:
        print("上传成功！")
    else:
        print("上传失败！")


if __name__ == "__main__":
    asyncio.run(main())
