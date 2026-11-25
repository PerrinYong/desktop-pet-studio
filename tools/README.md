# 工具入口

| 目的 | 工具 |
| --- | --- |
| 按选帧配置生成静态、汇总静态／动态成品、生成浏览页并验证 | build_sticker_library.py |
| 从高清原帧裁切、缩放、合成纯白底 | export_still_frames.ps1（由上一脚本调用） |
| 组装当前微信投稿包与动图的静态备选 | build_wechat_upload.py |
| 导出图文融合修订的动画和原静态图 | export_integrated_business.ps1 |
| 验证图文融合修订 | validate_integrated_business.py |
| 检查生成原图透明度 | audit_integrated_alpha.py |

日常按「制作源文件 → 成品 → 投稿包」维护，命令和目录规则见[目录说明](../docs/目录与投稿素材.md)。静态精选的配置在角色/表情包/静帧选择.json；成品清单记录来源，不手工修改生成目录。

本次从已有高清 PNG 帧制作静态版，没有调用图像模型重绘。已修订的动图和原素材保持不变。
