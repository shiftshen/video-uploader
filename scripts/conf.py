"""
配置文件
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent.resolve()

# 本地 Chrome 路径（可选，如果为空则使用 Playwright 自带的浏览器）
LOCAL_CHROME_PATH = os.getenv("LOCAL_CHROME_PATH", "")

# Cookie 文件目录
COOKIES_DIR = BASE_DIR / "cookiesFile"

# 小红书签名服务地址
XHS_SERVER = os.getenv("XHS_SERVER", "http://127.0.0.1:11901")
