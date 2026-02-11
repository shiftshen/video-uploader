# Cookie 文件目录

这个目录用于存储各平台的登录 Cookie。

## 文件命名规则

`{platform}_{account}.json`

例如：
- `douyin_default.json` - 抖音默认账号
- `tiktok_mybusiness.json` - TikTok 商业账号
- `kuaishou_personal.json` - 快手个人账号

## Cookie 文件格式

使用 Playwright 的 `storage_state` 格式（JSON）：

```json
{
  "cookies": [...],
  "origins": [...]
}
```

## 安全提示

⚠️ **不要将 Cookie 文件提交到 Git 仓库！**

Cookie 包含敏感的登录信息，泄露后可能导致账号被盗。

本目录已在 `.gitignore` 中排除。
