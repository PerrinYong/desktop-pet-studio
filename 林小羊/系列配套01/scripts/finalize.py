from pathlib import Path
import json, hashlib, shutil, re, sys, zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SHEEP=ROOT.parent
def read(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def write(p,data): p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(ROOT/"plan.json")
def install():
    checks=[]
    for item in read(ROOT/"exports/export-manifest.json")["files"]:
        p=ROOT/"exports"/item["file"]
        with Image.open(p) as im:
            assert im.size==(item["width"],item["height"]),p
            assert p.stat().st_size<500000,p
            assert im.format==("JPEG" if p.suffix==".jpg" else "PNG"),p
            alpha=im.convert("RGBA").getchannel("A")
            bounds=alpha.getextrema()
            if p.suffix==".png":
                assert bounds==(0,255),(p,bounds)
                w,h=im.size
                for edge in [(0,0,w,1),(0,h-1,w,h),(0,0,1,h),(w-1,0,w,h)]:
                    assert alpha.crop(edge).getextrema()[1]==0,(p,"edge")
            else: assert bounds==(255,255),p
        checks.append(dict(item,alpha_extrema=list(bounds)))
    assert len(checks)==26
    for p in (ROOT/"exports/profile").glob("*.png"):
        target=SHEEP/"账号资料"/p.name
        assert not target.exists(),target
        shutil.copy2(p,target)
    albums=[]
    rows=[]
    for a in plan["albums"]:
        album=SHEEP/a["dir"]
        dest=album/"assets"
        assert not dest.exists(),dest
        shutil.copytree(ROOT/"exports"/a["id"],dest)
        text=f'名称：林小羊·{a["name"]}\n短名称：{a["name"]}\n简介：{a["desc"]}\n场景：{a["scene"]}\n类型：{a["kind"]}\n数量：{a["count"]}\n'
        (dest/"专辑资料.txt").write_text(text,encoding="utf-8")
        (ROOT/"exports"/a["id"]/"专辑资料.txt").write_text(text,encoding="utf-8")
        folder=album/("exports/wechat-240" if a["kind"]=="静态" else "animation/exports")
        extension="*.png" if a["kind"]=="静态" else "*.gif"
        files=sorted(folder.glob(extension))
        assert len(files)==a["count"],(a["name"],len(files))
        primary=[]
        for p in files:
            with Image.open(p) as im: assert im.size==(240,240),(p,im.size)
            primary.append(dict(file=p.relative_to(album).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
        manifest=dict(name="林小羊·"+a["name"],kind=a["kind"],scene=a["scene"],description=a["desc"],files=primary)
        if a["id"]=="04":
            manifest["supplement_not_in_album"]=[p.relative_to(album).as_posix() for p in sorted((album/"animation/exports").glob("*.gif"))]
        write(dest/"album-manifest.json",manifest)
        albums.append(dict(id=a["id"],name=a["name"],count=len(primary),kind=a["kind"],manifest=str((dest/"album-manifest.json").relative_to(SHEEP)).replace("\\","/")))
        rows.append(f'| {a["id"]} | [{a["name"]}](../{a["dir"]}/配套素材.md) | {a["scene"]} | {a["kind"]} | {len(primary)} | [清单](../{a["dir"]}/assets/album-manifest.json) |')
    (ROOT/"exports/profile/资料文案.txt").write_text((SHEEP/"账号资料/资料文案.txt").read_text(encoding="utf-8"),encoding="utf-8")
    md="# 林小羊专辑清单\n\n本次为 8 张已有场景专辑补齐资料；不移动、不重组原始表情。以下主清单中静态与动态不混用。\n\n| 编号 | 专辑 | 场景 | 类型 | 张数 | 主体文件 |\n| --- | --- | --- | --- | --- | --- |\n"+"\n".join(rows)+"\n\n共 32 张静态、40 张动态专辑主体。「羊毛失控」另有 2 张动图补充，不计入静态专辑；项目累计动图仍为 42 张。早期 8 张角色探索样张保留在探索目录。\n"
    (ROOT/"专辑清单.md").write_text(md,encoding="utf-8")
    validation=dict(ok=True,created="2026-11-25",support_assets=len(checks),album_count=len(albums),files=checks,albums=albums,wechat_client_tested=False,platform_submitted=False,spec_basis="用户此前提供的规格截图；未声称已复核当前平台规则")
    write(ROOT/"validation.json",validation)
    print(json.dumps(dict(ok=True,assets=len(checks),max_bytes=max(x["bytes"] for x in checks),albums=len(albums)),ensure_ascii=False))
def archive():
    assert read(ROOT/"validation.json")["ok"]
    assert read(ROOT/"visual-review.json")["ok"]
    prov=read(ROOT/"provenance.json")
    for r in prov["files"]:
        assert sha(Path(r["source"]))==sha(ROOT/r["archived"]),r["id"]
    # Check links only in new documents; skip external links and anchors.
    docs=[ROOT/"README.md",ROOT/"专辑清单.md",SHEEP/"账号资料/README.md"]+[SHEEP/a["dir"]/"配套素材.md" for a in plan["albums"]]
    for p in docs:
        for raw in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text(encoding="utf-8")):
            if re.match(r'^[a-z]+://',raw):continue
            target=raw.split("#")[0]
            if target and not target.endswith("archive-manifest.json"):
                assert (p.parent/target).exists(),(p,target)
    records=[dict(file=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(ROOT.rglob("*")) if p.is_file() and p.name!="archive-manifest.json"]
    write(ROOT/"archive-manifest.json",dict(created="2026-11-25",files=records))
    repo=SHEEP.parent
    link="\n[林小羊系列配套](林小羊/系列配套01/README.md)：形象头像、简介及 8 张场景专辑的封面、图标、横幅与可复制资料。\n"
    p=repo/"README.md"
    if "林小羊系列配套" not in p.read_text(encoding="utf-8-sig"):
        with p.open("a",encoding="utf-8") as f:f.write(link)
    p=SHEEP/"README.md"
    if "## 形象资料与专辑配套" not in p.read_text(encoding="utf-8-sig"):
        with p.open("a",encoding="utf-8") as f:f.write("\n## 形象资料与专辑配套\n\n[形象资料](账号资料/README.md) · [8 张专辑配套与总览](系列配套01/README.md) · [按场景选择专辑](系列配套01/专辑清单.md)。各专辑独立封面、图标、横幅、简介和主体清单均已整理。\n")
    out=Path(r"C:\Users\prin\Documents\Codex\2026-11-24\pets-plugin-work-pets-openai-curated\outputs\linxiaoyang-album-support")
    assert not out.exists(),out
    out.mkdir(parents=True)
    for name in ("exports","raw","prompts","references","preview","scripts"):
        shutil.copytree(ROOT/name,out/name)
    for name in ("plan.json","provenance.json","validation.json","visual-review.json","发布文案.txt"):
        shutil.copy2(ROOT/name,out/name)
    portable="# 林小羊配套素材\n\n含角色资料与 8 张专辑配套。此压缩包不重复收录已有的表情主体；主体在 desktop-pet-studio 工程各专辑中。\n\n[形象头像](exports/profile/avatar-240.png) · [形象图标](exports/profile/icon-50.png) · [全部文案](发布文案.txt)\n\n| 专辑 | 封面／头像 | 图标 | 横幅 | 名称与简介 |\n| --- | --- | --- | --- | --- |\n"
    for a in plan["albums"]:
        d="exports/"+a["id"]
        portable+=f'| {a["name"]} | [240 PNG]({d}/cover-240.png) | [50 PNG]({d}/icon-50.png) | [750×400 JPG]({d}/banner-750x400.jpg) | [资料]({d}/专辑资料.txt) |\n'
    portable+="\n原图、提示词、参考、导出脚本和本地验证均附于本包。规格按用户给出的截图制作，尚未经过微信客户端实发或平台审核。\n"
    (out/"README.md").write_text(portable,encoding="utf-8")
    files=[dict(file=p.relative_to(out).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(out.rglob("*")) if p.is_file()]
    write(out/"archive-manifest.json",dict(files=files))
    zip_path=out/"林小羊-形象与8张专辑配套.zip"
    with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(out.rglob("*")):
            if p.is_file() and p!=zip_path:z.write(p,p.relative_to(out).as_posix())
    with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None
    for r in files:assert sha(out/r["file"])==r["sha256"]
    print(json.dumps(dict(path=str(out),zip_bytes=zip_path.stat().st_size,files_verified=len(files),zip_crc_valid=True),ensure_ascii=False))
if __name__=="__main__":
    {"install":install,"archive":archive}[sys.argv[1]]()
