from pathlib import Path
import json, hashlib, re
from PIL import Image, ImageSequence, ImageChops
root=Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
meta=read(root/"pack.json")
records=[]
for s in meta["stickers"]:
    path=root/"animation/exports"/(s["caption"]+".gif")
    im=Image.open(path)
    assert im.format=="GIF" and im.size==(240,240) and im.info.get("loop")==0,path
    assert path.stat().st_size<500000,path
    hashes=set();durations=[];residue=[];caption_hashes=set()
    for i,frame in enumerate(ImageSequence.Iterator(im)):
        rgba=frame.convert("RGBA")
        durations.append(frame.info.get("duration",0))
        hashes.add(hashlib.sha256(rgba.tobytes()).hexdigest())
        a=rgba.getchannel("A")
        assert a.getextrema()==(0,255),(path,i)
        for box in [(0,0,240,1),(0,239,240,240),(0,0,1,240),(239,0,240,240)]:
            assert a.crop(box).getextrema()==(0,0),(path,i,"edge")
        expected=Image.open(root/"animation/frames"/s["id"]/("frame-%03d.png"%i)).getchannel("A").point(lambda v:255 if v>=128 else 0)
        extra=ImageChops.subtract(a,expected)
        count=sum(1 for v in extra.tobytes() if v)
        residue.append(count)
        caption_hashes.add(hashlib.sha256(rgba.crop((0,195,240,240)).tobytes()).hexdigest())
    assert len(durations)==len(s["sequence"]),(path,len(durations))
    assert sum(durations)==100*len(s["sequence"]),(path,durations)
    assert len(hashes)==4 and not any(residue),(path,len(hashes),residue)
    assert len(caption_hashes)==1,(path,"caption instability")
    records.append({"file":str(path.relative_to(root)).replace("\\","/"),"bytes":path.stat().st_size,"size":[240,240],"frames":len(durations),"distinct_frames":len(hashes),"duration_ms":sum(durations),"loop":"forever","unexpected_opaque_pixels":residue,"caption_stable":True,"sha256":sha(path)})
prov=read(root/"provenance.json")
for rec in prov["files"]:
    assert sha(root/rec["archived"])==rec["sha256"]
    if Path(rec["source"]).exists():
        assert sha(Path(rec["source"]))==rec["sha256"]
support=[]
for name,size,alpha_range in [("cover-240.png",(240,240),(0,255)),("icon-50.png",(50,50),(0,255)),("banner-750x400.jpg",(750,400),(255,255))]:
    path=root/"assets"/name
    with Image.open(path) as image:
        assert image.size==size and path.stat().st_size<500000,path
        assert image.convert("RGBA").getchannel("A").getextrema()==alpha_range,path
    support.append({"file":"assets/"+name,"sha256":sha(path)})
for s in meta["stickers"]:
    name=s["id"].split("-")[0]+"-"+s["caption"]+".png"
    transparent=root/"static/transparent-240"/name
    white=root/"static/white-240"/name
    with Image.open(transparent) as a, Image.open(white) as b:
        assert a.size==b.size==(240,240)
        assert a.convert("RGBA").getchannel("A").getextrema()==(0,255)
        assert b.convert("RGBA").getchannel("A").getextrema()==(255,255)
        expected=Image.alpha_composite(Image.new("RGBA",a.size,"white"),a.convert("RGBA")).convert("RGB")
        assert max(hi for lo,hi in ImageChops.difference(expected,b.convert("RGB")).getextrema())<=1
        empty=a.convert("RGBA").getchannel("A").point(lambda x:255 if x==0 else 0)
        diff=ImageChops.difference(b.convert("RGB"),Image.new("RGB",b.size,"white"))
        assert all(ImageChops.multiply(ch,empty).getbbox() is None for ch in diff.split())
    assert transparent.stat().st_size<500000 and white.stat().st_size<500000
for p in root.rglob("*.md"):
    for link in re.findall(r"\]\(([^)]+)\)",p.read_text(encoding="utf-8-sig")):
        if "://" not in link and not link.startswith("#"):
            target=p.parent/link.split("#")[0]
            assert target==root/"validation.json" or target.exists(),(p,link)
result={"ok":True,"created":"2026-11-25","originals_hash_verified":len(prov["files"]),"local_links_valid":True,"wechat_client_tested":False,"static_pairs_verified":len(meta["stickers"]),"support":support,"files":records}
(root/"validation.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"ok":True,"gifs":len(records),"max_bytes":max(r["bytes"] for r in records),"originals_verified":len(prov["files"])},ensure_ascii=False))

