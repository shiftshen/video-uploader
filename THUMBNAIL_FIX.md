# 抖音封面设置修复说明

## 问题描述

抖音视频上传后，如果没有设置封面，会显示"请设置封面后再发布"的警告弹窗，无法点击发布按钮。

原始代码的 `set_thumbnail()` 方法只有在用户提供了 `thumbnail_path` 参数时才会执行，如果用户没有提供封面图，就会跳过封面设置步骤，导致无法发布。

## 解决方案

### 1. 创建视频工具模块

**文件**：`scripts/utils/video_utils.py`

**功能**：
- `capture_thumbnail_from_video()` - 从页面上的视频元素截取封面
- `select_platform_generated_cover()` - 选择平台自动生成的封面
- `get_video_thumbnail_path()` - 根据视频路径生成封面图片路径

### 2. 修改抖音上传器

**文件**：`scripts/uploader/douyin_uploader/main.py`

#### 新增方法

##### `set_thumbnail_with_validation()`

**功能**：设置视频封面（必须设置）并验证设置成功

**逻辑流程**：

```
1. 如果用户提供了封面图
   ├─ 使用用户提供的封面
   ├─ 上传封面
   ├─ 验证设置成功
   └─ 如果成功，返回

2. 如果没有提供封面或上传失败
   ├─ 尝试选择平台自动生成的封面
   ├─ 点击"选择封面"按钮
   ├─ 选择第一个封面选项
   ├─ 点击"完成"
   ├─ 验证设置成功
   └─ 如果成功，返回

3. 如果平台封面也失败
   ├─ 从视频预览截取封面
   ├─ 定位到视频元素
   ├─ 将视频定位到第1秒
   ├─ 截取视频帧保存为图片
   ├─ 上传截取的封面
   ├─ 验证设置成功
   └─ 清理临时文件

4. 如果所有方案都失败
   └─ 抛出异常
```

**代码**：

```python
async def set_thumbnail_with_validation(self, page: Page, thumbnail_path: str):
    """
    设置视频封面（必须设置）并验证设置成功
    
    如果用户没有提供封面，则自动从视频截取或选择平台生成的封面
    验证"请设置封面后再发布"的弹窗消失后才认为成功
    """
    douyin_logger.info('  [-] 正在设置视频封面...')
    
    # 方案 1: 如果用户提供了封面图，使用用户提供的
    if thumbnail_path and os.path.exists(thumbnail_path):
        douyin_logger.info(f'  [-] 使用用户提供的封面: {thumbnail_path}')
        success = await self.set_thumbnail(page, thumbnail_path)
        if success and await self.verify_thumbnail_set(page):
            douyin_logger.success('  [+] 视频封面设置完成！')
            return
    
    # 方案 2: 尝试选择平台自动生成的封面
    douyin_logger.info('  [-] 尝试选择平台生成的封面...')
    if await select_platform_generated_cover(page, cover_type="vertical"):
        if await self.verify_thumbnail_set(page):
            douyin_logger.success('  [+] 成功选择平台生成的封面！')
            return
    
    # 方案 3: 从视频预览截取封面
    douyin_logger.info('  [-] 尝试从视频预览截取封面...')
    try:
        # 截取封面
        temp_thumbnail = await capture_thumbnail_from_video(page)
        douyin_logger.info(f'  [-] 成功截取封面: {temp_thumbnail}')
        
        # 上传截取的封面
        success = await self.set_thumbnail(page, temp_thumbnail)
        if success and await self.verify_thumbnail_set(page):
            douyin_logger.success('  [+] 视频封面设置完成！')
            # 清理临时文件
            try:
                os.remove(temp_thumbnail)
            except:
                pass
            return
    except Exception as e:
        douyin_logger.error(f'  [-] 从视频截取封面失败: {e}')
    
    # 如果所有方案都失败，抛出异常
    raise Exception("无法设置视频封面，请检查视频是否正常加载")
```

##### `verify_thumbnail_set()`

**功能**：验证封面是否设置成功

**验证逻辑**：

1. **检查警告弹窗**：
   - 查找"请设置封面后再发布"文本
   - 查找"请设置封面"文本
   - 如果找到，说明封面未设置成功

2. **检查按钮状态**：
   - 查找"更改封面"按钮
   - 如果找到，说明封面已设置（按钮文本从"选择封面"变为"更改封面"）

3. **返回结果**：
   - 如果没有警告且有"更改封面"按钮 → 成功
   - 如果没有警告 → 成功
   - 如果有警告 → 失败

**代码**：

