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
    assert sha(Path(rec["source"]))==sha(root/rec["archived"])
for p in root.rglob("*.md"):
    for link in re.findall(r"\]\(([^)]+)\)",p.read_text(encoding="utf-8-sig")):
        if "://" not in link and not link.startswith("#"):
            target=p.parent/link.split("#")[0]
            assert target==root/"validation.json" or target.exists(),(p,link)
result={"ok":True,"created":"2026-11-25","originals_hash_verified":len(prov["files"]),"local_links_valid":True,"wechat_client_tested":False,"files":records}
(root/"validation.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"ok":True,"gifs":len(records),"max_bytes":max(r["bytes"] for r in records),"originals_verified":len(prov["files"])},ensure_ascii=False))

