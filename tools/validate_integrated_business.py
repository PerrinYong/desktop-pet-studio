"""Check revised outputs and provenance; does not edit image pixels."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops
from build_wechat_upload import check_image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "林小羊/表情包/专辑"
ALBUMS = ["10-今晚有安排", "11-随时招呼", "12-有事您招呼"]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def inspect_album(name, character="林小羊", revision="图文融合-v2", bonus=False):
    album = ROOT / character / "表情包/专辑" / name
    base = album / "revisions" / revision
    pack = read(base / "pack.json")
    old = read(album / "pack.json")
    config_path = base / "references/投稿-初版.json"
    config = read(config_path) if config_path.exists() else {}
    if bonus:
        timings = read(album / "animation/timing.json")["files"]
        meanings = {x["caption"]: x["meaning"] for x in old["stickers"]}
        old = {"stickers": [dict(x, meaning=meanings[x["caption"]]) for x in timings]}
    assert [(x["id"], x["caption"], x["meaning"]) for x in pack["stickers"]] == [
        (x["id"], x["caption"], x.get("meaning") or config.get("meanings", {}).get(x["id"])) for x in old["stickers"]
    ], "Captions or meanings changed"
    rows = []
    for item in pack["stickers"]:
        stem = f'{item["id"]}-{item["caption"]}.png'
        for directory, size, transparent in [
            ("chat-512", 512, True), ("wechat-240", 240, True),
            ("white-512", 512, False), ("white-240", 240, False),
            ("thumbnails-120", 120, True),
        ]:
            path = base / "exports" / directory / stem
            # 500 KB applies to submission files, not the 512px archive.
            if size <= 240:
                check_image(path, (size, size), "PNG", transparent)
            with Image.open(path) as im:
                assert im.size == (size, size)
                alpha = im.convert("RGBA").getchannel("A")
                assert alpha.getextrema() == ((0, 255) if transparent else (255, 255))
                edges = [alpha.crop(box).getextrema() for box in (
                    (0, 0, size, 2), (0, size-2, size, size),
                    (0, 0, 2, size), (size-2, 0, size, size))]
                assert all(a == ((0, 0) if transparent else (255, 255)) for a in edges)
        for size in (240, 512):
            transparent = base / "exports" / ("wechat-240" if size == 240 else "chat-512") / stem
            white = base / "exports" / f"white-{size}" / stem
            with Image.open(transparent) as a, Image.open(white) as b:
                # Compare independently rasterized white against alpha-composited output.
                expected = Image.alpha_composite(Image.new("RGBA", a.size, "white"), a.convert("RGBA"))
                delta = ImageChops.difference(expected.convert("RGB"), b.convert("RGB"))
                assert max(v[1] for v in delta.getextrema()) <= 3, (name, stem, "white mismatch")
        row = {"id": item["id"], "caption": item["caption"], "png240_bytes":
               (base / "exports/wechat-240" / stem).stat().st_size}
        if pack.get("kind") == "animated":
            gif = base / "animation/exports" / f'{item["caption"]}.gif'
            check_image(gif, (240, 240), "GIF")
            hashes, durations = set(), []
            with Image.open(gif) as im:
                assert im.n_frames == len(item["sequence"])
                assert im.info.get("loop") == 0
                for frame in range(im.n_frames):
                    im.seek(frame)
                    rgba = im.convert("RGBA")
                    hashes.add(hashlib.sha256(rgba.tobytes()).hexdigest())
                    durations.append(im.info["duration"])
                    expected_path = base / "animation/frames" / item["id"] / f"frame-{frame:03d}.png"
                    with Image.open(expected_path) as expected:
                        mask = expected.convert("RGBA").getchannel("A").point(lambda x: 255 if x >= 128 else 0)
                    assert ImageChops.difference(mask, rgba.getchannel("A")).getbbox() is None, (
                        item["id"], frame, "GIF residual/disposal mismatch")
                assert len(hashes) == 4
                assert sum(durations) == len(item["sequence"]) * 100
            row.update(gif_bytes=gif.stat().st_size, frames=len(item["sequence"]), distinct_poses=4, duration_ms=sum(durations), loop=0)
        rows.append(row)
    for entry in read(base / "provenance.json"):
        assert hashlib.sha256((base / entry["archived"]).read_bytes()).hexdigest() == entry["sha256"]
    if (base / "assets").exists():
        for file in (base / "assets").iterdir():
            if file.is_file():
                source = album / config.get("assets", {}).get(file.name, "assets/" + file.name)
                if source.exists():
                    assert file.read_bytes() == source.read_bytes()
    report = {"album": name, "revision": "图文融合-v2", "checks_passed": True,
              "checks": ["original caption/meaning identity", "dimensions", "submission file size",
                         "true alpha", "clear outer borders", "white composite", "raw SHA256",
                         "unchanged support assets", "GIF frame count/timing/loop/alpha disposal when applicable"],
              "visual_review": "另行查看 preview 深浅底总览及动图序列帧；此脚本不自动识别汉字或评价动作美感。",
              "stickers": rows}
    (base / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"album": name, "count": len(rows), "max_png240_bytes": max(x["png240_bytes"] for x in rows),
            "max_gif_bytes": max((x.get("gif_bytes", 0) for x in rows), default=0)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all-revisions", action="store_true")
    args = parser.parse_args()
    if args.all_revisions:
        for source in sorted(ROOT.glob("*/表情包/专辑/*/revisions/图文融合-v2/pack.json")):
            album = source.parents[2]
            print(json.dumps(inspect_album(album.name, album.parents[2].name), ensure_ascii=False))
            if (source.parent / "附赠动图/pack.json").exists():
                print(json.dumps(inspect_album(album.name, album.parents[2].name, "图文融合-v2/附赠动图", True), ensure_ascii=False))
    else:
        for album in ALBUMS:
            print(json.dumps(inspect_album(album), ensure_ascii=False))