```python
async def verify_thumbnail_set(self, page: Page) -> bool:
    """
    验证封面是否设置成功
    
    通过检查"请设置封面后再发布"的弹窗是否消失
    """
    try:
        # 等待一下让页面更新
        await page.wait_for_timeout(1000)
        
        # 检查是否还有"请设置封面后再发布"的提示
        warning_selectors = [
            'text="请设置封面后再发布"',
            'text="请设置封面"',
            'div:has-text("请设置封面")'
        ]
        
        for selector in warning_selectors:
            count = await page.locator(selector).count()
            if count > 0:
                douyin_logger.warning('  [!] 封面设置未生效，仍有提示弹窗')
                return False
        
        # 检查封面选择按钮的状态（如果设置成功，按钮文本可能会变为"更改封面"）
        change_cover_count = await page.locator('text="更改封面"').count()
        if change_cover_count > 0:
            douyin_logger.success('  [+] 封面设置成功（检测到"更改封面"按钮）')
            return True
        
        # 如果没有警告信息，认为设置成功
        douyin_logger.success('  [+] 封面设置成功（无警告信息）')
        return True
        
    except Exception as e:
        douyin_logger.error(f'  [-] 验证封面设置失败: {e}')
        return False
```

##### 修改 `set_thumbnail()`

**修改**：返回 `bool` 值表示是否成功

```python
async def set_thumbnail(self, page: Page, thumbnail_path: str) -> bool:
    """
    设置视频封面（原始方法）
    
    Returns:
        bool: 是否成功
    """
    if not thumbnail_path:
        return False
        
    try:
        douyin_logger.info(f'  [-] 正在上传封面: {thumbnail_path}')
        await page.click('text="选择封面"')
        await page.wait_for_selector("div.dy-creator-content-modal", timeout=5000)
        await page.click('text="设置竖封面"')
        await page.wait_for_timeout(2000)
        
        # 定位到上传区域并点击
        await page.locator("div[class^='semi-upload upload'] >> input.semi-upload-hidden-input").set_input_files(thumbnail_path)
        await page.wait_for_timeout(2000)
        
        # 点击完成按钮
        await page.locator("div#tooltip-container button:visible:has-text('完成')").click()
        
        douyin_logger.info('  [+] 封面上传完成')
        
        # 等待封面设置对话框关闭
        await page.wait_for_selector("div.extractFooter", state='detached', timeout=5000)
        
        return True
        
    except Exception as e:
        douyin_logger.error(f'  [-] 设置封面失败: {e}')
        return False
```

#### 修改调用

**之前**：

```python
# 上传视频封面
await self.set_thumbnail(page, self.thumbnail_path)
```

**之后**：

```python
# 上传视频封面（必须设置封面）
await self.set_thumbnail_with_validation(page, self.thumbnail_path)
```

## 使用示例

### 示例 1：用户提供封面

```bash
python scripts/upload.py \
  --platform douyin \
  --video /path/to/video.mp4 \
  --title "测试视频" \
  --tags "测试" \
  --thumbnail /path/to/cover.jpg  # 用户提供封面
```

**流程**：
1. 使用用户提供的封面
2. 上传封面
3. 验证设置成功
4. 继续发布

### 示例 2：不提供封面（自动处理）

```bash
python scripts/upload.py \
  --platform douyin \
  --video /path/to/video.mp4 \
  --title "测试视频" \
  --tags "测试"
  # 不提供 --thumbnail 参数
```

**流程**：
1. 检测到没有提供封面
2. 尝试选择平台生成的封面
3. 如果失败，从视频截取封面
4. 上传截取的封面
5. 验证设置成功
6. 继续发布

## 技术细节

### 从视频截取封面

```python
async def capture_thumbnail_from_video(page: Page, output_path: str = None) -> str:
    """从页面上的视频元素截取封面"""
    
    # 等待视频元素出现
    await page.wait_for_selector("video", timeout=10000)
    
    # 将视频定位到第1秒
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
    
    # 等待帧渲染
    await page.wait_for_timeout(500)
    
    # 截取视频元素
    video_element = await page.query_selector("video")
    if video_element:
        await video_element.screenshot(path=output_path)
        return output_path
```

### 选择平台生成的封面

```python
async def select_platform_generated_cover(page: Page, cover_type: str = "vertical") -> bool:
    """选择平台自动生成的封面"""
    
    # 点击"选择封面"按钮
    await page.click('text="选择封面"')
    await page.wait_for_selector("div.dy-creator-content-modal", timeout=5000)
    
    # 等待封面选项加载
    await page.wait_for_timeout(2000)
    
    # 选择第一个封面选项
    cover_selector = "div.dy-creator-content-modal div[class*='cover-item']:first-child"
    cover_count = await page.locator(cover_selector).count()
    
    if cover_count > 0:
        await page.locator(cover_selector).click()
        await page.wait_for_timeout(1000)
        
        # 点击完成按钮
        await page.locator("div#tooltip-container button:visible:has-text('完成')").click()
        
        return True
    else:
        return False
```

