# Video Uploader - 多平台视频自动上传工具

完整的视频自动上传解决方案，支持抖音、快手、TikTok、视频号、小红书等平台。

**核心特性**：
- ✅ **Cookie 自动管理**：首次登录后自动保存，后续无需重复登录
- ✅ **Cookie 验证**：每次上传前自动验证，失效时提示重新登录
- ✅ **多账号支持**：每个平台可管理多个账号
- ✅ **完整的上传功能**：标题、标签、封面、定时发布等
- ✅ **浏览器反检测**：使用 stealth.js 和自定义配置绕过平台检测

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r references/requirements.txt
playwright install chromium firefox
```

### 2. 首次使用（登录）

```bash
# 登录抖音账号
python scripts/upload.py --platform douyin --login --account my_account

# 登录 TikTok 账号
python scripts/upload.py --platform tiktok --login --account my_tiktok
```

浏览器会自动打开，完成扫码登录后，Cookie 会自动保存。

### 3. 上传视频

```bash
# 上传到抖音
python scripts/upload.py \
  --platform douyin \
  --account my_account \
  --video /path/to/video.mp4 \
  --title "我的视频标题" \
  --tags "美食,探店,北京"

# 上传到 TikTok
python scripts/upload.py \
  --platform tiktok \
  --account my_tiktok \
  --video /path/to/video.mp4 \
  --title "My Video Title" \
  --tags "food,travel,vlog"
```

## 📋 支持的平台

| 平台 | 标识符 | Cookie 管理 | 多账号 | 定时发布 |
|------|--------|------------|--------|---------|
| 抖音 | `douyin` | ✅ | ✅ | ✅ |
| 快手 | `kuaishou` | ✅ | ✅ | ✅ |
| TikTok | `tiktok` | ✅ | ✅ | ✅ |
| 视频号 | `tencent` | ✅ | ✅ | ✅ |
| 小红书 | `xhs` | ✅ | ✅ | ✅ |

## 🔐 Cookie 管理机制

### Cookie 自动保存

首次登录时，Cookie 会自动保存到 `cookiesFile/` 目录：

```
cookiesFile/
├── douyin_default.json      # 抖音默认账号
├── douyin_account2.json     # 抖音第二个账号
├── tiktok_default.json      # TikTok 默认账号
└── kuaishou_main.json       # 快手主账号
```

### Cookie 自动验证

每次上传前，会自动验证 Cookie 是否有效：
- ✅ 有效：直接使用，无需登录
- ❌ 无效：自动打开浏览器，提示重新登录

### 手动管理 Cookie

```bash
# 列出所有已保存的 Cookie
python scripts/upload.py --list-cookies

# 验证 Cookie 是否有效
python scripts/upload.py --platform douyin --account my_account --verify-cookie

# 强制重新登录
python scripts/upload.py --platform douyin --account my_account --login
```

## 📖 使用示例

### 示例 1：基本上传

```bash
python scripts/upload.py \
  --platform douyin \
  --video video.mp4 \
  --title "美食探店" \
  --tags "美食,探店"
```

### 示例 2：定时发布

```bash
python scripts/upload.py \
  --platform douyin \
  --video video.mp4 \
  --title "明天发布的视频" \
  --tags "测试" \
  --publish-date "2024-12-31 18:00:00"
```

### 示例 3：多账号管理

```bash
# 账号1上传
python scripts/upload.py \
  --platform douyin \
  --account account1 \
  --video video1.mp4 \
  --title "账号1的视频"

# 账号2上传
python scripts/upload.py \
  --platform douyin \
  --account account2 \
  --video video2.mp4 \
  --title "账号2的视频"
```

### 示例 4：抖音商品链接

```bash
python scripts/upload.py \
  --platform douyin \
  --video video.mp4 \
  --title "带货视频" \
  --tags "好物推荐" \
  --product-link "https://..." \
  --product-title "商品名称"
```

## 🎯 完整参数说明

### 必需参数

- `--platform`: 平台名称（douyin/kuaishou/tiktok/tencent/xhs）
- `--video`: 视频文件路径
- `--title`: 视频标题

### 可选参数

- `--tags`: 标签（逗号分隔）
- `--account`: 账号名称（默认：default）
- `--publish-date`: 发布时间（格式：YYYY-MM-DD HH:MM:SS）
- `--thumbnail`: 缩略图路径
- `--product-link`: 商品链接（抖音）
- `--product-title`: 商品标题（抖音）
- `--category`: 分类（视频号）

### Cookie 管理参数

- `--login`: 强制重新登录
- `--verify-cookie`: 验证 Cookie 有效性
- `--list-cookies`: 列出所有 Cookie

## 🔧 工作原理

### 1. Cookie 保存流程

```
首次使用
    ↓
检查 Cookie 文件是否存在
    ↓
[不存在] 打开浏览器
    ↓
用户扫码登录
    ↓
监听页面跳转（登录成功）
    ↓
保存 Cookie 到文件（storage_state）
    ↓
验证 Cookie 有效性
    ↓
