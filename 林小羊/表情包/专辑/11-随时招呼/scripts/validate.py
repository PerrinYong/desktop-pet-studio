"""Validate the album exports without changing any images."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pack = json.loads((ROOT / "pack.json").read_text(encoding="utf-8-sig"))
    records = []
    for folder, size, transparent in (
        ("wechat-240", 240, True), ("chat-512", 512, True),
        ("white-240", 240, False), ("white-512", 512, False),
        ("thumbnails-120", 120, True),
    ):
        directory = ROOT / "exports" / folder
        assert len(list(directory.glob("*.png"))) == len(pack["stickers"])
        for sticker in pack["stickers"]:
            path = directory / f'{sticker["id"]}-{sticker["caption"]}.png'
            with Image.open(path) as image:
                assert image.format == "PNG" and image.size == (size, size), path
                rgba = image.convert("RGBA")
                alpha = rgba.getchannel("A")
                assert alpha.getextrema() == ((0, 255) if transparent else (255, 255)), path
                assert path.stat().st_size < 500_000, path
                if not transparent:
                    source_folder = "wechat-240" if size == 240 else "chat-512"
                    with Image.open(ROOT / "exports" / source_folder / path.name) as source:
                        src = source.convert("RGBA")
                        expected = Image.alpha_composite(Image.new("RGBA", src.size, "white"), src).convert("RGB")
                        difference = ImageChops.difference(expected, image.convert("RGB"))
                        assert max(hi for lo, hi in difference.getextrema()) <= 1, path
                        empty = src.getchannel("A").point(lambda a: 255 if a == 0 else 0)
                        diff_white = ImageChops.difference(image.convert("RGB"), Image.new("RGB", src.size, "white"))
                        assert all(ImageChops.multiply(channel, empty).getbbox() is None for channel in diff_white.split()), path
            records.append({"file": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    for name, size, alpha_range in (
        ("cover-240.png", (240, 240), (0, 255)),
        ("icon-50.png", (50, 50), (0, 255)),
        ("banner-750x400.jpg", (750, 400), (255, 255)),
    ):
        path = ROOT / "assets" / name
        with Image.open(path) as image:
            assert image.size == size and path.stat().st_size < 500_000
            assert image.convert("RGBA").getchannel("A").getextrema() == alpha_range
        records.append({"file": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    provenance = json.loads((ROOT / "provenance.json").read_text(encoding="utf-8-sig"))
    assert len(provenance["files"]) == 18
    for item in provenance["files"]:
        assert sha(ROOT / item["archived"]) == item["sha256"]
        assert (ROOT / item["prompt"]).is_file()
    result = {"status": "passed", "sticker_count": 16, "generated_original_count": 18,
              "checked_export_count": len(records), "max_export_bytes": max(r["bytes"] for r in records),
              "white_background": "opaque RGB, #FFFFFF wherever source alpha is zero; compositing error <= 1 per channel",
              "platform_uploaded": False, "files": records}
    (ROOT / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "files"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
