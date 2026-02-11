# 浏览器配置修复说明

## 问题描述

上传视频后，视频预览区域黑屏，无法加载视频画面，导致：
1. 无法截取封面（横屏/竖屏）
2. 无法点击"发布"按钮（因为必须设置封面）
3. 上传流程卡死

## 根本原因

浏览器环境参数缺失或不一致，导致抖音/TikTok 判定为自动化浏览器，页面资源（预览组件/播放器）不加载。

### 典型缺失项

1. **locale**：语言环境未设置
2. **user_agent**：使用默认 UA，容易被识别
3. **Accept-Language**：HTTP 头缺失
4. **timezone_id**：时区未设置
5. **viewport**：视口大小不一致
6. **permissions**：权限未预授权，导致弹窗遮挡

## 解决方案

### 1. 创建完整的浏览器配置模块

文件：`scripts/utils/browser_setup.py`

**核心功能**：
- 统一的浏览器环境参数设置
- 完整的反检测脚本注入
- 权限预授权
- 视频预览加载等待

**关键配置**：

```python
context_options = {
    "storage_state": account_file,
    "locale": "zh-CN",  # 或 "en-US"
    "timezone_id": "Asia/Shanghai",
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    "extra_http_headers": {
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    },
    "permissions": ["geolocation", "notifications"],
    "geolocation": {"longitude": 116.397128, "latitude": 39.916527},
}
```

### 2. 修复所有平台上传器

#### 抖音 (douyin_uploader)

**修改位置**：
- `cookie_auth()` 函数
- `douyin_cookie_gen()` 函数
- `upload()` 方法

**修改内容**：
```python
# 之前
browser = await playwright.chromium.launch(headless=False)
context = await browser.new_context(storage_state=account_file)

# 之后
browser, context = await get_browser_context(
    playwright=playwright,
    account_file=account_file,
    headless=False,
    locale="zh-CN",
    use_chrome=True
)
```

**添加视频预览等待**：
```python
if await wait_for_video_preview(page, timeout=30000):
    douyin_logger.success("视频预览加载成功")
```

#### TikTok (tk_uploader)

**locale**: `"en-US"`
**use_chrome**: `False` (使用 Firefox)

#### 快手 (ks_uploader)

**locale**: `"zh-CN"`
**use_chrome**: `True`

#### 视频号 (tencent_uploader)

**locale**: `"zh-CN"`
**use_chrome**: `True`

#### 小红书 (xhs_uploader)

**locale**: `"zh-CN"`
**use_chrome**: `True`

### 3. 添加权限弹窗处理

在每个上传器的 `upload()` 方法中，创建 page 后立即调用：

```python
page = await context.new_page()
await handle_permissions_dialog(page)
```

### 4. 等待视频预览加载

在视频上传完成后，添加：

```python
if await wait_for_video_preview(page, timeout=30000):
    logger.success("视频预览加载成功")
else:
    logger.warning("视频预览加载超时，但继续执行")
```

## 技术细节

### 反检测脚本注入

```javascript
// 覆盖 navigator.webdriver
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// 覆盖 navigator.plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});

// 添加 window.chrome 对象
window.chrome = {
    runtime: {}
};
```

### 视频预览加载检测

```javascript
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
```

## 验证方法

### 1. 检查浏览器环境

在浏览器控制台执行：

```javascript
console.log({
    locale: navigator.language,
    languages: navigator.languages,
    userAgent: navigator.userAgent,
    webdriver: navigator.webdriver,
    plugins: navigator.plugins.length,
    chrome: window.chrome
});
```

**预期输出**：
```javascript
{
    locale: "zh-CN",
    languages: ["zh-CN", "zh", "en-US", "en"],
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    webdriver: undefined,  // ✅ 不是 true
    plugins: 5,  // ✅ 不是 0
    chrome: { runtime: {} }  // ✅ 存在
}
```

### 2. 检查视频预览

上传视频后：
1. 打开浏览器开发者工具
2. 查看 Network 面板
3. 确认视频文件（.mp4）已加载
4. 查看 Console 是否有错误

### 3. 检查封面选择

1. 视频上传完成后
2. 点击"选择封面"按钮
3. 应该能看到自动生成的封面选项（横屏3:4、竖屏4:3）
4. 预览区应该显示视频画面，不是黑屏

## 常见问题

### Q1: 视频预览仍然黑屏

**可能原因**：
- 浏览器版本过旧
- 视频编码不支持
- 网络问题导致视频未完全上传

**解决方法**：
1. 更新 Playwright 浏览器：`playwright install chromium --force`
2. 检查视频编码：使用 H.264 编码
3. 增加等待时间：`await wait_for_video_preview(page, timeout=60000)`

### Q2: 权限弹窗仍然出现

**解决方法**：
在 `context_options` 中添加更多权限：

```python
"permissions": [
    "geolocation",
    "notifications",
    "camera",
    "microphone"
]
```

### Q3: 仍然被识别为自动化

**解决方法**：
1. 使用本地 Chrome：设置 `LOCAL_CHROME_PATH` 环境变量
2. 使用 Chrome channel：`channel="chrome"` 而不是 `executable_path`
3. 添加更多浏览器参数

## 修改文件清单

- [x] `scripts/utils/browser_setup.py` - 新建
- [x] `scripts/uploader/douyin_uploader/main.py` - 修改
- [x] `scripts/uploader/ks_uploader/main.py` - 修改
- [x] `scripts/uploader/tk_uploader/main.py` - 修改
- [x] `scripts/uploader/tencent_uploader/main.py` - 修改
- [x] `scripts/uploader/xhs_uploader/main.py` - 修改

## 测试建议

1. **本地测试**：在有图形界面的环境测试
2. **逐个平台测试**：先测试抖音，确认可用后再测试其他平台
3. **完整流程测试**：从登录到上传到发布，完整走一遍
4. **多账号测试**：测试多个账号的 Cookie 管理

## 参考资料

- [Playwright Context Options](https://playwright.dev/docs/api/class-browser#browser-new-context)
- [Puppeteer Stealth Plugin](https://github.com/berstend/puppeteer-extra/tree/master/packages/puppeteer-extra-plugin-stealth)
- [抖音创作者中心](https://creator.douyin.com/)
- [TikTok Studio](https://www.tiktok.com/tiktokstudio/)
