"""Read-only alpha audit of generated originals; flags likely painted backgrounds."""
import json
from pathlib import Path
from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[1]
jobs = json.loads((ROOT / "docs/图文融合-其余专辑任务.json").read_text(encoding="utf-8"))
flags, count = [], 0
for job in jobs:
    base = ROOT / job["role"] / "表情包/专辑" / job["album"] / "revisions/图文融合-v2"
    raw = base / "raw" / (job["id"] + ("-sheet.png" if job["kind"] == "animated" else ".png"))
    if (base / "pack.json").exists():
        pack = json.loads((base / "pack.json").read_text(encoding="utf-8-sig"))
        item = next(x for x in pack["stickers"] if x["id"] == job["id"])
        selected = item.get("sheet" if job["kind"] == "animated" else "image")
        if selected:
            raw = base / selected
    if not raw.exists():
        continue
    count += 1
    with Image.open(raw) as im:
        alpha = im.convert("RGBA").getchannel("A")
        zero = alpha.histogram()[0] / (im.width * im.height)
        step = 2 if job["kind"] == "animated" else 1
        cw, ch = im.width // step, im.height // step
        corner_means = []
        for row in range(step):
            for col in range(step):
                for x, y in ((0, 0), (cw-12, 0), (0, ch-12), (cw-12, ch-12)):
                    patch = alpha.crop((col*cw+x, row*ch+y, col*cw+x+12, row*ch+y+12))
                    corner_means.append(ImageStat.Stat(patch).mean[0])
        if zero < .15 or max(corner_means) > 20:
            flags.append({"key": job["key"], "raw": str(raw), "alpha_zero_fraction": round(zero, 4),
                          "max_corner_mean": round(max(corner_means), 2)})
print(json.dumps({"available": count, "flagged": flags}, ensure_ascii=False, indent=2))

