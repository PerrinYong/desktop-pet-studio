# 知核 · 桌宠制作完整归档

灰白黏土猫头鹰；本次 session 的原图、动作、校验、视频项目及交付版本归档。后续宠物可在仓库中建立其他名称的同级目录。

## 快速入口

- [最终竖屏宣传视频（54秒）](session/outputs/zhihe-social-dark/zhihe-25min-process.mp4)
- [推荐封面 A](session/outputs/zhihe-social-dark/cover-A-3x4.jpg) · [封面 B](session/outputs/zhihe-social-dark/cover-B-3x4.jpg)
- [发布文案与媒体引用](docs/发布内容.md)
- [宠物图集](assets/spritesheet.png) · [73 帧清单](assets/frames-manifest.json)
- [动作动图](session/outputs/zhihe/previews/) · [原图对应表](raw/generated-image-map.json)
- [制作过程与版本说明](docs/制作过程与版本.md) · [归档校验报告](archive-verification.json)

## 目录

| 目录 | 内容 |
| --- | --- |
| assets/ | 最终透明图集、按动作分类的 73 张原像素单帧 |
| raw/generated-images/ | 13 张原始生成图片，保留生成文件名与任务目录 |
| raw/private-references/ | 用户提供的账号主页参考截图，本地保留并由 .gitignore 排除 |
| session/work/pets/zhihe/ | 提示词、条带原图、早期版本、拆帧、修正、盲测、图集与服务校验 |
| session/work/zhihe-film/ | 横屏视频脚本、素材、音乐、分镜与编码记录 |
| session/work/zhihe-social/ | 竖屏暖色/深色两版脚本、素材与检查记录 |
| session/outputs/zhihe/ | 宠物全部交付文件及原 creation-record.zip |
| session/outputs/zhihe-film/ | 横屏 56 秒宣传片、21 秒幕后片段、封面与项目 ZIP |
| session/outputs/zhihe-social/ | 暖色初稿封面、分镜、字幕；没有导出成片 |
| session/outputs/zhihe-social-dark/ | 最终深色成片、A/B 封面、开场预览、字幕、文案与项目 ZIP |
| tooling/ | 原制作管线工具快照与来源说明 |
| docs/ | 可迁移的发布文档、过程和版本索引 |

## 复现与验证

在本目录使用 Python 3.10+（原环境为 3.14），创建独立环境并安装 requirements.txt。视频字体依赖 Windows 的 Microsoft YaHei/Bahnschrift；其他系统需调整原脚本字体路径。

```powershell
python -m pip install -r requirements.txt
python session/work/zhihe-social/render_social_dark.py --output rebuild/social-dark --stills-only
python session/work/zhihe-social/render_social_dark.py --output rebuild/social-dark
python session/work/zhihe-film/render_film.py --output rebuild/film
python verify_archive.py
```

原动作校正脚本保留 session/work/pets 的相对布局；运行会重新写入中间产物，建议先复制项目至实验目录。笔记保存脚本仍保留原私人知识库绝对路径，仅作为历史记录，不要为重建视频而运行。

manifest.json 记录来源路径、归档相对路径、大小和 SHA-256；复制文件均与源文件逐一比对。verify_archive.py 只读校验归档内容，无需原 C: 工作目录。manifest 和校验报告自身不计入清单，以避免自引用。