完成
```

### 2. 上传流程

```
开始上传
    ↓
检查 Cookie 文件
    ↓
验证 Cookie 有效性
    ↓
[有效] 加载 Cookie 创建浏览器上下文
    ↓
[无效] 重新登录并保存 Cookie
    ↓
访问上传页面
    ↓
填写标题、标签等信息
    ↓
上传视频文件
    ↓
等待上传完成
    ↓
点击发布
    ↓
保存最新的 Cookie
    ↓
完成
```

### 3. 技术细节

**Cookie 存储格式**：Playwright 的 `storage_state` 格式（JSON）

```json
{
  "cookies": [...],
  "origins": [...]
}
```

**Cookie 加载**：

```python
context = await browser.new_context(storage_state="cookie_file.json")
```

**Cookie 保存**：

```python
await context.storage_state(path="cookie_file.json")
```

## 🛠️ 项目结构

```
video-uploader-v2/
├── cookiesFile/              # Cookie 存储目录
│   ├── douyin_default.json
│   ├── tiktok_default.json
│   └── ...
│
├── scripts/                  # 脚本目录
│   ├── upload.py             # 主上传脚本
│   ├── conf.py               # 配置文件
│   │
│   ├── uploader/             # 各平台上传器
│   │   ├── douyin_uploader/
│   │   ├── ks_uploader/
│   │   ├── tk_uploader/
│   │   ├── tencent_uploader/
│   │   └── xhs_uploader/
│   │
│   └── utils/                # 工具模块
│       ├── cookie_manager.py # Cookie 管理器（核心）
│       ├── auth.py           # 认证模块
│       ├── login.py          # 登录模块
│       ├── base_social_media.py
│       ├── files_times.py
│       ├── log.py
│       └── stealth.min.js    # 反检测脚本
│
├── references/               # 参考文档
│   └── requirements.txt
│
└── README.md                 # 本文件
```

## 🔍 故障排除

### 问题 1：Cookie 失效

**现象**：每次都需要重新登录

**原因**：
- Cookie 文件不存在
- Cookie 已过期
- 平台更新了认证机制

**解决**：
```bash
# 删除旧 Cookie
rm cookiesFile/douyin_default.json

# 重新登录
python scripts/upload.py --platform douyin --login
```

### 问题 2：浏览器无法打开

**现象**：报错 "Error: Browser closed"

**原因**：没有图形界面

**解决**：
- 在有桌面环境的系统运行
- 或配置 Xvfb 虚拟显示

### 问题 3：上传失败

**现象**：视频上传后没有发布成功

**原因**：
- 网络问题
- 视频格式不支持
- 平台 UI 变化

**解决**：
- 检查网络连接
- 检查视频格式（推荐 MP4）
- 查看日志输出
- 手动检查浏览器页面

## 📊 与原始项目的对比

### 原始项目（social-auto-upload）

- ✅ 功能完整
- ✅ Cookie 机制完善
- ❌ 代码复杂，不易集成
- ❌ 依赖数据库
- ❌ 有 Web 界面（对 CLI 使用不友好）

### 本项目（video-uploader-v2）

- ✅ **Cookie 机制完全保留**
- ✅ **简化代码结构**
- ✅ **纯 CLI 工具**
- ✅ **无需数据库**
- ✅ **易于集成到 OpenClaw/Manus**
- ✅ **保留所有核心功能**

## 🎉 核心改进

### 1. Cookie 管理器（新增）

创建了独立的 `cookie_manager.py` 模块：
- 统一管理所有平台的 Cookie
- 自动验证 Cookie 有效性
- 支持多账号
- 简化的 API

### 2. 统一上传入口

`upload.py` 提供统一的命令行接口：
- 所有平台使用相同的参数格式
- 自动处理 Cookie 验证和登录
- 清晰的错误提示

### 3. 完整保留原始功能

- ✅ 所有平台的上传器代码完全保留
- ✅ Cookie 保存和加载机制完全保留
- ✅ 浏览器反检测配置完全保留
- ✅ 登录流程完全保留

## 📝 开发说明

### 添加新平台

1. 在 `scripts/uploader/` 创建新平台目录
2. 实现上传逻辑
3. 在 `cookie_manager.py` 添加验证函数
4. 在 `upload.py` 添加上传函数

### 修改 Cookie 验证逻辑

编辑 `scripts/utils/cookie_manager.py`：

```python
async def verify_cookie_platform(self, cookie_path: Path) -> bool:
    """验证平台 Cookie"""
    # 实现验证逻辑
    pass
```

## 🙏 致谢

本项目基于 [social-auto-upload](https://github.com/lijingpan/social-auto-upload) 项目，保留了其核心的 Cookie 管理和上传机制，并进行了简化和优化。

## 📄 许可证

MIT License

---

**重要提醒**：
1. 首次使用每个平台时，必须先登录：`--login`
2. Cookie 会自动保存，后续无需重复登录
3. Cookie 失效时会自动提示重新登录
4. 每个平台可以管理多个账号，使用 `--account` 区分
