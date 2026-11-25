"""Prepare revision metadata; artwork is generated with the built-in image tool."""
import json
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "docs/图文融合-其余专辑任务.json"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    jobs = read(TASKS)
    groups = {}
    for job in jobs:
        groups.setdefault((job["role"], job["album"]), []).append(job)
    for (role, name), items in groups.items():
        album = ROOT / role / "表情包/专辑" / name
        base = album / "revisions/图文融合-v2"
        (base / "references").mkdir(parents=True, exist_ok=True)
        config = read(album / "投稿.json") if (album / "投稿.json").exists() else {}
        snapshot = base / "references/投稿-初版.json"
        if not snapshot.exists():
            write(snapshot, config)
        else:
            config = read(snapshot)
        original = read(album / "pack.json")
        original_snapshot = base / "references/pack-初版.json"
        if not original_snapshot.exists():
            write(original_snapshot, original)
        original["kind"] = original.get("kind", original.get("type"))
        original["revision"] = "图文融合-v2"
        original["revision_date"] = "2026-11-26"
        original["source_character"] = role
        original["generation_tool"] = "built-in image_gen"
        original["reference"] = "references/character.png"
        by_id = {x["id"]: x for x in items}
        for sticker in original["stickers"]:
            job = by_id[sticker["id"]]
            sticker["meaning"] = job["meaning"]
            sticker["layout"] = job["layout"]
            if "prompt" in sticker:
                sticker["original_prompt"] = sticker["prompt"]
            sticker["prompt"] = job["prompt"]
            sticker["prompt_file"] = f'prompts/{job["id"]}.md'
            sticker["raw"] = f'raw/{job["id"]}' + ("-sheet.png" if job["kind"] == "animated" else ".png")
            sticker.pop("original_path", None)
        # Keep targeted repair selections when re-running metadata preparation.
        if (base / "pack.json").exists():
            prior = read(base / "pack.json")
            for sticker, previous in zip(original["stickers"], prior["stickers"]):
                for key in ("image", "sheet", "repair_prompt_file"):
                    if key in previous:
                        sticker[key] = previous[key]
        write(base / "pack.json", original)
        (base / "assets").mkdir(exist_ok=True)
        for filename in ("cover-240.png", "icon-50.png", "banner-750x400.jpg"):
            source = album / config.get("assets", {}).get(filename, f"assets/{filename}")
            dest = base / "assets" / filename
            if not dest.exists():
                shutil.copy2(source, dest)
        fields = album / "assets/专辑资料.txt"
        dest = base / "assets/专辑资料.txt"
        if not dest.exists():
            if fields.exists():
                shutil.copy2(fields, dest)
            else:
                dest.write_text(f'名称：{config["name"]}\n简介：{config["description"]}\n类型：静态\n数量：{len(items)}\n', encoding="utf-8")
        entries = [read(p) for p in sorted((base / "raw").glob("*.source.json"))]
        for entry in entries:
            entry["sha256"] = hashlib.sha256((base / entry["archived"]).read_bytes()).hexdigest()
        if entries:
            write(base / "provenance.json", entries)
        print(role, name, f"{len(entries)} source records (including repairs), {len(items)} stickers")


if __name__ == "__main__":
    main()

