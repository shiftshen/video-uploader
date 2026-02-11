# 测试指南

## Cookie 机制测试

### 测试 1：首次登录和 Cookie 保存

```bash
# 1. 确保没有 Cookie 文件
rm -f cookiesFile/douyin_default.json

# 2. 执行登录
python scripts/upload.py --platform douyin --login

# 预期结果：
# - 浏览器自动打开
# - 显示抖音登录页面
# - 用户扫码登录后，页面跳转
# - Cookie 自动保存到 cookiesFile/douyin_default.json
# - 显示 "✅ Cookie 验证成功！"
```

### 测试 2：Cookie 重用

```bash
# 1. 确保 Cookie 文件存在
ls -la cookiesFile/douyin_default.json

# 2. 上传视频（不需要登录）
python scripts/upload.py \
  --platform douyin \
  --video test.mp4 \
  --title "测试视频" \
  --tags "测试"

# 预期结果：
# - 不会打开登录页面
# - 直接加载 Cookie 并访问上传页面
# - 显示 "[Cookie] 已加载 douyin 账号 default 的 Cookie"
```

### 测试 3：Cookie 验证

```bash
# 验证 Cookie 是否有效
python scripts/upload.py --platform douyin --verify-cookie

# 预期结果：
# - 显示 "✅ douyin 账号 default 的 Cookie 有效"
# 或
# - 显示 "❌ douyin 账号 default 的 Cookie 无效或不存在"
```

### 测试 4：多账号管理

```bash
# 1. 登录账号1
python scripts/upload.py --platform douyin --account account1 --login

# 2. 登录账号2
python scripts/upload.py --platform douyin --account account2 --login

# 3. 列出所有 Cookie
python scripts/upload.py --list-cookies

# 预期结果：
# douyin:
#   - account1
#   - account2

# 4. 使用不同账号上传
python scripts/upload.py --platform douyin --account account1 --video test1.mp4 --title "账号1"
python scripts/upload.py --platform douyin --account account2 --video test2.mp4 --title "账号2"
```

### 测试 5：Cookie 失效处理

```bash
# 1. 删除 Cookie 文件模拟失效
rm cookiesFile/douyin_default.json

# 2. 尝试上传
python scripts/upload.py \
  --platform douyin \
  --video test.mp4 \
  --title "测试"

# 预期结果：
# - 检测到 Cookie 不存在
# - 显示 "[抖音] Cookie 文件不存在，需要登录"
# - 自动打开浏览器让用户登录
# - 登录成功后继续上传
```

## 上传功能测试

### 测试 6：基本上传

```bash
python scripts/upload.py \
  --platform douyin \
  --video test.mp4 \
  --title "测试视频标题" \
  --tags "测试,视频,上传"

# 预期结果：
# - 视频成功上传
# - 标题和标签正确填写
# - 显示 "✅ 视频上传成功！"
```

### 测试 7：定时发布

```bash
python scripts/upload.py \
  --platform douyin \
  --video test.mp4 \
  --title "定时发布测试" \
  --tags "测试" \
  --publish-date "2024-12-31 18:00:00"

# 预期结果：
# - 定时发布选项被选中
# - 发布时间设置为指定时间
```

### 测试 8：多平台上传

```bash
# 抖音
python scripts/upload.py --platform douyin --video test.mp4 --title "抖音视频" --tags "测试"

# 快手
python scripts/upload.py --platform kuaishou --video test.mp4 --title "快手视频" --tags "测试"

# TikTok
python scripts/upload.py --platform tiktok --video test.mp4 --title "TikTok Video" --tags "test"

# 视频号
python scripts/upload.py --platform tencent --video test.mp4 --title "视频号视频" --tags "测试"

# 小红书
python scripts/upload.py --platform xhs --video test.mp4 --title "小红书视频" --tags "测试"
```

## 错误处理测试

### 测试 9：无效的视频文件

```bash
python scripts/upload.py \
  --platform douyin \
  --video nonexistent.mp4 \
  --title "测试"

# 预期结果：
# - 显示错误信息
# - 程序正常退出
```

### 测试 10：网络问题

```bash
# 断开网络后尝试上传
python scripts/upload.py \
  --platform douyin \
  --video test.mp4 \
  --title "测试"

# 预期结果：
# - 显示网络错误
# - 程序正常退出
```

## Cookie 文件结构验证

### 测试 11：检查 Cookie 文件格式

```bash
# 查看 Cookie 文件内容
cat cookiesFile/douyin_default.json | python -m json.tool

# 预期结果：
# {
#   "cookies": [
#     {
#       "name": "...",
#       "value": "...",
#       "domain": "...",
#       ...
#     }
#   ],
#   "origins": [...]
# }
```

## 性能测试

### 测试 12：Cookie 加载速度

```bash
# 测试 Cookie 加载和验证的时间
time python scripts/upload.py --platform douyin --verify-cookie

# 预期结果：
# - 验证时间 < 10秒
```

## 集成测试

### 测试 13：完整工作流

```bash
# 1. 清理环境
rm -rf cookiesFile/*.json

# 2. 首次登录
python scripts/upload.py --platform douyin --login

# 3. 上传视频
python scripts/upload.py \
  --platform douyin \
  --video test.mp4 \
  --title "完整测试" \
  --tags "测试,完整流程"

# 4. 验证 Cookie
python scripts/upload.py --platform douyin --verify-cookie

# 5. 再次上传（无需登录）
python scripts/upload.py \
  --platform douyin \
  --video test2.mp4 \
  --title "第二次上传" \
  --tags "测试"

# 预期结果：
# - 所有步骤成功完成
# - 第二次上传无需登录
```

## 测试清单

- [ ] Cookie 首次保存
- [ ] Cookie 重用
- [ ] Cookie 验证
- [ ] 多账号管理
- [ ] Cookie 失效处理
- [ ] 基本上传功能
- [ ] 定时发布
- [ ] 多平台支持
- [ ] 错误处理
- [ ] Cookie 文件格式
- [ ] 性能测试
- [ ] 完整工作流

## 已知限制

1. **无头模式**：大部分平台需要非无头模式才能正常上传
2. **图形界面**：需要 X Server 或桌面环境
3. **Cookie 有效期**：Cookie 通常 7-30 天后失效，需要重新登录
4. **平台变化**：平台 UI 更新可能导致脚本失效

## 故障排除

### Cookie 无法保存

**检查**：
```bash
# 确保目录存在且有写权限
ls -la cookiesFile/
chmod 755 cookiesFile/
```

### 浏览器无法打开

**检查**：
```bash
# 确保有图形界面
echo $DISPLAY

# 安装 Playwright 浏览器
playwright install chromium firefox
```

### Cookie 验证失败

**解决**：
```bash
# 删除旧 Cookie
rm cookiesFile/douyin_default.json

# 重新登录
python scripts/upload.py --platform douyin --login
```
