# 热梗动起来 · 图文融合版

2026-11-26 修订，8 张动态表情。保留角色、原文案、含义词和使用场景；逐张重新安排文字、表情、手势与道具，使文字成为动作或情境的一部分。

- [透明图 240](exports/wechat-240/) / [纯白图 240](exports/white-240/)。
- [透明图 512](exports/chat-512/) / [纯白图 512](exports/white-512/) / [缩略图 120](exports/thumbnails-120/)。
- [深底总览](preview/总览-深底.png) / [浅底总览](preview/总览-浅底.png)。
- [循环 GIF](animation/exports/) / [完整序列帧](animation/frames/) / [4 个关键姿势](animation/frames/)；逐张四帧总览在 preview。
- [封面、横幅、图标、简介](assets/)：沿用既有配套资料。
- [集中投稿素材](../../../../微信投稿/当前/06-热梗动起来/)：主图、缩略图、含义词及配套资料。
- [原图与返修图](raw/) / [逐张提示词](prompts/) / [构图与动作清单](pack.json) / [来源与 SHA256](provenance.json) / [技术验证](validation.json)。

生成使用内置 image_gen；导出脚本只负责裁切、尺寸适配、白底合成和动画编码。动图由 4 个不同姿势按原有节奏循环。原始版本保留在[专辑根目录](../../README.md)，初版元数据在 references。

在仓库根目录重新导出：

```powershell
pwsh -NoProfile -File tools/export_integrated_business.ps1 -Character '林小羊' -Album '06-热梗动起来' -FFmpeg '<ffmpeg可执行文件路径>'
python tools/validate_integrated_business.py --all-revisions
```

尺寸、透明度、边缘、白底一致性和来源哈希通过脚本检查；动图另检查帧数、循环、时长和透明残影。文字、构图与关键姿势经目视检查，未代表平台审核通过。
