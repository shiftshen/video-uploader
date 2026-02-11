"""
视频处理工具
"""

import os
import tempfile
from pathlib import Path
from playwright.async_api import Page


async def capture_thumbnail_from_video(page: Page, output_path: str = None) -> str:
    """
    从页面上的视频元素截取封面
    
    Args:
        page: Playwright Page 对象
        output_path: 输出图片路径（可选，不提供则自动生成临时文件）
    
    Returns:
        str: 封面图片的路径
    """
    if output_path is None:
        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"douyin_thumbnail_{os.getpid()}.jpg")
    
    try:
        # 等待视频元素出现
        await page.wait_for_selector("video", timeout=10000)
        
        # 将视频定位到第1秒（通常第1秒的画面比较好）
        await page.evaluate("""
            async () => {
                const video = document.querySelector('video');
                if (video) {
                    video.currentTime = 1.0;
                    await new Promise(resolve => {
                        video.addEventListener('seeked', resolve, { once: true });
                    });
                }
            }
        """)
        
        # 等待一下确保帧渲染完成
        await page.wait_for_timeout(500)
        
        # 截取视频元素
        video_element = await page.query_selector("video")
        if video_element:
            await video_element.screenshot(path=output_path)
            print(f"[+] 成功从视频截取封面: {output_path}")
            return output_path
        else:
            raise Exception("未找到视频元素")
            
    except Exception as e:
        print(f"[错误] 截取视频封面失败: {e}")
        raise


async def capture_thumbnail_from_page_element(page: Page, selector: str, output_path: str = None) -> str:
    """
    从页面上的特定元素截取封面（备用方案）
    
    Args:
        page: Playwright Page 对象
        selector: 元素选择器
        output_path: 输出图片路径
    
    Returns:
        str: 封面图片的路径
    """
    if output_path is None:
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"douyin_thumbnail_{os.getpid()}.jpg")
    
    try:
        element = await page.query_selector(selector)
        if element:
            await element.screenshot(path=output_path)
            print(f"[+] 成功截取封面: {output_path}")
            return output_path
        else:
            raise Exception(f"未找到元素: {selector}")
    except Exception as e:
        print(f"[错误] 截取封面失败: {e}")
        raise


async def select_platform_generated_cover(page: Page, cover_type: str = "vertical") -> bool:
    """
    选择平台自动生成的封面（抖音会自动生成多个封面选项）
    
    Args:
        page: Playwright Page 对象
        cover_type: 封面类型 "vertical" (竖屏4:3) 或 "horizontal" (横屏3:4)
    
    Returns:
        bool: 是否成功选择
    """
    try:
        print(f"[+] 尝试选择平台生成的{cover_type}封面...")
        
        # 点击"选择封面"按钮
        await page.click('text="选择封面"')
        await page.wait_for_selector("div.dy-creator-content-modal", timeout=5000)
        
        # 等待封面选项加载
        await page.wait_for_timeout(2000)
        
        # 根据类型选择封面
        if cover_type == "vertical":
            # 选择竖屏封面（4:3）
            # 抖音会自动生成多个封面选项，选择第一个
            cover_selector = "div.dy-creator-content-modal div[class*='cover-item']:first-child"
        else:
            # 选择横屏封面（3:4）
            cover_selector = "div.dy-creator-content-modal div[class*='cover-item']:nth-child(2)"
        
        # 检查是否有封面选项
        cover_count = await page.locator(cover_selector).count()
        if cover_count > 0:
            await page.locator(cover_selector).click()
            await page.wait_for_timeout(1000)
            
            # 点击完成按钮
            await page.locator("div#tooltip-container button:visible:has-text('完成')").click()
            
            print(f"[+] 成功选择平台生成的封面")
            return True
        else:
            print(f"[警告] 未找到平台生成的封面选项")
            return False
            
    except Exception as e:
        print(f"[错误] 选择平台封面失败: {e}")
        return False


def get_video_thumbnail_path(video_path: str) -> str:
    """
    根据视频路径生成封面图片路径
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        str: 封面图片路径
    """
    video_path_obj = Path(video_path)
    thumbnail_dir = video_path_obj.parent
    thumbnail_name = video_path_obj.stem + "_thumbnail.jpg"
    return str(thumbnail_dir / thumbnail_name)
