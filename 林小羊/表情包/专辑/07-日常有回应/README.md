# 林小羊 · 日常有回应

8 张新增动态聊天表情，覆盖出门、报平安、吃饭、安慰、休息、晚安、周末与收到祝福。每张图对应一句能直接发出去的回应。

[动态总览](animation/preview/八张动图总览.gif) · [浅色总览](animation/preview/contact-light.jpg) · [深色总览](animation/preview/contact-dark.jpg) · [GIF 文件](animation/exports/) · [含义词](含义词.txt)

| 文案 | 含义词 | 使用场景 |
| --- | --- | --- |
| [我出发了](animation/exports/我出发了.gif) | 出发 | 约饭、见面前告知已动身 |
| [到家啦](animation/exports/到家啦.gif) | 报平安 | 聚会或出行结束，给家人朋友报平安 |
| [开饭了](animation/exports/开饭了.gif) | 吃饭 | 约饭、晒饭或招呼大家吃饭 |
| [抱抱你](animation/exports/抱抱你.gif) | 安慰 | 朋友委屈、累了或想被安慰 |
| [回血中](animation/exports/回血中.gif) | 休息 | 忙完后短暂休息，稍后再聊 |
| [晚安老己](animation/exports/晚安老己.gif) | 晚安 | 结束聊天，对自己说声晚安 |
| [周末开摆](animation/exports/周末开摆.gif) | 放松 | 周末不排任务，进入休息状态 |
| [接住好运](animation/exports/接住好运.gif) | 祝福 | 收到红包、祝福或好消息，开心回应 |

## 设计与用法

- 「我出发了」「到家啦」承接约见与报平安，动作分别是背包走路和举钥匙挥手。
- 「开饭了」表现举勺、吃一口、满足地嚼，适合招呼和分享日常。
- 「抱抱你」朝屏幕前的人张开蹄子，与上一套「爱你老己」抱住自己的动作区分。
- 「回血中」用热饮与小毯子表达休息；「晚安老己」是前套自我关怀语气的晚安改编，不宣称它是独立新热梗。
- 「周末开摆」滑进靠垫、放松身体；「接住好运」接住红包后抱紧弹起，可回应祝福，不代表索要红包。

保留奶油白羊毛、卷角、垂耳、黑蹄和温柔的疲惫感。活泼动作循环较快，安慰和休息场景保留更长停顿。

## 完整素材

[生成原图](animation/raw/) · [逐张提示词](animation/prompts/) · [角色参考](references/character-master.png) · [序列帧](animation/frames/) · [来源记录](provenance.json) · [技术校验](validation.json)

内置 image_gen 生成每张 2 × 2 姿态图集；System.Drawing 切分、等比缩放，并用 Microsoft YaHei 固定排字；FFmpeg 编码为 240 × 240 透明循环 GIF。每张 4 个不同姿态，走路循环 0.8 秒，其余 1.6 秒。帧目录保留原始裁切 source、加字后的 key 和按时序排列的 frame。

重新导出（Windows，需 Microsoft YaHei 字体和 FFmpeg）：

```powershell
pwsh -File scripts/export-animation.ps1 -FFmpeg '你的ffmpeg.exe路径' -OutputRoot rebuild
pwsh -File scripts/build-preview.ps1 -FFmpeg '你的ffmpeg.exe路径' -OutputRoot rebuild
```

导出脚本拒绝覆盖已有成片，可更换 OutputRoot 重建。验证脚本使用 Python 3 与 Pillow。检查覆盖 GIF 尺寸、体积、循环、字幕稳定、透明边缘及解码残影；微信实发与平台审核尚未进行。

本套为第 07 套，新增 8 张；连同此前 10 张，林小羊累计有 18 张动态聊天素材。

