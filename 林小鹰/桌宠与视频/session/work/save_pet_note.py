from pathlib import Path
import json, re, subprocess

vault=Path('H:/0-Notes/my-notes-private')
workspace=Path(__file__).resolve().parent.parent
out=workspace/'outputs/zhihe-social-dark'
target=vault/'4-项目与事业档案/01-文章编写与分享/仅仅用25分钟，我让GPT帮我做了一个会动的桌面宠物.md'
note_id='gpt-animated-desktop-pet-in-25-minutes'
if target.exists():
    raise SystemExit('Target already exists; refusing to overwrite.')
for p in vault.rglob('*.md'):
    if any(x in p.parts for x in ['.git','.obsidian','tools']):continue
    if re.search(r'^note_id:\s*'+re.escape(note_id)+r'\s*$',p.read_text(encoding='utf-8-sig',errors='replace'),re.M):
        raise SystemExit('Note ID already exists.')

files=['cover-A-3x4.jpg','cover-B-3x4.jpg','zhihe-25min-process.mp4','cover-small-size-check.jpg','storyboard.jpg','narration.srt','source-project.zip','validation.json']
for f in files:
    if not (out/f).is_file():raise SystemExit('Missing media: '+f)
def uri(f):return (out/f).as_uri()
copy=(out/'发布文案.txt').read_text(encoding='utf-8')
body=copy.split('正文\n',1)[1].split('\n补充说明\n',1)[0].strip()
note=f'''---
note_id: {note_id}
type: project
status: draft
created: 2026-11-24
updated: 2026-11-24
platforms:
  - 小红书
tags:
  - AI创作
  - 桌面宠物
  - 内容创作
---

# 仅仅用25分钟，我让GPT帮我做了一个会动的桌面宠物

> 第一人称制作记录，拟用于小红书等社交媒体。当前保留发布文案、深色竖屏视频与两版封面，尚未发布。

归属：[[4-项目与事业档案/01-文章编写与分享/文章编写与分享项目地图|文章编写与分享]]。

## 发布文案

### 标题

仅仅用25分钟，我让GPT帮我做了一个会动的桌面宠物

### 正文

{body}

### 补充说明

本次使用 Pets 插件，宠物在 GPT 工作界面中启用。视频中的制作步骤由本次真实源图、序列帧与检查记录可视化复盘。

### 话题

#GPT #AI创作 #桌面宠物 #动画制作 #工具实践

## 视频

[播放或打开竖屏成片]({uri('zhihe-25min-process.mp4')})

- 时长：54 秒；画面：1080 × 1920、24 fps。
- 形式：第一人称屏幕文字、制作过程演示与原创合成配乐，无人声配音。
- 开头第一帧直接交代“25分钟、GPT、会动的桌面宠物”，随后进入构思、出图、拆帧、播放、校验与启用过程。
- 已完成视频完整解码、导出画面与音轨检查；[查看校验记录]({uri('validation.json')})。

## 封面

### A 版：突出“25分钟”（当前推荐）

![封面A：突出25分钟]({uri('cover-A-3x4.jpg')})

[打开封面 A 原图]({uri('cover-A-3x4.jpg')})

### B 版：突出“会动的桌面宠物”

![封面B：突出会动的桌面宠物]({uri('cover-B-3x4.jpg')})

[打开封面 B 原图]({uri('cover-B-3x4.jpg')})

两版均为 1080 × 1440，已做 180px 与 300px 小尺寸检查。[查看缩略图对照]({uri('cover-small-size-check.jpg')})。

## 创作思路与依据

- **主题与叙述**：保留完整标题，用“我提出要求，GPT完成宠物”的第一人称经历组织内容；重点展示序列帧如何变成动画。
- **账号视觉**：依据本次提供的主页截图，使用墨蓝黑底、暖白文字、少量哑金与稀疏节点连线；保留宠物自身的灰白和琥珀色。
- **信息层级**：应用 [[3-技术创业核心/02-能力-选品到营销/03-价值表达与营销/视频封面文字排版|视频封面文字排版]] 的关键词放大、分配阅读顺序与小尺寸检查方法。
- **真实内容与封面一致**：应用 [[3-技术创业核心/02-能力-选品到营销/03-价值表达与营销/视频封面设计|视频封面设计]] 的主体突出、真实结果作证据、封面与正片色板一致原则。
- **事实边界**：“25分钟”沿用作者提供的标题口径；制作画面是基于真实素材的可视化复盘。尚无发布后的点击率、观看留存或传播效果数据。

## 制作资料

- [分镜总览]({uri('storyboard.jpg')})
- [第一人称叙述字幕稿 SRT]({uri('narration.srt')})
- [可复现的制作脚本与素材]({uri('source-project.zip')})

## 媒体存放说明

本页引用当前电脑上的既有制作输出，媒体未复制进知识库，也未上传云端。封面和视频链接使用 `file:///` 本地文件 URI；换设备访问时，需要同步媒体或调整引用。

本地素材目录：`{out.as_posix()}`。
'''
target.write_text(note,encoding='utf-8')
(out/'内容归档.md').write_text(note,encoding='utf-8')
report={'document':str(target),'note_id':note_id,'media_count':len(files),'media_all_exist':True,'new_note':True}
(workspace/'work/pet-note-save.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
