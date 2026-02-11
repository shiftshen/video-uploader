#!/usr/bin/env python3
"""
统一的视频上传入口
支持所有平台的视频上传，自动管理 Cookie
"""
import asyncio
import argparse
import json
from pathlib import Path
from datetime import datetime
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.cookie_manager import cookie_manager
from utils.log import logger


async def upload_douyin(args):
    """上传到抖音"""
    from uploader.douyin_uploader.main import DouYinVideo, douyin_setup
    
    # 检查 Cookie
    account_file = cookie_manager.get_cookie_path("douyin", args.account)
    
    if not account_file.exists():
        logger.warning(f"[抖音] Cookie 文件不存在，需要登录")
        success = await cookie_manager.login_and_save_cookie("douyin", args.account)
        if not success:
            logger.error(f"[抖音] 登录失败")
            return False
    
    logger.info(f"[抖音] Cookie 文件存在: {account_file}")
    # 注意：跳过 verify_cookie 避免超时，直接尝试上传
    
    # 准备上传参数
    publish_date = None
    if args.publish_date:
        try:
            publish_date = datetime.strptime(args.publish_date, "%Y-%m-%d %H:%M:%S")
        except:
            logger.warning(f"[抖音] 发布时间格式错误，将立即发布")
    
    # 创建视频对象 - publish_date=None 表示立即发布
    video = DouYinVideo(
        title=args.title,
        file_path=args.video,
        tags=args.tags.split(',') if args.tags else [],
        publish_date=None,  # 立即发布
        account_file=str(account_file),
        thumbnail_path=args.thumbnail,
        productLink=args.product_link or '',
        productTitle=args.product_title or ''
    )
    
    # 执行上传
    result = await douyin_setup(video)
    return result


async def upload_kuaishou(args):
    """上传到快手"""
    from uploader.ks_uploader.main import KSVideo, ks_setup
    
    # 检查 Cookie
    account_file = cookie_manager.get_cookie_path("kuaishou", args.account)
    
    if not account_file.exists():
        logger.warning(f"[快手] Cookie 文件不存在，需要登录")
        success = await cookie_manager.login_and_save_cookie("kuaishou", args.account)
        if not success:
            logger.error(f"[快手] 登录失败")
            return False
    else:
        # 验证 Cookie
        is_valid = await cookie_manager.verify_cookie("kuaishou", args.account)
        if not is_valid:
            logger.warning(f"[快手] Cookie 已失效，需要重新登录")
            success = await cookie_manager.login_and_save_cookie("kuaishou", args.account)
            if not success:
                logger.error(f"[快手] 登录失败")
                return False
    
    # 准备上传参数
    publish_date = None
    if args.publish_date:
        try:
            publish_date = datetime.strptime(args.publish_date, "%Y-%m-%d %H:%M:%S")
        except:
            logger.warning(f"[快手] 发布时间格式错误，将立即发布")
    
    # 创建视频对象
    video = KSVideo(
        title=args.title,
        file_path=args.video,
        tags=args.tags.split(',')[:3] if args.tags else [],  # 快手最多3个标签
        publish_date=publish_date or datetime.now(),
        account_file=str(account_file)
    )
    
    # 执行上传
    result = await ks_setup(video)
    return result


async def upload_tiktok(args):
    """上传到 TikTok"""
    from uploader.tk_uploader.main import TiktokVideo, tiktok_setup
    
    # 检查 Cookie
    account_file = cookie_manager.get_cookie_path("tiktok", args.account)
    
    if not account_file.exists():
        logger.warning(f"[TikTok] Cookie 文件不存在，需要登录")
        success = await cookie_manager.login_and_save_cookie("tiktok", args.account)
        if not success:
            logger.error(f"[TikTok] 登录失败")
            return False
    else:
        # 验证 Cookie
        is_valid = await cookie_manager.verify_cookie("tiktok", args.account)
        if not is_valid:
            logger.warning(f"[TikTok] Cookie 已失效，需要重新登录")
            success = await cookie_manager.login_and_save_cookie("tiktok", args.account)
            if not success:
                logger.error(f"[TikTok] 登录失败")
                return False
    
    # 准备上传参数
    publish_date = None
    if args.publish_date:
        try:
            publish_date = datetime.strptime(args.publish_date, "%Y-%m-%d %H:%M:%S")
        except:
            logger.warning(f"[TikTok] 发布时间格式错误，将立即发布")
    
    # 创建视频对象
    video = TiktokVideo(
        title=args.title,
        file_path=args.video,
        tags=args.tags.split(',') if args.tags else [],
        publish_date=publish_date or datetime.now(),
        account_file=str(account_file)
    )
    
    # 执行上传
    result = await tiktok_setup(video)
    return result


