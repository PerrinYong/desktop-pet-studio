"""Archive the Zhihe session without modifying any original file."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from urllib.parse import unquote
from PIL import Image

SOURCE = Path(__file__).resolve().parent.parent
REPO = Path('E:/0-MyProj/desktop-pet-studio')
DEST = REPO / '知核'
PLUGIN = Path('C:/Users/prin/.codex/plugins/cache/openai-curated-remote/work-pets/0.1.6')
GENERATED = Path('C:/Users/prin/.codex/generated_images')
records = {}
excluded = []

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def write(rel, text):
    p = DEST / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8', newline='\n') as f:
        f.write(text)

def write_json(rel, data):
    write(rel, json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def copy(src, rel):
    p = DEST / rel
    if p.exists():
        raise FileExistsError(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, p)
    h = digest(src)
    if digest(p) != h:
        raise RuntimeError(f'Copy mismatch: {src}')
    records[p.relative_to(DEST).as_posix()] = {
        'source': str(src), 'sha256': h, 'bytes': p.stat().st_size,
        'kind': 'verbatim-copy', 'source_copy_verified': True,
    }

def tree(src, rel, omit=()):
    for f in sorted(src.rglob('*')):
        if not f.is_file():
            continue
        local = f.relative_to(src)
        if any(part in {'__pycache__', *omit} for part in local.parts) or f.suffix == '.pyc':
            continue
        copy(f, Path(rel) / local)

if DEST.exists():
    raise SystemExit(f'Refusing to overwrite existing archive: {DEST}')
DEST.mkdir()
tree(SOURCE / 'work', 'session/work', omit=('pet-env',))
tree(SOURCE / 'outputs', 'session/outputs')
tree(PLUGIN / 'skills/create-pet', 'tooling/work-pets-0.1.6/skills/create-pet')
tree(PLUGIN / 'references', 'tooling/work-pets-0.1.6/references')

# Only copy generated originals whose SHA-256 matches this pet's decoded source.
decoded = SOURCE / 'work/pets/zhihe/decoded'
source_hashes = {}
for f in decoded.glob('*.png'):
    source_hashes.setdefault(digest(f), []).append(f.name)
original_map = []
for f in sorted(GENERATED.rglob('*.png')):
    h = digest(f)
    if h in source_hashes:
        target = Path('raw/generated-images') / f.relative_to(GENERATED)
        copy(f, target)
        original_map.append({'original': target.as_posix(), 'decoded_names': source_hashes[h], 'sha256': h})
assert len(original_map) == 13, f'Expected 13 original generations, got {len(original_map)}'
write_json('raw/generated-image-map.json', original_map)
copy(Path('C:/Users/prin/AppData/Local/Temp/codex-clipboard-bc5dbd15-8a76-414e-b7f2-b0f7673e87ca.jpg'),
     'raw/private-references/小红书账号主页.jpg')
write('.gitignore', '# 本地保留的账号截图；不随常规 git add 提交。\nraw/private-references/\n__pycache__/\n*.pyc\n.venv/\nrebuild/\n')

# Export exact final atlas cells for direct reuse, including all 16 look directions.
copy(SOURCE / 'outputs/zhihe/spritesheet.png', 'assets/spritesheet.png')
atlas = Image.open(DEST / 'assets/spritesheet.png').convert('RGBA')
states = ['idle', 'running-right', 'running-left', 'waving', 'jumping', 'failed', 'waiting', 'running', 'review', 'look-000-to-157.5', 'look-180-to-337.5']
counts = [6, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8]
frames = []
for row, (state, count) in enumerate(zip(states, counts)):
    for col in range(count):
        rel = f'assets/frames/{state}/{col:02d}.png'
        p = DEST / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        box = (col * 192, row * 208, (col + 1) * 192, (row + 1) * 208)
        cell = atlas.crop(box)
        cell.save(p)
        assert Image.open(p).convert('RGBA').tobytes() == cell.tobytes()
        frame = {'state': state, 'row': row, 'column': col, 'path': rel, 'source_box': box}
        if row >= 9:
            frame['direction_degrees_clockwise_from_up'] = ((row - 9) * 8 + col) * 22.5
        frames.append(frame)
write_json('assets/frames-manifest.json', {'source': 'assets/spritesheet.png', 'pixel_exact': True, 'frame_count': len(frames), 'frames': frames})

note = (SOURCE / 'outputs/zhihe-social-dark/内容归档.md').read_text(encoding='utf-8-sig')
prefix = 'file:///' + SOURCE.as_posix() + '/outputs/zhihe-social-dark/'
note = note.replace(prefix, '../session/outputs/zhihe-social-dark/')
note = re.sub(r'归属：.*?。', '归档归属：desktop-pet-studio / 知核。原知识库版本保存在 session/outputs/zhihe-social-dark/内容归档.md。', note, count=1)
note = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'《\2》（原知识库路径：`\1`）', note)
note = note.split('## 媒体存放说明')[0] + '## 媒体存放说明\n\n本工程副本使用相对路径引用归档媒体，可随整个「知核」目录迁移。原笔记及其原始链接保持不变。\n'
write('docs/发布内容.md', note)
write('requirements.txt', 'Pillow==13.0.0\nimageio-ffmpeg==0.8.1\n')
write('docs/制作过程与版本.md', '''# 知核制作过程与版本

## 宠物生成

根据用户「按你对我的了解」的要求，角色定为沉稳好奇的灰白黏土猫头鹰「知核」。参考用户关注基本事实、认真思考与检查的沟通偏好。先生成统一角色原图，再生成独立动作条带，提取透明帧、统一行尺度与落地基线，组成最终图集。

- 9 种状态：idle、running-right、running-left、waving、jumping、failed、waiting、running（思考）、review。
- 左跑逐帧镜像右跑，保留时间顺序；原始右跑第一版与采用版均保留。
- 挥翅逐帧水平校正 [0, 6, 12, 0]，保留校正前图与记录。
- 4 个视线锚点作为生成参考，最终两行覆盖 16 个方向；保存连续性、方向语义、盲测与透明边缘处理记录。
- 最终图集 1536 × 2288，8 列 × 11 行，单元 192 × 208；73 个有效姿态。
- 当时已上传并选中；稳定 pet id 与校验记录在 session/work/pets/zhihe/pet-record.json。归档不重新操作线上宠物。

## 宣传内容版本

1. 横屏宣传片：56 秒，1920 × 1080；另有 21 秒制作幕后剪辑。完整脚本、源图、原创合成音乐、分镜与编码检查均保留。
2. 第一人称暖色初稿：按「仅仅用25分钟，我让GPT帮我做了一个会动的桌面宠物」组织；只生成封面、分镜、开场图及字幕，没有独立成片。
3. 第一人称深色最终版：54 秒，1080 × 1920，24 fps。按账号截图改为墨蓝黑、暖白、哑金和稀疏节点；开头直接交代时间、GPT 与结果，重点演示连续姿态、按时长播放和位置修正。含屏幕文字与合成配乐，无人声口播。

## 发布与事实边界

最终发布文案与封面、视频的可迁移引用见 [发布内容](发布内容.md)。标题中的「25分钟」沿用作者口径；没有独立计时证明。制作画面由真实素材可视化复盘，不是实时屏幕录制。宠物在 GPT 工作界面的 Pets 中启用。未在本次归档中发布内容或推送 GitHub。

封面设计使用用户指定知识库两篇文章的方法：关键词层级、突出主体、真实成果、小尺寸检查与封面/正片一致。原文仍在 H:/0-Notes/my-notes-private/3-技术创业核心/02-能力-选品到营销/03-价值表达与营销/，本工程只保留引用和应用说明，不复制整个私人知识库。

## 保留范围

session/work 完整保留原制作目录（排除虚拟环境与 Python 缓存），session/outputs 完整保留归档前的全部交付版本，包括 ZIP。raw/generated-images 中的 13 张原图以 SHA-256 与本次 decoded 原图逐一匹配，包含未采用的右跑第一版。保留冗余交付包以便追溯。

历史 JSON、脚本和笔记里的原路径保持原样，不篡改制作证据。路径映射：原工作目录的 work/ → session/work/；outputs/ → session/outputs/。新建发布文档使用相对引用。

不包含 Python 虚拟环境、下载缓存、系统字体/FFmpeg 二进制、其他会话文件或整个私人笔记库。不把对话记忆伪造成完整操作日志；现有提示词、任务计划、脚本、源图、检查记录和版本文件是本次归档的过程依据。
''')
write('tooling/PROVENANCE.md', f'''# 工具来源

work-pets 0.1.6 的 create-pet 技能、脚本和相关契约文档快照，原目录：`{PLUGIN.as_posix()}`。
保留原文件内容；仅作为本地复现依据，不改变第三方权利归属，也不声称该插件代码由本项目创作。原目录未提供顶层 LICENSE 文件。

本次自编脚本保存在 session/work/，视频项目是自包含目录。依赖见 ../requirements.txt；原环境为 Windows、Python 3.14、Pillow 13.0.0、imageio-ffmpeg 0.8.1。字体使用本机 Microsoft YaHei 与 Bahnschrift，不打包系统字体。图像生成还需相应生成工具；保存的提示词并不保证重新生成像素一致。
''')
write('README.md', '''# 知核 · 桌宠制作完整归档

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
''')
write('verify_archive.py', '''"""Read-only verification of all archived files; standard library only."""
from pathlib import Path
import hashlib, json, sys
root = Path(__file__).resolve().parent
data = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
errors = []
for entry in data['files']:
    path = root / entry['path']
    if not path.is_file():
        errors.append({'path': entry['path'], 'error': 'missing'})
        continue
    with path.open('rb') as f:
        h = hashlib.file_digest(f, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else hashlib.sha256(f.read()).hexdigest()
    if h != entry['sha256'] or path.stat().st_size != entry['bytes']:
        errors.append({'path': entry['path'], 'error': 'hash-or-size-mismatch'})
print(json.dumps({'ok': not errors, 'checked_files': len(data['files']), 'errors': errors}, ensure_ascii=False, indent=2))
sys.exit(bool(errors))
''')

# Verify every new relative Markdown media reference resolves inside the archive.
links_checked = 0
for rel in ['README.md', 'docs/发布内容.md', 'docs/制作过程与版本.md']:
    p = DEST / rel
    for href in re.findall(r'\]\(([^)]+)\)', p.read_text(encoding='utf-8')):
        if '://' in href or href.startswith('#'):
            continue
        target = p.parent / unquote(href)
        if href == 'archive-verification.json':
            continue
        assert target.exists(), (rel, href)
        links_checked += 1
all_records = []
for f in sorted(DEST.rglob('*')):
    if f.is_file():
        rel = f.relative_to(DEST).as_posix()
        record = records.get(rel, {'sha256': digest(f), 'bytes': f.stat().st_size, 'kind': 'archive-generated'})
        all_records.append({'path': rel, **record})
total = sum(r['bytes'] for r in all_records)
write_json('manifest.json', {
    'schema_version': 1, 'pet_name': '知核', 'created_utc': datetime.now(timezone.utc).isoformat(),
    'source_workspace': str(SOURCE), 'archive_root': str(DEST),
    'files': all_records, 'excluded': ['work/pet-env/', '**/__pycache__/', '**/*.pyc', 'unrelated generated-image sessions', 'system fonts and installed FFmpeg binary'],
    'manifest_excludes_itself_and_report': True,
})
report = {
    'ok': True, 'archive_root': str(DEST), 'repository': 'https://github.com/PerrinYong/desktop-pet-studio.git',
    'manifest_files': len(all_records), 'copied_files': len(records), 'bytes': total,
    'copied_files_sha256_verified': len(records), 'mismatches': [],
    'matched_generated_originals': len(original_map), 'final_frames_pixel_verified': len(frames),
    'relative_document_links_verified': links_checked,
    'extension_counts': dict(Counter(Path(r['path']).suffix.lower() for r in all_records)),
    'source_files_preserved': True, 'git_commit_or_push_performed': False,
}
write_json('archive-verification.json', report)
print(json.dumps(report, ensure_ascii=False, indent=2))
