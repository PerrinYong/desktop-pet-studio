"""Assemble local WeChat submission folders from the approved album assets."""
import argparse
import csv
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 500_000
ALBUM_SUPPORT = {
    "cover-240.png": ((240, 240), "PNG", True),
    "icon-50.png": ((50, 50), "PNG", True),
    "banner-750x400.jpg": ((750, 400), "JPEG", False),
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_image(path, size, fmt, transparent=True):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f"{path}: larger than {MAX_BYTES} bytes")
    with Image.open(path) as im:
        if im.size != size or im.format != fmt:
            raise ValueError(f"{path}: expected {size} {fmt}, got {im.size} {im.format}")
        if fmt == "GIF" and (im.n_frames < 2 or im.info.get("loop") != 0):
            raise ValueError(f"{path}: expected an animated looping GIF")
        expected = (0, 255) if transparent else (255, 255)
        if im.convert("RGBA").getchannel("A").getextrema() != expected:
            raise ValueError(f"{path}: unexpected transparency")


def copy_image(source, dest, size, fmt, transparent=True):
    check_image(source, size, fmt, transparent)
    shutil.copy2(source, dest)


def write_text(path, text):
    path.write_text(text, encoding="utf-8")


def build_album(album, target):
    pack = read_json(album / "pack.json")
    config_path = album / "投稿.json"
    config = read_json(config_path) if config_path.is_file() else {}
    kind = pack.get("kind", pack.get("type"))
    stickers = pack["stickers"]
    if kind not in {"static", "animated"} or not 8 <= len(stickers) <= 24:
        raise ValueError(f"{album}: unsupported album type or count")
    animated = kind == "animated"
    main = target / "主图"
    thumbs = target / "缩略图"
    main.mkdir(parents=True)
    thumbs.mkdir()
    rows = []
    for index, sticker in enumerate(stickers, 1):
        caption = sticker["caption"]
        meaning = sticker.get("meaning") or config.get("meanings", {}).get(sticker["id"])
        if not meaning:
            raise ValueError(f"{album}: missing meaning for {sticker['id']}")
        name = f"{index:02d}-{caption}"
        thumb = thumbs / f"{name}.png"
        if animated:
            source = album / "animation" / "exports" / f"{caption}.gif"
            picture = main / f"{name}.gif"
            copy_image(source, picture, (240, 240), "GIF")
            with Image.open(source) as im:
                im.seek(im.n_frames // 2)
                im.convert("RGBA").resize((120, 120), Image.Resampling.LANCZOS).save(thumb, optimize=True)
            check_image(thumb, (120, 120), "PNG")
        else:
            original = f"{sticker['id']}-{caption}.png"
            picture = main / f"{name}.png"
            copy_image(album / "exports" / "wechat-240" / original, picture, (240, 240), "PNG")
            copy_image(album / "exports" / "thumbnails-120" / original, thumb, (120, 120), "PNG")
        rows.append([f"{index:02d}", caption, meaning, f"主图/{picture.name}", f"缩略图/{thumb.name}"])
    for filename, specs in ALBUM_SUPPORT.items():
        source = config.get("assets", {}).get(filename, f"assets/{filename}")
        copy_image(album / source, target / filename, *specs)
    fields = album / "assets" / "专辑资料.txt"
    if fields.is_file():
        shutil.copy2(fields, target / "专辑资料.txt")
    else:
        write_text(target / "专辑资料.txt",
                   f"名称：{config['name']}\n简介：{config['description']}\n"
                   f"类型：{'动态' if animated else '静态'}\n数量：{len(rows)}\n")
    with (target / "上传顺序.tsv").open("w", encoding="utf-8-sig", newline="") as handle:
        table = csv.writer(handle, delimiter="\t")
        table.writerow(["序号", "文案", "含义词", "主图", "缩略图"])
        table.writerows(rows)
    return len(rows)


def build_role(stickers, output):
    if output.exists():
        raise ValueError(f"{output}: already exists; choose a new --output-dir")
    albums = sorted(p for p in (stickers / "专辑").iterdir() if (p / "pack.json").is_file())
    if not albums:
        raise ValueError(f"{stickers}: no albums")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temp:
        staging = Path(temp) / "素材"
        account = staging / "账号资料"
        account.mkdir(parents=True)
        for filename, size in (("avatar-240.png", (240, 240)), ("icon-50.png", (50, 50))):
            copy_image(stickers / "账号资料" / filename, account / filename, size, "PNG")
        shutil.copy2(stickers / "账号资料" / "资料文案.txt", account / "资料文案.txt")
        counts = [(album.name, build_album(album, staging / album.name)) for album in albums]
        listing = "\n".join(f"- {name} · {count} 张" for name, count in counts)
        write_text(staging / "README.md",
                   "# 微信投稿素材\n\n账号字段在「账号资料」。每套表情的「上传顺序.tsv」对应主图、缩略图和含义词。\n"
                   "封面、横幅及面板图标与主图分放。提交前按实际后台核对规范和 AI 声明。\n\n"
                   f"{listing}\n")
        staging.rename(output)
    return len(counts), sum(count for _, count in counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("character", help="角色目录名")
    parser.add_argument("--output-dir", type=Path, help="指定一个尚不存在的输出目录")
    args = parser.parse_args()
    stickers = (ROOT / args.character / "表情包").resolve()
    if stickers.parent.parent != ROOT or not stickers.is_dir():
        parser.error(f"角色或表情包目录不存在：{args.character}")
    output = args.output_dir or stickers / "微信投稿" / "素材"
    try:
        albums, images = build_role(stickers, output.resolve())
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"{exc}\n")
    print(f"{args.character}: {albums} 张专辑 / {images} 张主图 / {output.resolve()}")


if __name__ == "__main__":
    main()
