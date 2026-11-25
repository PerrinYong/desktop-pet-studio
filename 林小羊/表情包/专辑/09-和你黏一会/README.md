# 林小羊 · 和你黏一会

16 张情侣日常动图，覆盖想念、亲近、见面吃饭、体谅、安慰、道歉和晚安。延续林小羊柔软、轻松的表达方式，让用户可以借这个形象直接说出一句话。

[亲近与日常 · 动态总览](animation/preview/01-亲近与日常.gif) · [陪伴与和好 · 动态总览](animation/preview/02-陪伴与和好.gif) · [GIF 主图](animation/exports/) · [含义词](含义词.txt)

| 编号 | 文案 | 含义词 | 使用时机 |
| --- | --- | --- | --- |
| 01 | [想你了](animation/exports/想你了.gif) | 想念 | 分开时主动表达想念 |
| 02 | [贴贴](animation/exports/贴贴.gif) | 亲近 | 想黏着对方、回应亲近 |
| 03 | [亲一口](animation/exports/亲一口.gif) | 亲亲 | 双方喜欢的亲昵玩笑 |
| 04 | [心动了](animation/exports/心动了.gif) | 心动 | 收到夸奖、照片或可爱的举动 |
| 05 | [接你下班](animation/exports/接你下班.gif) | 接人 | 约好下班见面，告知前来接人 |
| 06 | [一起吃饭](animation/exports/一起吃饭.gif) | 邀约 | 约吃饭、一起安排日常 |
| 07 | [给你留一口](animation/exports/给你留一口.gif) | 分享 | 吃到好吃的，想给对方留一点 |
| 08 | [你先忙](animation/exports/你先忙.gif) | 体谅 | 对方工作或学习时，表示可以稍后再聊 |
| 09 | [到家说一声](animation/exports/到家说一声.gif) | 关心 | 分别后关心安全抵达，按双方习惯使用 |
| 10 | [抱抱就好](animation/exports/抱抱就好.gif) | 安慰 | 难过时想得到拥抱，也可回应对方的委屈 |
| 11 | [我在呢](animation/exports/我在呢.gif) | 陪伴 | 对方想倾诉时给予回应 |
| 12 | [对不起嘛](animation/exports/对不起嘛.gif) | 道歉 | 小摩擦后主动道歉，具体事情另用文字说明 |
| 13 | [和好好不好](animation/exports/和好好不好.gif) | 和好 | 争执缓和后试着重新靠近，允许对方稍后回应 |
| 14 | [被你拿捏](animation/exports/被你拿捏.gif) | 宠溺 | 对方撒娇或做了可爱的事，玩笑表达心软 |
| 15 | [晚安宝宝](animation/exports/晚安宝宝.gif) | 晚安 | 双方习惯这种称呼时结束聊天 |
| 16 | [梦里见](animation/exports/梦里见.gif) | 思念 | 晚安后再留一句亲昵的告别 |

## 设计思路

这次把情侣交流分成“表达喜欢”和“接住对方”两类。前八张以想念、亲近、约见和分享为主，后八张补充报平安、安慰、道歉、和好和晚安。图能独立发送，也能放在具体文字后面。

单角色图可以由双方轮流使用，不限定性别。双角色图中，无配饰的是林小羊，淡绿色围巾用于区分伴侣；不另起角色名字，不设定谁必须主动照顾谁。双人互动表现为相互靠近、亲脸颊、一起吃饭和伸蹄和好。

「你先忙」把手机放下，表示可以晚点聊；「我在呢」留出倾听的位置；「对不起嘛」适合轻微摩擦，具体道歉仍应说清事情；「和好好不好」表达邀请。「被你拿捏」用羊毛身体软成一摊表达心软，沿用玩笑口语，不宣称是本月新热梗。

## 动画与完整资产

每张 4 个独立姿态，16 个播放时序帧、1.6 秒透明循环，固定字幕。两张总览每页 8 张，便于在聊天窗口检查。

[参考母版](references/character-master.png) · [生成原图](animation/raw/) · [逐张提示词](animation/prompts/) · [序列帧](animation/frames/) · [生成来源](provenance.json) · [技术校验](validation.json)

内置 image_gen 生成 2 × 2 图集。System.Drawing 等比缩放、裁切图格、用 Microsoft YaHei 排字，FFmpeg 输出 240 × 240 GIF。source 为原始格子，key 为标准化关键帧，frame 为安排停顿后的播放帧。保留所有生成及修正版本，最终采用版本见来源清单。

在 Windows 下重新导出（需 Microsoft YaHei 和 FFmpeg）：

```powershell
pwsh -File scripts/export-animation.ps1 -FFmpeg '你的ffmpeg.exe路径' -OutputRoot rebuild
pwsh -File scripts/build-preview.ps1 -FFmpeg '你的ffmpeg.exe路径' -OutputRoot rebuild
```

脚本拒绝覆盖已有帧或成片，可换 OutputRoot 重建。Python 3 / Pillow 验证 GIF 尺寸、体积、循环、字幕稳定、透明边缘、解码残影和原图哈希。双角色图另外检查角色数量、位置、肢体与互动动作。尚未进行微信实发或平台审核，也没有真实发送数据证明受欢迎程度。

本套新增 16 张，连同此前 26 张，林小羊累计有 42 张动态聊天素材。

制作复查中发现「一起吃饭」首版有半透明底色，已用 image_gen 修正后重新导出。原图 v1、首版帧及预览保留在 raw 与 review 目录；对外使用 animation/exports 中的修正版。需要单独重建一张时，可传入 -OnlyId 06-dinner-date 并指定新的 OutputRoot。

