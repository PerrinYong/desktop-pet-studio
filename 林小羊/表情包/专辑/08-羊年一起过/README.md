> 直接使用：[本专辑成品](../../成品/08-羊年一起过/README.md)，含全部静态格式及可用动图；制作历史保留如下。

> 当前使用[图文融合版](revisions/图文融合-v2/README.md)。下文保留初版记录；投稿素材由 投稿.json 的 source_dir 选择新版。

# 林小羊 · 羊年一起过

8 张春节动态聊天表情：拜年祝福、感谢红包、团圆饭、守岁、走亲戚、饭桌转场、春节后开工。保留林小羊原有的卷角、垂耳、点眼、奶油白羊毛与柔软身体，加少量朱红、暖金节日元素。

[动态总览](animation/preview/八张动图总览.gif) · [浅色总览](animation/preview/contact-light.jpg) · [深色总览](animation/preview/contact-dark.jpg) · [GIF 主图](animation/exports/) · [含义词](含义词.txt)

| 文案 | 含义词 | 使用场景 |
| --- | --- | --- |
| [羊年大吉](animation/exports/羊年大吉.gif) | 拜年 | 羊年新春主动问候、向长辈亲友拜年 |
| [恭喜发财](animation/exports/恭喜发财.gif) | 祝福 | 互道吉利话、向朋友回祝 |
| [谢谢红包](animation/exports/谢谢红包.gif) | 感谢 | 已经收到红包后致谢 |
| [年夜饭开席](animation/exports/年夜饭开席.gif) | 团圆饭 | 除夕人齐了、招呼亲友开饭 |
| [守岁中](animation/exports/守岁中.gif) | 守岁 | 除夕夜聊天、等零点时的困倦自嘲 |
| [串门来啦](animation/exports/串门来啦.gif) | 拜访 | 已约好走亲访友，告知自己来了 |
| [先吃饭哈](animation/exports/先吃饭哈.gif) | 转场 | 熟人饭桌上轻松暂停追问、邀请先吃饭 |
| [开工大吉](animation/exports/开工大吉.gif) | 开工 | 春节后复工当天，在同事群互相祝福 |

## 表达分工

「羊年大吉」拱蹄作揖，适合新春问候；「恭喜发财」捧元宝往前送，是吉利祝愿；「谢谢红包」抱住红包点头，表达已经收到后的感谢。三张的动作与交谈位置各不相同。

「年夜饭开席」张开蹄子邀请大家上桌；「守岁中」困得点头又努力清醒，表达除夕夜的轻度自嘲；「串门来啦」拎礼袋挥手，适合已约好的到访。「先吃饭哈」用温和的停顿手势转向饭碗，给熟人饭桌上的追问留一句缓冲，不保证能代替正式沟通。「开工大吉」在电脑前举蹄打气，不指定初几返工。

动作按 4 个关键姿态构成 1.6 秒循环，字幕位置固定，不以整图平移代替动作。主图均为 240 × 240 透明 GIF。

## 年俗依据与创作边界

核对日期：2026-11-25。沿用项目此前关于年俗、聊天关系与地域差异的研究。本套按“祝福—感谢—团圆—守岁—访亲—返工”选择聊天事件，而不是只给日常表情换红衣服。

- [中国非遗网《萧放：春节礼仪与当代实践》](https://www.ihchina.cn/details/29722.html)列举年夜饭、压岁钱、守岁、拜年等礼俗。本套取其社交场景，不把具体礼仪或家庭日程当作全国统一要求。
- [香港天文台 2027 年公农历对照表](https://my.weather.gov.hk/tc/gts/time/calendar/pdf/files/2027.pdf)标明丁未肖羊，正月初一对应 2027 年 2 月 6 日。除夕在前一天，腊月为小月，因此本套不用“年三十”标注 2027 除夕。
- 饭桌采用通用碗盘，不把全国春节餐食画成固定一道菜。祝愿发财、感谢红包与索要红包分开；本套没有索取动作。开工日期随个人安排，不据此推断假期。
- 羊年题字适用于羊年；其他七张不写年份，可以跨年使用。文案是节日口语与祝福，没有把它们包装为最新互联网热梗或必火选题。

## 原图与制作

[参考母版](references/character-master.png) · [完整生成原图](animation/raw/) · [逐张提示词](animation/prompts/) · [序列帧](animation/frames/) · [生成来源](provenance.json) · [技术验证](validation.json)

内置 image_gen 生成 2 × 2 动作图集，System.Drawing 切分、等比缩放并统一中文排字，FFmpeg 编码。source 为原始裁切，key 为标准化关键帧，frame 为排入时序的播放帧；原图、修正版本和最终成片分别保留。字体使用 Microsoft YaHei。

重新导出（Windows，需上述字体与 FFmpeg）：

```powershell
pwsh -File scripts/export-animation.ps1 -FFmpeg '你的ffmpeg.exe路径' -OutputRoot rebuild
pwsh -File scripts/build-preview.ps1 -FFmpeg '你的ffmpeg.exe路径' -OutputRoot rebuild
```

脚本拒绝覆盖已有帧和成片，可换 OutputRoot 重建。Python 3 / Pillow 验证尺寸、体积、循环、字幕稳定、透明边缘、残影及原图哈希。微信客户端实发、投稿审核尚未进行。

本套新增 8 张，连同此前 18 张，林小羊累计有 26 张动态聊天素材。

