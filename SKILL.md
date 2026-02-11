# Video Uploader Skill

自动上传视频到多个社交媒体平台的 Manus/OpenClaw skill。

## 功能概述

这个 skill 可以自动上传视频到以下平台：
- 抖音 (Douyin)
- 快手 (Kuaishou)
- TikTok
- 视频号 (WeChat Channels / Tencent Video)
- 小红书 (Xiaohongshu)

**核心特性**：
- ✅ **Cookie 自动管理**：首次登录后自动保存，后续无需重复登录
- ✅ **Cookie 自动验证**：每次上传前验证有效性，失效时自动提示登录
- ✅ **多账号支持**：每个平台可管理多个账号
- ✅ **完整上传功能**：标题、标签、封面、定时发布等
- ✅ **浏览器反检测**：使用 stealth.js 绕过平台检测

## 安装依赖

```bash
cd /path/to/video-uploader-v2
pip install -r references/requirements.txt
playwright install chromium firefox
```

## 使用方法

### 1. 首次使用（登录）

每个平台首次使用时需要登录一次：

```bash
# 登录抖音
python scripts/upload.py --platform douyin --login

# 登录 TikTok
python scripts/upload.py --platform tiktok --login
```

浏览器会自动打开，完成扫码登录后，Cookie 会自动保存到 `cookiesFile/` 目录。

### 2. 上传视频

登录后，就可以直接上传视频，无需再次登录：

```bash
# 上传到抖音
python scripts/upload.py \
  --platform douyin \
  --video /path/to/video.mp4 \
  --title "我的视频标题" \
  --tags "美食,探店,北京"

# 上传到 TikTok
python scripts/upload.py \
  --platform tiktok \
  --video /path/to/video.mp4 \
  --title "My Video Title" \
  --tags "food,travel,vlog"
```

### 3. Cookie 管理

```bash
# 列出所有已保存的 Cookie
python scripts/upload.py --list-cookies

# 验证 Cookie 是否有效
python scripts/upload.py --platform douyin --verify-cookie

# 强制重新登录
python scripts/upload.py --platform douyin --login
```

## OpenClaw 集成

### 在 OpenClaw 中使用

OpenClaw 可以通过自然语言命令调用这个 skill：

**用户**：帮我把这个视频上传到抖音，标题是"美食探店"

**OpenClaw 执行**：
1. 读取 video-uploader skill
2. 检查抖音 Cookie 是否存在和有效
3. 如果无效，打开浏览器让用户登录
4. 执行上传命令

### 示例命令

```python
# OpenClaw 内部会执行类似这样的命令
import subprocess

subprocess.run([
    "python", "scripts/upload.py",
    "--platform", "douyin",
    "--video", video_path,
    "--title", title,
    "--tags", ",".join(tags)
])
```

## 参数说明

### 必需参数

- `--platform`: 平台名称（douyin/kuaishou/tiktok/tencent/xhs）
- `--video`: 视频文件路径
- `--title`: 视频标题

### 可选参数

- `--tags`: 标签（逗号分隔）
- `--account`: 账号名称（默认：default，用于多账号管理）
- `--publish-date`: 发布时间（格式：YYYY-MM-DD HH:MM:SS，不填则立即发布）
- `--thumbnail`: 缩略图路径
- `--product-link`: 商品链接（抖音）
- `--product-title`: 商品标题（抖音）
- `--category`: 分类（视频号）

### Cookie 管理参数

- `--login`: 强制重新登录
- `--verify-cookie`: 验证 Cookie 有效性
- `--list-cookies`: 列出所有 Cookie

## Cookie 机制说明

### 为什么需要 Cookie？

社交媒体平台需要用户登录才能上传视频。Cookie 保存了登录状态，避免每次都需要扫码登录。

### Cookie 如何保存？

1. 首次使用时，打开浏览器让用户登录
2. 登录成功后，使用 Playwright 的 `storage_state` 功能保存 Cookie
3. Cookie 保存为 JSON 文件，存储在 `cookiesFile/` 目录

### Cookie 如何使用？

1. 每次上传前，先验证 Cookie 是否有效
2. 如果有效，直接加载 Cookie 创建浏览器上下文
3. 如果无效，提示用户重新登录

### Cookie 文件位置

```
cookiesFile/
├── douyin_default.json      # 抖音默认账号
├── douyin_account2.json     # 抖音第二个账号
├── tiktok_default.json      # TikTok 默认账号
└── kuaishou_main.json       # 快手主账号
```

