"""Assemble local WeChat submission folders from the approved album assets."""
import argparse
import csv
import json
import hashlib
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


def album_source(album, config):
    if config.get("source_dir"):
        selected = (album / config["source_dir"]).resolve()
        if not selected.is_relative_to(album.resolve()):
            raise ValueError(f"{album}: source_dir must stay inside the album")
        return selected
    return album


def build_album(album, target, library, record):
    album_name = album.name
    config_path = album / "投稿.json"
    config = read_json(config_path) if config_path.is_file() else {}
    album = album_source(album, config)
    pack = read_json(album / "pack.json")
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
    catalog = {s["id"]: s for s in record["stickers"] if not s["bonus"]}
    if set(catalog) != {s["id"] for s in stickers}:
        raise ValueError(f"{album}: library does not match selected album; rebuild 成品")
    if animated:
        for directory in ("主图", "白底主图", "缩略图"):
            (target / "静态备选" / directory).mkdir(parents=True)
    static_rows = []
    for index, sticker in enumerate(stickers, 1):
        caption = sticker["caption"]
        meaning = sticker.get("meaning") or config.get("meanings", {}).get(sticker["id"])
        if not meaning:
            raise ValueError(f"{album}: missing meaning for {sticker['id']}")
        name = f"{index:02d}-{caption}"
        thumb = thumbs / f"{name}.png"
        selected_still = catalog[sticker["id"]]
        if (selected_still["caption"], selected_still["meaning"]) != (caption, meaning):
            raise ValueError(f"{album}: stale library meaning/caption")
        still_base = library / album_name / "静态"
        still_name = selected_still["name"] + ".png"
        if animated:
            source = album / "animation" / "exports" / f"{caption}.gif"
            picture = main / f"{name}.gif"
            copy_image(source, picture, (240, 240), "GIF")
            copy_image(still_base / "缩略图-120" / still_name, thumb, (120, 120), "PNG")
            for directory, source_dir in (("主图", "透明-240"), ("白底主图", "纯白-240"), ("缩略图", "缩略图-120")):
                size = (120, 120) if directory == "缩略图" else (240, 240)
                copy_image(still_base / source_dir / still_name,
                           target / "静态备选" / directory / f"{name}.png", size, "PNG", directory != "白底主图")
            static_rows.append([f"{index:02d}", caption, meaning, f"主图/{name}.png", f"缩略图/{name}.png"])
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
    if static_rows:
        with (target / "静态备选/上传顺序.tsv").open("w", encoding="utf-8-sig", newline="") as handle:
            table = csv.writer(handle, delimiter="\t")
            table.writerow(["序号", "文案", "含义词", "主图", "缩略图"])
            table.writerows(static_rows)
        write_text(target / "静态备选/README.md", "# 动图对应的静态备选\n\n主图为透明 PNG；白底主图为纯白 PNG。缩略图与所选静帧一致，原文案和含义词不变。\n\n同一专辑按静态或动态选择一种类型；本目录不混入上一级 GIF 主图。配套资料见上一级。\n")
    return len(rows)


def build_role(stickers, output, library=None):
    if output.exists():
        raise ValueError(f"{output}: already exists; choose a new --output-dir")
    albums = sorted(p for p in (stickers / "专辑").iterdir() if (p / "pack.json").is_file())
    if not albums:
        raise ValueError(f"{stickers}: no albums")
    library = library or stickers / "成品"
    catalog = read_json(library / "清单.json")
    by_album = {a["album"]: a for a in catalog["albums"]}
    if set(by_album) != {a.name for a in albums}:
        raise ValueError("Library album list changed; rebuild 成品 first")
    for album in catalog["albums"]:
        config_path = stickers / "专辑" / album["album"] / "投稿.json"
        config = read_json(config_path) if config_path.exists() else {}
        selected = album_source(config_path.parent, config)
        if selected != (ROOT / album["source_dir"]).resolve():
            raise ValueError("Selected revision changed; rebuild 成品 first")
        for item in album["stickers"]:
            source = ROOT / item["source"]
            if hashlib.sha256(source.read_bytes()).hexdigest() != item["source_sha256"]:
                raise ValueError(f"Stale source: {source}; rebuild 成品 first")
            for directory in ("透明-240", "纯白-240", "缩略图-120"):
                p = library / album["album"] / "静态" / directory / (item["name"] + ".png")
                if hashlib.sha256(p.read_bytes()).hexdigest() != item["files"][directory]:
                    raise ValueError(f"Modified library file: {p}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temp:
        staging = Path(temp) / "素材"
        account = staging / "账号资料"
        account.mkdir(parents=True)
        for filename, size in (("avatar-240.png", (240, 240)), ("icon-50.png", (50, 50))):
            copy_image(stickers / "账号资料" / filename, account / filename, size, "PNG")
        shutil.copy2(stickers / "账号资料" / "资料文案.txt", account / "资料文案.txt")
        counts = [(album.name, build_album(album, staging / album.name, library, by_album[album.name])) for album in albums]
        for album in albums:
            config_path = album / "投稿.json"
            config = read_json(config_path) if config_path.exists() else {}
            extras = album_source(album, config) / "附赠动图/animation/exports"
            if extras.is_dir():
                extra_target = staging / "附赠聊天动图" / album.name
                extra_target.mkdir(parents=True)
                for item in by_album[album.name]["stickers"]:
                    if not item["bonus"]:
                        continue
                    copy_image(library / album.name / item["gif"], extra_target / (item["name"] + ".gif"), (240, 240), "GIF")
                    for directory, transparent in (("透明-240", True), ("纯白-240", False)):
                        dest = extra_target / directory
                        dest.mkdir(exist_ok=True)
                        copy_image(library / album.name / "静态" / directory / (item["name"] + ".png"),
                                   dest / (item["name"] + ".png"), (240, 240), "PNG", transparent)
                write_text(extra_target / "README.md", "附赠 GIF 及其透明、纯白静态版供直接聊天使用，不混入静态专辑的投稿主图。\n")
        listing = "\n".join(f"- {name} · {count} 张" for name, count in counts)
        write_text(staging / "README.md",
                   "# 微信投稿素材\n\n账号字段在「账号资料」。每套表情的「上传顺序.tsv」对应主图、缩略图和含义词。\n"
                   "封面、横幅及面板图标与主图分放。动态专辑下的「静态备选」提供对应 PNG、白底 PNG、缩略图和含义词，按一种类型选择使用。\n\n"
                   f"{listing}\n")
        staging.rename(output)
    return len(counts), sum(count for _, count in counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("character", help="角色目录名")
    parser.add_argument("--output-dir", type=Path, help="指定一个尚不存在的输出目录")
    parser.add_argument("--library-dir", type=Path, help="成品库目录，默认 角色/表情包/成品")
    args = parser.parse_args()
    stickers = (ROOT / args.character / "表情包").resolve()
    if stickers.parent.parent != ROOT or not stickers.is_dir():
        parser.error(f"角色或表情包目录不存在：{args.character}")
    output = args.output_dir or stickers / "微信投稿" / "当前"
    try:
        albums, images = build_role(stickers, output.resolve(), args.library_dir.resolve() if args.library_dir else None)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"{exc}\n")
    print(f"{args.character}: {albums} 张专辑 / {images} 张主图 / {output.resolve()}")


if __name__ == "__main__":
    main()
