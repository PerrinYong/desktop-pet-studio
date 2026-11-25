"""Build a current-use sticker library from selected album revisions and explicit keyframes."""
import argparse
import hashlib
import html
import json
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote

from PIL import Image, ImageChops
from build_wechat_upload import ROOT, album_source, check_image, read_json

FORMATS = {
    "透明-240": ("wechat-240", 240, True),
    "纯白-240": ("white-240", 240, False),
    "透明-512": ("chat-512", 512, True),
    "纯白-512": ("white-512", 512, False),
    "缩略图-120": ("thumbnails-120", 120, True),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(value, encoding="utf-8", newline="\n")


def write_json(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def copy(source, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)


def validate_library(output):
    manifest = read_json(output / "清单.json")
    stills = gifs = derived = 0
    for album in manifest["albums"]:
        base = output / album["album"]
        for item in album["stickers"]:
            source = ROOT / item["source"]
            if sha(source) != item["source_sha256"]:
                raise ValueError(f"Source changed: {source}")
            for directory, (_, size, transparent) in FORMATS.items():
                p = base / "静态" / directory / (item["name"] + ".png")
                if size <= 240:
                    check_image(p, (size, size), "PNG", transparent)
                with Image.open(p) as im:
                    if im.size != (size, size):
                        raise ValueError(f"Wrong dimensions: {p}")
                    a = im.convert("RGBA").getchannel("A")
                    expected = (0, 255) if transparent else (255, 255)
                    if a.getextrema() != expected:
                        raise ValueError(f"Wrong alpha: {p}")
                    if transparent:
                        for box in ((0,0,size,2),(0,size-2,size,size),(0,0,2,size),(size-2,0,size,size)):
                            if a.crop(box).getbbox() is not None:
                                raise ValueError(f"Clipped edge: {p}")
                if sha(p) != item["files"][directory]:
                    raise ValueError(f"Changed output: {p}")
            for size in (240, 512):
                with Image.open(base / f"静态/透明-{size}" / (item["name"] + ".png")) as a, Image.open(base / f"静态/纯白-{size}" / (item["name"] + ".png")) as b:
                    white = Image.alpha_composite(Image.new("RGBA", a.size, "white"), a.convert("RGBA"))
                    delta = ImageChops.difference(white.convert("RGB"), b.convert("RGB"))
                    if max(x[1] for x in delta.getextrema()) > 3:
                        raise ValueError(f"White/transparent pair mismatch: {item['name']}")
            if item.get("gif"):
                p = base / item["gif"]
                check_image(p, (240,240), "GIF")
                if sha(p) != sha(ROOT / item["gif_source"]):
                    raise ValueError(f"GIF changed: {p}")
                derived += 1
                gifs += 1
            stills += 1
    result = {"passed": True, "albums": len(manifest["albums"]), "static_stickers": stills,
              "animated_stickers": gifs, "selected_frames": derived,
              "checks": ["source SHA256", "GIF byte identity", "size and alpha", "clear edges",
                         "white/transparent consistency", "submission PNG/GIF below 500 KB"]}
    write_json(output / "验证.json", result)
    return result


def gallery(output, manifest):
    sections = []
    for album in manifest["albums"]:
        cards = []
        for item in album["stickers"]:
            prefix = album["album"]
            picture = quote(f'{prefix}/静态/透明-240/{item["name"]}.png')
            links = []
            for d in ("透明-240", "纯白-240", "透明-512", "纯白-512"):
                url = quote(f'{prefix}/静态/{d}/{item["name"]}.png')
                links.append(f'<a href="{url}" download>{d}</a>')
            if item.get("gif"):
                url = quote(f'{prefix}/{item["gif"]}')
                links.append(f'<a href="{url}" download>GIF 动图</a>')
                motion = f'<img class="motion" loading="lazy" src="{url}" alt="{html.escape(item["caption"])} 动图">'
            else:
                motion = ""
            cards.append(f'<article><div class="images"><img loading="lazy" src="{picture}" alt="{html.escape(item["caption"])}">{motion}</div><strong>{html.escape(item["caption"])}</strong><p>{" · ".join(links)}</p></article>')
        sections.append(f'<section><h2>{html.escape(album["album"])}</h2><div class="grid">{"".join(cards)}</div></section>')
    write(output / "浏览.html", """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>表情成品库</title><style>
body{font:16px/1.6 system-ui,sans-serif;background:#f3f0e9;color:#292725;margin:0;padding:32px}
main{max-width:1400px;margin:auto}h1{margin-bottom:8px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
article{border-radius:14px;background:white;padding:16px}.images{display:flex;justify-content:center;background:#e1ddd4;border-radius:10px;min-height:150px}
img{object-fit:contain;width:50%;max-width:220px;aspect-ratio:1}.images img:only-child{width:75%}
a{color:#35665e}p{font-size:13px;margin:8px 0}section{margin-top:32px}
</style><main><h1>""" + html.escape(manifest["character"]) + """ · 表情成品</h1>
<p>左侧静态精选，右侧原动图（如有）。点击格式直接打开或保存；所有素材均在本地。</p>
""" + "".join(sections) + "</main></html>")


def build(character, output):
    stickers = ROOT / character / "表情包"
    if output.exists():
        raise ValueError(f"{output} already exists; choose a new --output-dir")
    selection_path = stickers / "静帧选择.json"
    choices = read_json(selection_path)["albums"] if selection_path.exists() else {}
    manifest = {"character": character, "albums": []}
    plan = {"jobs": [], "previews": []}
    selected_preview = []
    used_choices = set()
    with TemporaryDirectory(dir=stickers) as temp:
        staging = Path(temp) / "成品"
        staging.mkdir()
        for album in sorted((stickers / "专辑").iterdir()):
            if not (album / "pack.json").exists():
                continue
            config = read_json(album / "投稿.json") if (album / "投稿.json").exists() else {}
            selected = album_source(album, config)
            target = staging / album.name
            for d in FORMATS:
                (target / "静态" / d).mkdir(parents=True)
            record = {"album": album.name, "source_dir": selected.relative_to(ROOT).as_posix(), "stickers": []}
            for subdir in ("", "附赠动图"):
                source = selected / subdir
                if not (source / "pack.json").exists():
                    continue
                pack = read_json(source / "pack.json")
                animated = pack.get("kind", pack.get("type")) == "animated"
                group = album.name + ("/" + subdir if subdir else "")
                if animated:
                    if set(choices.get(group, {})) != {s["id"] for s in pack["stickers"]}:
                        raise ValueError(f"Missing or extra frame selections: {group}")
                    used_choices.add(group)
                for index, item in enumerate(pack["stickers"], 1):
                    name = ("附赠-" if subdir else "") + f'{index:02d}-{item["caption"]}'
                    entry = {"id": item["id"], "name": name, "caption": item["caption"],
                             "meaning": item.get("meaning") or config.get("meanings", {}).get(item["id"]),
                             "bonus": bool(subdir), "kind": "animated" if animated else "static"}
                    if not entry["meaning"]:
                        raise ValueError(f"Missing meaning: {group}/{item['id']}")
                    if animated:
                        choice = choices[group][item["id"]]
                        k = choice["keyframe"]
                        if type(k) is not int or k not in range(4) or choice["caption"] != item["caption"]:
                            raise ValueError(f"Invalid frame selection: {group}/{item['id']}")
                        origin = source / "animation/frames" / item["id"] / f"source-{k}.png"
                        if sha(origin) != choice["source_sha256"]:
                            raise ValueError(f"Selected frame changed; review again: {origin}")
                        plan["jobs"].append({"source": str(origin), "target": str(target / "静态"), "name": name})
                        gif = source / "animation/exports" / (item["caption"] + ".gif")
                        copy(gif, target / "动态" / (name + ".gif"))
                        entry.update(keyframe=k, reason=choice["reason"], gif=f"动态/{name}.gif",
                                     gif_source=gif.relative_to(ROOT).as_posix())
                        selected_preview.append(str(target / "静态/透明-240" / (name + ".png")))
                    else:
                        origin = source / "exports/wechat-240" / f'{item["id"]}-{item["caption"]}.png'
                        for d, (old, _, _) in FORMATS.items():
                            copy(source / "exports" / old / origin.name, target / "静态" / d / (name + ".png"))
                    entry.update(source=origin.relative_to(ROOT).as_posix(), source_sha256=sha(origin))
                    record["stickers"].append(entry)
            if (selected / "assets").is_dir():
                for p in (selected / "assets").iterdir():
                    if p.is_file():
                        copy(p, target / "配套" / p.name)
            for dark, title in ((True, "总览-深底.png"), (False, "总览-白底.png")):
                plan["previews"].append({"paths": [str(target / "静态/透明-240" / (s["name"] + ".png")) for s in record["stickers"]],
                                         "target": str(target / title), "dark": dark})
            manifest["albums"].append(record)
        if used_choices != set(choices):
            raise ValueError(f"Unused frame selections: {set(choices)-used_choices}")
        if selected_preview:
            for dark, title in ((True, "动图静态精选-深底.png"), (False, "动图静态精选-白底.png")):
                plan["previews"].append({"paths": selected_preview, "target": str(staging / title), "dark": dark})
        plan_path = Path(temp) / "plan.json"
        write_json(plan_path, plan)
        subprocess.run(["pwsh", "-NoProfile", "-File", str(ROOT / "tools/export_still_frames.ps1"),
                        "-Plan", str(plan_path)], check=True)
        for album in manifest["albums"]:
            target = staging / album["album"]
            rows = []
            for s in album["stickers"]:
                s["files"] = {d: sha(target / "静态" / d / (s["name"] + ".png")) for d in FORMATS}
                rows.append(f'| {s["name"]} | {s["meaning"]} | {"静态＋动态" if s.get("gif") else "静态"} |')
            write(target / "README.md", f'# {album["album"]}\n\n'
                  '[透明静态 240](静态/透明-240/) · [纯白静态 240](静态/纯白-240/) · '
                  '[透明 512](静态/透明-512/) · [纯白 512](静态/纯白-512/) · [缩略图](静态/缩略图-120/)\n\n'
                  + ('[GIF 动图](动态/) · ' if any(s.get("gif") for s in album["stickers"]) else '')
                  + '[封面、横幅、简介](配套/) · [深底总览](总览-深底.png) · [白底总览](总览-白底.png)\n\n'
                  '文件编号和文案在各格式间一致；附赠版本带「附赠-」前缀。静态图取高清原帧，动图保持原文件。\n\n'
                  '| 文件名 | 含义词 | 格式 |\n| --- | --- | --- |\n' + "\n".join(rows) + "\n")
        for filename in ("avatar-240.png", "icon-50.png", "资料文案.txt"):
            copy(stickers / "账号资料" / filename, staging / "账号资料" / filename)
        write_json(staging / "清单.json", manifest)
        report = validate_library(staging)
        gallery(staging, manifest)
        listing = "\n".join(f'- [{a["album"]}]({a["album"]}/README.md)：{len(a["stickers"])} 张静态，'
                            f'{sum(bool(s.get("gif")) for s in a["stickers"])} 张动图。' for a in manifest["albums"])
        write(staging / "README.md", f'# {character} · 成品库\n\n'
              f'共 {report["static_stickers"]} 张静态表情、{report["animated_stickers"]} 张动图。'
              '每张静态均有透明和纯白 240/512，以及透明 120 缩略图。\n\n'
              '[打开本地浏览页](浏览.html) · [账号资料](账号资料/) · [素材清单与来源](清单.json) · [验证结果](验证.json)\n\n'
              + listing + '\n\n这里是当前使用素材；制作过程见 ../专辑，平台字段包见 ../微信投稿。'
              '由 tools/build_sticker_library.py 重建，不直接手改成品。\n')
        output.parent.mkdir(parents=True, exist_ok=True)
        staging.rename(output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("character")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    stickers = (ROOT / args.character / "表情包").resolve()
    if stickers.parent.parent != ROOT or not stickers.is_dir():
        parser.error("Unknown character")
    output = args.output_dir.resolve() if args.output_dir else stickers / "成品"
    try:
        result = validate_library(output) if args.validate_only else build(args.character, output)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

