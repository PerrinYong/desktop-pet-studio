"""First-person process story. Existing pet pixels + native editorial typography.
Usage: python render_social.py --output output [--stills-only]
"""
from pathlib import Path
from functools import lru_cache
import argparse, bisect, io, json, math, subprocess, zipfile
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parent
W,H,FPS,DURATION=1080,1920,24,54
CREAM='#111b27';INK='#f1eee7';DARK='#080e16';WHITE='#f1eee7';AMBER='#c8a777';MUTED='#9ba8b5';LINE='#2e3c4b'
ATLAS=Image.open(ROOT/'assets/spritesheet.png').convert('RGBA')
RAW=Image.open(ROOT/'assets/jumping-source.png').convert('RGB')
BASE=Image.open(ROOT/'assets/base-source.png').convert('RGB')
BEFORE=Image.open(ROOT/'assets/wave-before.png').convert('RGBA')
AFTER=Image.open(ROOT/'assets/wave-after.png').convert('RGBA')
COUNTS=[6,8,8,4,5,8,6,6,6,8,8]
CELLS=[[ATLAS.crop((c*192,r*208,(c+1)*192,(r+1)*208)) for c in range(n)] for r,n in enumerate(COUNTS)]
TIMES=[[.28,.11,.11,.14,.14,.32],[.12]*7+[.22],[.12]*7+[.22],[.14]*3+[.28],[.14]*4+[.28],[.14]*7+[.24],[.15]*5+[.26],[.12]*5+[.22],[.15]*5+[.28]]
CUTS=[0,4,8,12,17,25,31,37,43,49,54]
TITLES=['25分钟，我让GPT做了一个会动的桌面宠物','我只提了一个要求','GPT给它取名叫知核','每个动作先生成连续姿态','五张静态图如何变成一次跳跃','动作生成后还要检查修正','十六个视线方向','七十三幅姿态组成完整图集','上传验证并启用','从一句话到动画成品']
SUBTITLES=[
 (0,4,'仅仅用25分钟，我让GPT帮我做了一个会动的桌面宠物。'),
 (4,8,'我让它按对我的了解，创建并选中一只宠物。'),
 (8,12,'GPT给我选了一只猫头鹰，取名叫「知核」。'),
 (12,17,'每个动作，它都先画出一组连续姿态。'),
 (17,21,'最酷的是这一步：把五张静态图排好。'),
 (21,25,'按顺序和每帧时长播放，它就跳起来了。'),
 (25,31,'我还看到它修正位置偏移，检查边缘和落地位置。'),
 (31,37,'它又做了十六个视线方向，头部能向四周转动。'),
 (37,43,'最后，九种动作和十六个视线姿态，被装进一张图。'),
 (43,49,'上传、验证、启用，它成了我在GPT工作界面里的小伙伴。'),
 (49,54,'从一句要求，到一个动画成品，我把这次过程剪给你看。')]

@lru_cache(None)
def font(n,bold=False,latin=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('bahnschrift.ttf' if latin else 'msyhbd.ttc' if bold else 'msyh.ttc'),n)

def text(im,x,y,s,n=42,color=WHITE,bold=False,latin=False,anchor=None):
    ImageDraw.Draw(im).text((x,y),s,font=font(n,bold,latin),fill=color,anchor=anchor)

def lines(im,x,y,seq,n=78,color=WHITE,bold=True,gap=22):
    for i,s in enumerate(seq):text(im,x,y+i*(n+gap),s,n,color,bold)

def card(im,box,fill,outline=None,r=26,width=2):
    ImageDraw.Draw(im).rounded_rectangle(box,r,fill=fill,outline=outline,width=width)

def line(im,xy,color=LINE,width=2):ImageDraw.Draw(im).line(xy,fill=color,width=width)
def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)