async def upload_tencent(args):
    """上传到视频号"""
    from uploader.tencent_uploader.main import TencentVideo, tencent_setup
    
    # 检查 Cookie
    account_file = cookie_manager.get_cookie_path("tencent", args.account)
    
    if not account_file.exists():
        logger.warning(f"[视频号] Cookie 文件不存在，需要登录")
        success = await cookie_manager.login_and_save_cookie("tencent", args.account)
        if not success:
            logger.error(f"[视频号] 登录失败")
            return False
    else:
        # 验证 Cookie
        is_valid = await cookie_manager.verify_cookie("tencent", args.account)
        if not is_valid:
            logger.warning(f"[视频号] Cookie 已失效，需要重新登录")
            success = await cookie_manager.login_and_save_cookie("tencent", args.account)
            if not success:
                logger.error(f"[视频号] 登录失败")
                return False
    
    # 准备上传参数
    publish_date = None
    if args.publish_date:
        try:
            publish_date = datetime.strptime(args.publish_date, "%Y-%m-%d %H:%M:%S")
        except:
            logger.warning(f"[视频号] 发布时间格式错误，将立即发布")
    
    # 创建视频对象
    video = TencentVideo(
        title=args.title,
        file_path=args.video,
        tags=args.tags.split(',') if args.tags else [],
        publish_date=publish_date or datetime.now(),
        account_file=str(account_file),
        category=args.category or ''
    )
    
    # 执行上传
    result = await tencent_setup(video)
    return result


async def upload_xhs(args):
    """上传到小红书"""
    from uploader.xhs_uploader.main import XHSVideo, xhs_setup
    
    # 检查 Cookie
    account_file = cookie_manager.get_cookie_path("xhs", args.account)
    
    if not account_file.exists():
        logger.warning(f"[小红书] Cookie 文件不存在，需要登录")
        success = await cookie_manager.login_and_save_cookie("xhs", args.account)
        if not success:
            logger.error(f"[小红书] 登录失败")
            return False
    else:
        # 验证 Cookie
        is_valid = await cookie_manager.verify_cookie("xhs", args.account)
        if not is_valid:
            logger.warning(f"[小红书] Cookie 已失效，需要重新登录")
            success = await cookie_manager.login_and_save_cookie("xhs", args.account)
            if not success:
                logger.error(f"[小红书] 登录失败")
                return False
    
    # 准备上传参数
    publish_date = None
    if args.publish_date:
        try:
            publish_date = datetime.strptime(args.publish_date, "%Y-%m-%d %H:%M:%S")
        except:
            logger.warning(f"[小红书] 发布时间格式错误，将立即发布")
    
    # 创建视频对象
    video = XHSVideo(
        title=args.title,
        file_path=args.video,
        tags=args.tags.split(',') if args.tags else [],
        publish_date=publish_date or datetime.now(),
        account_file=str(account_file)
    )
    
    # 执行上传
    result = await xhs_setup(video)
    return result


def main():
    parser = argparse.ArgumentParser(description='视频上传工具')
    
    # 必需参数
    parser.add_argument('--platform', required=True, 
                       choices=['douyin', 'kuaishou', 'tiktok', 'tencent', 'xhs'],
                       help='上传平台')
    parser.add_argument('--video', help='视频文件路径')
    parser.add_argument('--title', help='视频标题')
    
    # 可选参数
    parser.add_argument('--tags', help='标签（逗号分隔）')
    parser.add_argument('--account', default='default', help='账号名称（用于区分多账号）')
    parser.add_argument('--publish-date', help='发布时间（格式：YYYY-MM-DD HH:MM:SS，不填则立即发布）')
    parser.add_argument('--thumbnail', help='缩略图路径')
    parser.add_argument('--product-link', help='商品链接（抖音）')
    parser.add_argument('--product-title', help='商品标题（抖音）')
    parser.add_argument('--category', help='分类（视频号）')
    
    # Cookie 管理
    parser.add_argument('--login', action='store_true', help='强制重新登录')
    parser.add_argument('--verify-cookie', action='store_true', help='仅验证 Cookie 有效性')
    parser.add_argument('--list-cookies', action='store_true', help='列出所有已保存的 Cookie')
    
    args = parser.parse_args()
    
    # Cookie 管理命令
    if args.list_cookies:
        cookies = cookie_manager.list_cookies()
        print("\n已保存的 Cookie:")
        for platform, accounts in cookies.items():
            print(f"\n{platform}:")
            for account in accounts:
                print(f"  - {account}")
        return
    
    if args.verify_cookie:
        result = asyncio.run(cookie_manager.verify_cookie(args.platform, args.account))
        if result:
            print(f"✅ {args.platform} 账号 {args.account} 的 Cookie 有效")
        else:
            print(f"❌ {args.platform} 账号 {args.account} 的 Cookie 无效或不存在")
        return
    
    if args.login:
        result = asyncio.run(cookie_manager.login_and_save_cookie(args.platform, args.account))
        if result:
            print(f"✅ {args.platform} 账号 {args.account} 登录成功")
        else:
            print(f"❌ {args.platform} 账号 {args.account} 登录失败")
        return
    
    # 检查必需参数
    if not args.video or not args.title:
        print("❌ 错误: --video 和 --title 参数不能为空")
        print("💡 使用 --login 进行登录（不需要 --video 和 --title）")
        sys.exit(1)
    
    # 上传视频
    upload_funcs = {
        'douyin': upload_douyin,
        'kuaishou': upload_kuaishou,
        'tiktok': upload_tiktok,
        'tencent': upload_tencent,
        'xhs': upload_xhs,
    }
    
    upload_func = upload_funcs.get(args.platform)
    if upload_func is None:
        print(f"❌ 不支持的平台: {args.platform}")
        return
    
    try:
        result = asyncio.run(upload_func(args))
        if result:
            print(f"\n✅ 视频上传成功！")
        else:
            print(f"\n❌ 视频上传失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 上传过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
