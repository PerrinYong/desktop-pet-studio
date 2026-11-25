# 两张循环动图

「好耶」用下蹲、拉长、腾空、回落表达突然开心；「反复横跳」用左右摆动表达纠结与摇摆。每张使用 4 个独立姿态，按 8 个时序帧播放，10 fps、总长 800 ms、无限循环。文字固定，主体改变姿态。

- [好耶](exports/好耶.gif) · [反复横跳](exports/反复横跳.gif)：240 × 240，透明背景。
- [生成图集](raw/)与[提示词](prompts/)保留生成来源。
- [帧目录](frames/)包含原始格子裁切 `source-*`、标准化关键帧 `key-*` 和带重复停留的播放帧 `frame-*`。
- [时序](timing.json)、[验证记录](validation.json)与[预览](preview/)用于复核。

## 复现

Windows PowerShell / System.Drawing 完成图集切分、等比缩放和中文排字，FFmpeg 负责透明 GIF 编码。字体为 Microsoft YaHei。导出脚本默认拒绝覆盖已有帧与成片；先复制本套目录到新的工作目录，仅保留该副本中的 `animation/raw`、`animation/prompts` 与脚本，再运行：

```powershell
pwsh -File scripts/export-animation.ps1 -FFmpeg '你的ffmpeg.exe路径'
```

本轮两张属于附加聊天素材，与 8 张静态主图分开存放。验证覆盖尺寸、循环时序、透明度和解码残影，尚未在微信客户端实发。
