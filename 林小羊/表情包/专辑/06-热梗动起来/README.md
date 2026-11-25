# 林小羊 · 热梗动起来

8 张新增循环 GIF，接续前四套场景表情。以近期仍在使用的大陆互联网表达为主，加入日常协作回应。梗的核对时间、来源和改编关系见 [选题调研](research/热梗选题.md)。

[动态总览](animation/preview/八张动图总览.gif) · [浅色总览](animation/preview/contact-light.jpg) · [深色总览](animation/preview/contact-dark.jpg) · [GIF 主图](animation/exports/) · [含义词](含义词.txt)

| 文案 | 含义词 | 场景 |
| --- | --- | --- |
| [爱你老己](animation/exports/爱你老己.gif) | 自爱 | 累了、做完一件事，抱抱自己 |
| [夯爆了](animation/exports/夯爆了.gif) | 赞叹 | 朋友作品好看、方案很棒 |
| [拉完了](animation/exports/拉完了.gif) | 翻车 | 自己的演示、游戏操作翻车 |
| [手搓中](animation/exports/手搓中.gif) | 制作 | 做原型、写脚本、制作小作品 |
| [我真没招了](animation/exports/我真没招了.gif) | 无奈 | 反复尝试仍没解决，向熟人求助 |
| [画地为牢啊](animation/exports/画地为牢啊.gif) | 困住 | 卡在同一件事里，熟人自嘲 |
| [我要验牌](animation/exports/我要验牌.gif) | 质疑 | 年会没抽中或朋友运气太好，玩笑接梗 |
| [处理中](animation/exports/处理中.gif) | 处理 | 协作群告知正在处理，另补时间和进度 |

## 素材与制作

- [角色参考](references/character-master.png)、[生成原图](animation/raw/)及[逐张提示词](animation/prompts/)完整保留，使用内置 image_gen 生成。
- [序列帧](animation/frames/)中的 source 为图集原始裁切，key 为统一尺寸并添加字幕后的关键帧，frame 为安排停顿后的播放帧。
- 每张 4 个姿态，240 × 240 透明 GIF，无限循环。「夯爆了」「处理中」循环 0.8 秒，其他循环 1.6 秒。
- 中文由 Microsoft YaHei 字体后期统一排版，字幕位置固定。System.Drawing 切分、缩放和排字，FFmpeg 编码，保留可复现脚本。
- [时序与成片哈希](animation/timing.json)、[技术验证](validation.json)、[来源记录](provenance.json)以及 archive-manifest.json 用于归档复核。

## 重新导出

在本套目录运行（Windows，需 PowerShell、System.Drawing、Microsoft YaHei 字体和 FFmpeg）：

```powershell
pwsh -File scripts/export-animation.ps1 -FFmpeg '你的ffmpeg.exe路径' -OutputRoot rebuild
pwsh -File scripts/build-preview.ps1 -FFmpeg '你的ffmpeg.exe路径' -OutputRoot rebuild
```

脚本拒绝覆盖已存在的帧和成片，换一个 OutputRoot 即可重新导出。画面原图保持不变。

本次为聊天素材交付，尚未进行微信客户端实发或平台审核。此前两张「好耶」「反复横跳」仍在原目录，累计已有 10 张动图；这套 8 张是独立新增素材。