### 多账号管理

使用 `--account` 参数区分不同账号：

```bash
# 账号1
python scripts/upload.py --platform douyin --account account1 --login
python scripts/upload.py --platform douyin --account account1 --video video.mp4 --title "账号1的视频"

# 账号2
python scripts/upload.py --platform douyin --account account2 --login
python scripts/upload.py --platform douyin --account account2 --video video.mp4 --title "账号2的视频"
```

## 工作流程

### 完整流程

```
用户请求上传视频
    ↓
检查 Cookie 文件是否存在
    ↓
[存在] 验证 Cookie 有效性
    ↓
[有效] 加载 Cookie 并上传
    ↓
[无效] 打开浏览器让用户登录
    ↓
用户完成登录
    ↓
保存 Cookie 到文件
    ↓
验证 Cookie 有效性
    ↓
加载 Cookie 并上传
    ↓
上传完成，保存最新的 Cookie
    ↓
完成
```

### 技术实现

**Cookie 保存**：
```python
await context.storage_state(path="cookie_file.json")
```

**Cookie 加载**：
```python
context = await browser.new_context(storage_state="cookie_file.json")
```

**Cookie 验证**：
```python
# 访问平台页面，检查是否出现登录提示
await page.goto("https://creator.douyin.com/...")
if await page.get_by_text("扫码登录").count():
    return False  # Cookie 无效
else:
    return True   # Cookie 有效
```

## 支持的平台

| 平台 | 标识符 | Cookie 管理 | 多账号 | 定时发布 | 特色功能 |
|------|--------|------------|--------|---------|---------|
| 抖音 | `douyin` | ✅ | ✅ | ✅ | 商品链接、缩略图 |
| 快手 | `kuaishou` | ✅ | ✅ | ✅ | 最多3个标签 |
| TikTok | `tiktok` | ✅ | ✅ | ✅ | 隐私设置 |
| 视频号 | `tencent` | ✅ | ✅ | ✅ | 原创声明、合集 |
| 小红书 | `xhs` | ✅ | ✅ | ✅ | 图文混合 |

## 故障排除

### 问题 1：每次都需要重新登录

**原因**：Cookie 文件不存在或已失效

**解决**：
```bash
# 检查 Cookie 是否有效
python scripts/upload.py --platform douyin --verify-cookie

# 如果无效，重新登录
python scripts/upload.py --platform douyin --login
```

### 问题 2：浏览器无法打开

**原因**：没有图形界面（X Server）

**解决**：
- 在有桌面环境的系统运行（Windows/Mac/Linux 桌面）
- 或配置 Xvfb 虚拟显示

### 问题 3：Cookie 验证失败

**原因**：平台更新了 UI 或认证机制

**解决**：
- 删除旧 Cookie：`rm cookiesFile/douyin_default.json`
- 重新登录：`python scripts/upload.py --platform douyin --login`

## 环境要求

- Python 3.8+
- Playwright（自动安装浏览器）
- 图形界面环境（X Server）
- 网络连接

## 项目结构

```
video-uploader-v2/
├── SKILL.md                  # 本文件
├── README.md                 # 详细说明
├── cookiesFile/              # Cookie 存储目录
├── scripts/                  # 脚本目录
│   ├── upload.py             # 主上传脚本
│   ├── uploader/             # 各平台上传器
│   └── utils/                # 工具模块
│       └── cookie_manager.py # Cookie 管理器（核心）
└── references/
    └── requirements.txt
```

## 核心改进

相比原始项目（social-auto-upload），本项目：

1. ✅ **完全保留 Cookie 机制**：使用原始项目的 Cookie 保存和验证逻辑
2. ✅ **简化代码结构**：移除数据库依赖，纯 CLI 工具
3. ✅ **统一接口**：所有平台使用相同的命令格式
4. ✅ **易于集成**：适合 OpenClaw/Manus 调用
5. ✅ **保留核心功能**：所有上传器代码完全保留

## 使用建议

1. **首次使用**：先用 `--login` 登录所有需要的平台
2. **定期验证**：使用 `--verify-cookie` 检查 Cookie 有效性
3. **多账号**：使用有意义的账号名称，如 `--account personal`、`--account business`
4. **错误处理**：如果上传失败，检查日志输出和浏览器页面

## 致谢

本项目基于 [social-auto-upload](https://github.com/lijingpan/social-auto-upload)，完全保留了其核心的 Cookie 管理和上传机制。