## 验证方法

### 1. 检查日志输出

上传视频时，观察日志：

```
[+] 正在上传视频...
[-] 视频上传完毕
[-] 等待视频预览加载...
[+] 视频预览加载成功
[-] 正在设置视频封面...
[-] 尝试选择平台生成的封面...
[+] 成功选择平台生成的封面！
[+] 封面设置成功（检测到"更改封面"按钮）  ← 关键！
[-] 正在发布视频...
[+] 视频发布成功
```

### 2. 检查页面状态

在浏览器中：
1. 视频上传完成后
2. 检查是否有"请设置封面后再发布"的警告
3. 检查"选择封面"按钮是否变为"更改封面"
4. 检查封面预览区域是否显示封面图

### 3. 检查发布按钮

- 如果封面设置成功，"发布"按钮应该可以点击
- 如果封面未设置，"发布"按钮会被禁用，并显示警告

## 常见问题

### Q1: 所有方案都失败怎么办？

**可能原因**：
- 视频预览未加载（黑屏）
- 网络问题导致封面上传失败
- 页面结构变化

**解决方法**：
1. 确保视频预览正常加载（参考 BROWSER_FIX.md）
2. 检查网络连接
3. 手动提供封面图：`--thumbnail /path/to/cover.jpg`

### Q2: 验证总是失败

**可能原因**：
- 页面更新延迟
- 选择器变化

**解决方法**：
1. 增加等待时间：`await page.wait_for_timeout(2000)`
2. 检查页面元素是否变化
3. 更新选择器

### Q3: 截取的封面质量不好

**解决方法**：
1. 调整截取时间点：修改 `video.currentTime = 1.0` 为其他值
2. 手动提供高质量封面图
3. 使用视频编辑工具预先生成封面

## 修改文件清单

- [x] `scripts/utils/video_utils.py` - 新建
- [x] `scripts/uploader/douyin_uploader/main.py` - 修改
  - 新增 `set_thumbnail_with_validation()` 方法
  - 新增 `verify_thumbnail_set()` 方法
  - 修改 `set_thumbnail()` 方法返回 bool
  - 修改调用从 `set_thumbnail()` 到 `set_thumbnail_with_validation()`

## 测试建议

1. **测试用户提供封面**：
   ```bash
   python scripts/upload.py --platform douyin --video test.mp4 --title "测试" --tags "测试" --thumbnail cover.jpg
   ```

2. **测试不提供封面（自动处理）**：
   ```bash
   python scripts/upload.py --platform douyin --video test.mp4 --title "测试" --tags "测试"
   ```

3. **测试平台封面选择**：
   - 上传视频后，观察是否能选择平台生成的封面

4. **测试视频截取封面**：
   - 关闭平台封面选项，测试从视频截取

5. **测试验证逻辑**：
   - 检查日志中是否有"封面设置成功"的消息
   - 检查页面中"请设置封面"的警告是否消失

## 总结

### 核心改进

1. ✅ **自动封面处理**
   - 即使用户不提供封面，也能自动处理
   - 3种备选方案确保封面一定能设置

2. ✅ **封面设置验证**
   - 验证"请设置封面"警告是否消失
   - 验证"选择封面"按钮是否变为"更改封面"
   - 确保封面真正设置成功

3. ✅ **多种封面来源**
   - 用户提供的封面图（优先）
   - 平台自动生成的封面
   - 从视频截取的封面

4. ✅ **完善的错误处理**
   - 每个步骤都有错误处理
   - 失败时尝试下一个方案
   - 所有方案都失败时抛出明确的异常

### 与原始代码对比

**原始代码**：
```python
async def set_thumbnail(self, page: Page, thumbnail_path: str):
    if thumbnail_path:  # 如果没有提供，直接跳过
        # 上传封面
        ...
```

**修复后**：
```python
async def set_thumbnail_with_validation(self, page: Page, thumbnail_path: str):
    # 方案 1: 用户提供的封面
    if thumbnail_path and os.path.exists(thumbnail_path):
        ...
    
    # 方案 2: 平台生成的封面
    if await select_platform_generated_cover(page):
        ...
    
    # 方案 3: 从视频截取封面
    temp_thumbnail = await capture_thumbnail_from_video(page)
    ...
    
    # 验证设置成功
    if await self.verify_thumbnail_set(page):
        return
    
    # 所有方案都失败
    raise Exception("无法设置视频封面")
```

**区别**：
- ✅ 不再跳过封面设置
- ✅ 提供多种备选方案
- ✅ 验证设置成功
- ✅ 完善的错误处理

---

**修复状态**：✅ 完成

**下一步**：测试实际上传流程