@lru_cache(None)
def bg(light=False):
    im=Image.new('RGB',(W,H),DARK)
    d=ImageDraw.Draw(im)
    # Sparse graph echoes the supplied profile background without copying its UI.
    nodes=[(38,876),(177,645),(345,785),(670,602),(902,741),(1028,1043),(733,1120),(916,1432),(596,1531),(235,1365),(41,1532)]
    edges=[(0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(9,10),(2,9),(2,6),(3,6),(6,8)]
    for a,b in edges:d.line((*nodes[a],*nodes[b]),fill='#172431',width=2)
    for i,(x,y) in enumerate(nodes):
        d.ellipse((x-5,y-5,x+5,y+5),fill='#45525c' if i%3 else '#75654d')
    return im

def idx(row,t):
    p=t%sum(TIMES[row]);acc=0
    for i,d in enumerate(TIMES[row]):
        acc+=d
        if p<acc:return i
    return len(TIMES[row])-1

@lru_cache(maxsize=600)
def sprite(r,c,h):return CELLS[r][c].resize((round(h*192/208),h),Image.Resampling.LANCZOS)

def pet(im,r,c,x,bottom,h):
    art=sprite(r,c,h);im.paste(art,(round(x-art.width/2),round(bottom-h)),art)

def art(im,source,box):
    x,y,w,h=box;scale=min(w/source.width,h/source.height)
    a=source.resize((round(source.width*scale),round(source.height*scale)),Image.Resampling.LANCZOS)
    pos=(round(x+(w-a.width)/2),round(y+(h-a.height)/2))
    im.paste(a,pos,a if a.mode=='RGBA' else None)

def label(im,x,y,s,light=False):
    n=29;w=ImageDraw.Draw(im).textlength(s,font=font(n))+38
    card(im,(x,y,x+w,y+52),'#182330',r=26)
    text(im,x+19,y+6,s,n,INK if light else AMBER)

def chrome(im,s,t,light=False):
    text(im,76,80,'石心SX / 我的 GPT 制作记录',28,INK if light else MUTED)
    text(im,966,86,f'{s+1:02d} / 10',26,INK if light else AMBER,latin=True,anchor='ra')
    line(im,(76,139,966,139),LINE)
    # Editorial footer remains above the deliberately empty lower margin.
    text(im,76,1760,'真实素材 · 制作过程可视化',24,MUTED)
    line(im,(76,1820,966,1820),LINE,3)
    line(im,(76,1820,76+890*t/DURATION,1820),AMBER,5)

def headline(im,tag,words,light=False):
    text(im,76,190,tag,30,AMBER)
    lines(im,70,256,words,76,INK if light else WHITE)

def caption(im,words,light=False):
    lines(im,76,1580,words,38,INK if light else WHITE,False,18)

def scene(s,t):
    u=t-CUTS[s];light=s in [0,2,8,9]
    im=bg(light).copy();d=ImageDraw.Draw(im)
    if s==0:
        text(im,76,187,'仅仅用',45,INK)
        text(im,65,228,'25',178,AMBER,True,True)
        text(im,320,317,'分钟',69,AMBER,True)
        line(im,(78,442,78,527),AMBER,5)
        text(im,99,449,'我让 GPT 帮我做了个',57,INK,True)
        text(im,70,558,'会动的桌面宠物',83,INK,True)
        pet(im,3,idx(3,u*.7),540,1405,900)
        # Real frames are evidence of the promised process, not a decorative stock image.
        for j in range(5):
            x=78+j*178
            card(im,(x,1436,x+163,1534),'#121e2a',LINE,r=10)
            pet(im,4,j,x+82,1530,103)
        caption(im,['从一句要求，','到一个会动的小伙伴。'],True)
    elif s==1:
        headline(im,'01 / 我提出要求',['我只提了','一个要求'])
        card(im,(76,570,966,1045),CREAM,r=30)
        text(im,119,613,'我的提示词 · 中文意译',29,'#73797b')
        lines(im,118,706,['按你对我的了解，','创建并选中','一只宠物。'],59,INK,True,20)
        label(im,79,1125,'角色、绘图、动画与检查')
        text(im,80,1224,'我把这些交给 GPT 继续完成。',43,WHITE)
        pet(im,7,idx(7,u),800,1510,340)
        caption(im,['我想看看，','它会给我做出什么。'])
    elif s==2:
        headline(im,'02 / 先确定主角',['GPT给它取名','叫「知核」'],True)
        card(im,(150,560,925,1320),'#111b27',LINE,r=24)
        pet(im,0,0,535,1270,745)
        art(im,BASE,(753,1130,125,138))
        text(im,540,1283,'角色参考 · 右下为原始生成图',27,MUTED,anchor='mm')
        label(im,78,1397,'沉稳的猫头鹰 · 灰白黏土质感',True)
        caption(im,['后面的每一组动作，','都会参考这张图保持一致。'],True)
    elif s==3:
        headline(im,'03 / 生成连续姿态',['然后，它开始','给角色画动作'])
        card(im,(77,575,966,990),'#111b27',LINE,r=24)
        art(im,RAW,(95,620,853,286))
        if u>.8:
            clean=source_cutout().resize((853,286),Image.Resampling.LANCZOS)
            width=round(853*ease((u-.8)/1.6))
            panel=Image.new('RGB',(853,286),'#152433');panel.paste(clean,(0,0),clean)
            im.paste(panel.crop((0,0,width,286)),(95,620))
            if width<853:line(im,(95+width,612,95+width,915),AMBER,3)
        text(im,116,937,'真实跳跃源图 / 5 个连续姿态',27,WHITE)
        actions=['蓄力','起跳','腾空','下降','落地']
        for j in range(5):
            x=78+j*178;card(im,(x,1100,x+162,1350),'#14212e',LINE,r=14)
            pet(im,4,j,x+81,1322,214)
            text(im,x+81,1395,actions[j],27,AMBER,anchor='mm')
        caption(im,['我能看见每一帧，','是怎么变化的。'])
    elif s==4:
        headline(im,'04 / 静态图连成动画',['最酷的，','就是这一步'])
        clock=.5*min(u,3)+max(0,u-3);active=idx(4,clock)
        for j in range(5):
            x=78+j*178
            card(im,(x,570,x+162,809),'#14212e',AMBER if j==active else LINE,r=15,width=4)
            pet(im,4,j,x+81,795,208)
            text(im,x+81,856,f'{j+1:02d}',29,AMBER if j==active else MUTED,latin=True,anchor='mm')
        total=sum(TIMES[4]);start=80;end=955
        line(im,(start,922,end,922),LINE,3)
        elapsed=0
        for dt in [0]+TIMES[4]:
            elapsed+=dt;x=start+(end-start)*elapsed/total
            line(im,(x,909,x,935),MUTED)
        pos=start+(end-start)*(clock%total)/total
        d.polygon([(pos-9,884),(pos+9,884),(pos,902)],fill=AMBER)
        line(im,(pos,904,pos,958),AMBER,3)
        card(im,(186,1010,856,1510),CREAM,LINE,r=30)
        pet(im,4,active,521,1500,440)
        text(im,520,1049,'慢放 → 循环播放',28,INK,anchor='mm')
        caption(im,['五张图，按顺序和时长播放。','它就真的跳起来了。'])
    elif s==5:
        headline(im,'05 / 检查和修正',['我还看到它','把动作做稳'])
        for j,(a,title) in enumerate([(BEFORE,'提取后'),(AFTER,'对齐后')]):
            x=78+j*456;card(im,(x,590,x+426,1150),'#111b27',LINE,r=24)
            art(im,a,(x+20,650,386,425))
            line(im,(x+213,642,x+213,1080),'#8f7959',2)
            text(im,x+213,1111,title,33,INK,True,anchor='mm')
        text(im,78,1200,'挥翅时的位置偏移，被修正了。',37,WHITE)
        for j,lab in enumerate(['清理透明边缘','对齐落地位置','核对视线方向']):
            x=80+j*298;card(im,(x,1350,x+275,1435),'#182330',r=14)
            text(im,x+137,1392,lab,30,AMBER,anchor='mm')
        caption(im,['出图之后，','还要检查动作是否连贯。'])
    elif s==6:
        headline(im,'06 / 十六向视线',['我还收到了','16个视线方向'])
        cx,cy,rad=520,1040,354;k=int(u/.24)%16
        for j in range(16):
            a=j*math.tau/16-math.pi/2;x=cx+rad*math.cos(a);y=cy+rad*math.sin(a)
            r=12 if j==k else 5;d.ellipse((x-r,y-r,x+r,y+r),fill=AMBER if j==k else '#626e77')
        pet(im,9+k//8,k%8,cx,1350,700)
        a=k*math.tau/16-math.pi/2;x=cx+rad*math.cos(a);y=cy+rad*math.sin(a)
        d.polygon([(x+17,y+8),(x+17,y+47),(x+30,y+35),(x+45,y+33)],fill=WHITE)
        label(im,78,1450,'抬头 · 低头 · 向左看 · 向右看')
        caption(im,['身体保持稳定，','头部自然地看向四周。'])
    elif s==7:
        headline(im,'07 / 打包成图集',['73幅姿态，','被装进一张图'])
        gx,gy,cw,ch=76,580,70,80
        valid=[(r,c) for r,n in enumerate(COUNTS) for c in range(n)]
        rr,cc=valid[int(u/.09)%73]
        for r in range(11):
            for c in range(8):
                x=gx+c*cw;y=gy+r*ch
                d.rectangle((x,y,x+cw-3,y+ch-3),fill='#334049' if c<COUNTS[r] else '#20292f',outline=AMBER if (r,c)==(rr,cc) else LINE,width=2)
                if c<COUNTS[r]:pet(im,r,c,x+cw/2,y+ch-4,76)
        text(im,704,633,'9',110,AMBER,latin=True);text(im,710,770,'种动作',37,WHITE)
        text(im,697,897,'16',110,AMBER,latin=True);text(im,710,1035,'个视线姿态',32,WHITE)
        label(im,700,1180,'共 73 帧')
        text(im,80,1505,'8 列 × 11 行 / 透明精灵图',27,MUTED)
        caption(im,['每个小格子，','都是它的一个姿态。'])
    elif s==8:
        headline(im,'08 / 创建完成',['上传、验证、启用','我的小伙伴来了'],True)
        pet(im,3,idx(3,u*.75),520,1270,850)
        card(im,(77,1327,966,1502),'#14212e',LINE,r=24)
        text(im,111,1361,'知核',48,INK,True)
        text(im,320,1368,'创建成功 · 已设为当前宠物',35,INK)
        text(im,112,1438,'本次创建结果 / GPT 工作界面 · Pets',25,MUTED)
        caption(im,['从画出来，到真的启用，','这次流程就跑通了。'],True)
    else:
        headline(im,'我把这次过程剪给你看',['从一句话，','到动画成品'],True)
        label(im,77,513,'25 分钟 · 我与 GPT 的一次创作',True)
        pet(im,3,idx(3,u*.65),530,1380,875)
        card(im,(76,1442,966,1513),'#182330',LINE,r=14)
        text(im,521,1476,'构思 → 出图 → 拆帧 → 校验 → 启用',32,INK,True,anchor='mm')
        caption(im,['你会想做一只','什么样的宠物？'],True)
    chrome(im,s,t,light)
    return im

def render(t):
    s=min(9,bisect.bisect_right(CUTS,t)-1);im=scene(s,t)
    # First frame is fully legible. Only later cuts use a short dissolve.
    if s>0 and t-CUTS[s]<.18:
        im=Image.blend(scene(s-1,CUTS[s]-.001),im,ease((t-CUTS[s])/.18))
    return im

def cover(version='A'):
    im=bg(False).crop((0,0,1080,1440));d=ImageDraw.Draw(im)
    text(im,76,71,'石心SX / 我的 GPT 制作记录',29,MUTED)
    if version=='A':
        text(im,65,139,'25',177,AMBER,True,True);text(im,321,225,'分钟',69,AMBER,True)
        line(im,(78,352,78,437),AMBER,5)
        text(im,100,361,'我让 GPT 帮我做了个',58,INK,True)
        lines(im,72,469,['会动的','桌面宠物'],90,INK,True,12)
    else:
        text(im,73,165,'25分钟',91,INK,True)
        text(im,79,345,'我让 GPT 帮我做了个',57,INK,True)
        lines(im,72,469,['会动的','桌面宠物'],90,AMBER,True,12)
    pet(im,3,1,658,1220,760)
    # A real five-frame filmstrip gives a concrete promise of a process story.
    for j in range(5):
        x=78+j*178;card(im,(x,1243,x+162,1370),'#111b27',LINE,r=10)
        pet(im,4,j,x+81,1365,132)
    text(im,79,1160,'真实制作过程',31,MUTED)
    return im

@lru_cache(None)
def source_cutout():
    im=RAW.convert('RGBA')
    im.putdata([(0,0,0,0) if (r-255)**2+g*g+(b-255)**2<96**2 else (r,g,b,a) for r,g,b,a in im.getdata()])
    return im

def srt_stamp(t):
    m=int(t//60);sec=int(t%60);ms=round((t-int(t))*1000)
    return f'00:{m:02d}:{sec:02d},{ms:03d}'

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default=str(ROOT/'output'));p.add_argument('--stills-only',action='store_true')
    a=p.parse_args();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
    qa=ROOT/'qa';qa.mkdir(exist_ok=True)
    samples=[0,5.8,10,14.3,20.5,27.5,33.5,39.7,45.7,51.3]
    board=Image.new('RGB',(1620,1310),'#10171c')
    for i,t in enumerate(samples):
        shot=render(t);shot.save(qa/f'shot-{i:02d}.png')
        board.paste(shot.resize((288,512),Image.Resampling.LANCZOS),(20+(i%5)*320,20+(i//5)*640))
        text(board,24+(i%5)*320,550+(i//5)*640,f'{t:04.1f}s / {i+1:02d}',25,WHITE,latin=True)
    board.save(out/'storyboard.jpg',quality=93)
    for v in ['A','B']:cover(v).save(out/f'cover-{v}-3x4.jpg',quality=96)
    contact=Image.new('RGB',(1000,780),'#18222b')
    for i,v in enumerate(['A','B']):
        c=cover(v);contact.paste(c.resize((300,400),Image.Resampling.LANCZOS),(50+i*480,50))
        contact.paste(c.resize((180,240),Image.Resampling.LANCZOS),(50+i*480,490))
        text(contact,50+i*480,12,f'{v} / 300px 与 180px 缩略图',23,INK)
    contact.save(out/'cover-small-size-check.jpg',quality=94)
    render(0).save(out/'opening-9x16.jpg',quality=96)
    (out/'narration.srt').write_text('\n\n'.join(f'{i+1}\n{srt_stamp(st)} --> {srt_stamp(en)}\n{s}' for i,(st,en,s) in enumerate(SUBTITLES))+'\n',encoding='utf-8')
    if a.stills_only:return
    ff=imageio_ffmpeg.get_ffmpeg_exe();video=out/'zhihe-25min-process.mp4'
    cmd=[ff,'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
         '-i',str(ROOT/'assets/soundtrack.wav'),'-t',str(DURATION),'-af','volume=4dB,afade=t=out:st=52.5:d=1.5',
         '-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',str(video)]
    with (qa/'encode.log').open('wb') as log:
        pr=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log)
        for n in range(FPS*DURATION):
            pr.stdin.write(render(n/FPS).tobytes())
            if n%(FPS*6)==0:print(f'rendered {n/FPS:.0f}/{DURATION}s',flush=True)
        pr.stdin.close()
        if pr.wait():raise RuntimeError('Encoding failed')
    subprocess.run([ff,'-y','-i',str(video),'-t','4','-vf','fps=8,scale=324:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse','-loop','0',str(out/'opening-preview.gif')],check=True,capture_output=True)
    meta={'title':'仅仅用25分钟，我让GPT帮我做了一个会动的桌面宠物','duration':DURATION,'size':[W,H],'fps':FPS,'mode':'First-person on-screen text with original synthesized soundtrack; no spoken narration.','visual_identity':'User supplied profile reference: deep ink blue-black, warm white, restrained muted gold, sparse network motif. Pet colors preserved.',
        'timing_claim':'25 minutes is the user-provided narrative framing; no independent stopwatch claim or fake time-lapse.',
        'production':'Actual character source, five-frame strip, before/after registration images, final atlas and saved activation result. Re-typeset process visualization, not a screen recording.',
        'scenes':[{'start':CUTS[i],'end':CUTS[i+1],'topic':TITLES[i]} for i in range(10)]}
    (out/'production.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print('DONE '+str(video),flush=True)

if __name__=='__main__':main()
