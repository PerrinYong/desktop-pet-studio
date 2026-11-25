> 直接使用：[本专辑成品](../../成品/12-有事您招呼/README.md)，含全部静态格式及可用动图；制作历史保留如下。

> **当前推荐： [图文融合版](revisions/图文融合-v2/README.md)**（2026-11-26）。文案和画面重新共同构图；本页原有素材链接保留为初版记录。投稿脚本现采用新版，集中素材见 [新版投稿目录](../../微信投稿/当前/12-有事您招呼)。

# 林小羊 · 有事您招呼

8 张通用商务沟通动图，延续《随时招呼》的林小羊形象。通过招呼、邀约、确认、安排、等候与致谢推进交流；文字与画面均不点明具体行业或场所。

[动态总览](animation/preview/八张动图总览.gif) · [GIF 成品](animation/exports/) · [微信投稿目录](../../微信投稿/历史/素材/12-有事您招呼/) · [浅底总览](animation/preview/contact-light.jpg) · [深底总览](animation/preview/contact-dark.jpg)

## 文案与动作

| 编号 | 文案 | 含义词 | 动作 | 沟通用途 |
| --- | --- | --- | --- | --- |
| 01 | 老板好 | 问候 | 挥手招呼 | 初次开场或熟客问候 |
| 02 | 今晚有空吗 | 邀约 | 抬头看手机、伸蹄询问 | 轻松询问对方是否方便 |
| 03 | 收到收到 | 收到 | 点头、竖拇指 | 接收到信息后积极回应 |
| 04 | 马上安排 | 安排 | 抱着清单原地小跑 | 开始处理已经确认的请求 |
| 05 | 给您留着 | 预留 | 把心形抱紧、松开 | 确认已经替对方预留 |
| 06 | 不急慢慢来 | 不催 | 坐着慢慢抬蹄示意 | 等候时缓解对方赶时间的压力 |
| 07 | 谢谢照顾 | 感谢 | 拱蹄鞠躬、起身 | 结束交流或收到支持后致谢 |
| 08 | 下次再约 | 再约 | 回头挥手、轻轻抬脚 | 自然收尾，留下下次联系空间 |

“老板好”作为轻松敬称；“今晚有空吗”适合已有交流基础的联系人。预留类回应在确认办妥后使用，具体人数、时间和地点另用文字补充。

## 直接取用

- 动图：animation/exports，每张 240 × 240、透明循环 GIF、1.6 秒完整时序。每张 4 个关键姿态，按 100ms 时基安排动作与停顿，小跑每 0.4 秒重复一次步态。
- 静态备选：[透明底 240](static/transparent-240/) / [纯白底 240](static/white-240/)，每张选用第三个关键姿态，编号一致。
- 专辑配套：[封面 240](assets/cover-240.png)、[图标 50](assets/icon-50.png)、[横幅 750×400](assets/banner-750x400.jpg)、[名称与简介](assets/专辑资料.txt)。
- 投稿主图、120 像素缩略图、配套和上传顺序集中于微信投稿目录。静态备选不混入动态专辑的投稿主图。

## 制作档案

使用内置 image_gen 为每张动图生成 2×2 四姿态图集，再由 System.Drawing 切帧、等比缩放、固定中文排字，FFmpeg 编码 GIF。逐格动作变化来自生成姿态；原始格、加字关键帧、播放时序帧分别保留为 source、key、frame。

[角色参考](references/character.png) · [生成图集与初稿](animation/raw/) · [全部提示词](animation/prompts/) · [序列帧](animation/frames/) · [播放时序](animation/timing.json) · [来源与哈希](provenance.json) · [技术验证](validation.json) · [视觉检查记录](visual-review.json)

邀约的手机持握侧、小跑的前后腿、告别挥手的左右手均经过定向修正。初稿和修正提示词保留；导出只使用最终的 -sheet.png。其余 5 张图集、封面、横幅分别生成，合计保存 13 张生成原图。已有商务静态专辑继续保留。

## 重建

Windows 下使用 PowerShell 7、Microsoft YaHei 字体与 FFmpeg。在专辑目录运行：

```powershell
pwsh -File scripts/export-animation.ps1 -FFmpeg '你的ffmpeg.exe路径' -OutputRoot animation-rebuild
pwsh -File scripts/build-preview.ps1 -FFmpeg '你的ffmpeg.exe路径' -OutputRoot animation-rebuild
pwsh -File scripts/export-support.ps1 -OutputRoot support-rebuild
python scripts/validate.py
```

脚本拒绝覆盖已有导出；配套脚本默认读取正式 animation/frames。验证覆盖正式成品的尺寸、体积、循环、4 个不同姿态、帧时长、透明边缘、解码残影、字幕稳定及静态背景。重建输出如需作为新正式版本，应先审核再替换。

微信投稿目录由仓库根目录 tools/build_wechat_upload.py 生成。尺寸等本地检查已经完成，微信实发和平台审核尚未进行。

