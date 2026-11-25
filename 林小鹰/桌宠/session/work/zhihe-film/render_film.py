"""ZHIHE — a reproducible sprite-film. Reuses real artwork; draws only editorial graphics.
Run: python render_film.py --output ../../outputs/zhihe-film
Requires Pillow and imageio-ffmpeg. Default: 1920x1080 / 24 fps / 56 seconds.
"""
from pathlib import Path
from functools import lru_cache
import argparse, array, bisect, hashlib, json, math, random, subprocess, wave
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent
W, H, FPS, LENGTH = 1920, 1080, 24, 56
CREAM, INK, AMBER, MUTED = '#f3eee4', '#272a2b', '#dd9d35', '#777b7b'
DARK, WHITE, LINE = '#181d21', '#f4f0e8', '#d9d3c9'
CN = Path('C:/Windows/Fonts/msyh.ttc')
BOLD = Path('C:/Windows/Fonts/msyhbd.ttc')
LATIN = Path('C:/Windows/Fonts/bahnschrift.ttf')
COUNTS = [6, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8]
NAMES = ['idle','running-right','running-left','waving','jumping','failed','waiting','running','review']
DURATIONS = [[.28,.11,.11,.14,.14,.32], [.12]*7+[.22], [.12]*7+[.22], [.14]*3+[.28], [.14]*4+[.28], [.14]*7+[.24], [.15]*5+[.26], [.12]*5+[.22], [.15]*5+[.28]]
ATLAS = Image.open(ROOT/'assets/spritesheet.png').convert('RGBA')
SOURCE = Image.open(ROOT/'assets/jumping-source.png').convert('RGB')
CELLS = [[ATLAS.crop((c*192,r*208,(c+1)*192,(r+1)*208)) for c in range(n)] for r,n in enumerate(COUNTS)]
CUTS = [0,5,9.5,14,18,22,28,34,41,49,56]
SCENES = [
    ('HELLO, ZHIHE','知核，认真陪你'), ('FOCUS','专注思考'),
    ('REVIEW','认真检查'), ('WAIT','耐心等你'), ('CELEBRATE','为每一步进展雀跃'),
    ('LOOK AROUND','目光，跟随你的方向'), ('BEHIND THE FRAMES','从一排姿态开始'),
    ('FRAME BY FRAME','五幅画，开始跳跃'), ('ASSEMBLY','把动作装进一张图'), ('ZHIHE','认真做事，也认真陪你')]

@lru_cache(None)
def font(size, bold=False, latin=False):
    return ImageFont.truetype(str(LATIN if latin else BOLD if bold else CN), size)

def txt(im, xy, value, size=36, fill=INK, bold=False, latin=False, anchor=None):
    ImageDraw.Draw(im).text(xy, value, font=font(size,bold,latin), fill=fill, anchor=anchor)

def ease(x):
    x=max(0,min(1,x)); return x*x*(3-2*x)

@lru_cache(None)
def background(dark=False):
    im=Image.new('RGB',(W,H),DARK if dark else CREAM)
    d=ImageDraw.Draw(im)
    if dark:
        for x in range(0,W,60): d.line((x,0,x,H),fill='#21282e')
        for y in range(0,H,60): d.line((0,y,W,y),fill='#21282e')
    else:
        d.ellipse((1080,-260,2140,800),fill='#eae2d4')
        d.ellipse((1430,-190,2170,540),fill='#eee7db')
    return im

def index(row,t,speed=1):
    ds=DURATIONS[row]; p=(t*speed)%sum(ds)
    total=0
    for i,dt in enumerate(ds):
        total+=dt
        if p<total:return i
    return len(ds)-1

@lru_cache(maxsize=500)
def scaled(row,col,height):
    return CELLS[row][col].resize((round(height*192/208),height),Image.Resampling.LANCZOS)

def pet(im,row,col,cx,bottom,height=610):
    art=scaled(row,col,height)
    im.paste(art,(round(cx-art.width/2),round(bottom-height)),art)

def card(im,box,fill,outline=None,radius=28,width=2):
    ImageDraw.Draw(im).rounded_rectangle(box,radius=radius,fill=fill,outline=outline,width=width)

def line(im,xy,fill=LINE,width=2):ImageDraw.Draw(im).line(xy,fill=fill,width=width)

def chrome(im,number,t,dark=False):
    color=WHITE if dark else INK
    txt(im,(92,55),'知核',29,color,True)
    txt(im,(178,60),'ZHIHE  /  WORK COMPANION',21,AMBER if dark else MUTED,latin=True)
    txt(im,(1828,62),f'{number+1:02d} / 10',22,AMBER,latin=True,anchor='ra')
    line(im,(92,101,1828,101),'#364047' if dark else LINE)
    txt(im,(92,1019),'从基本事实出发，让每一步都有回应。' if not dark else 'MAKING OF  /  基于真实源图与序列帧的过程可视化',21,MUTED)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((1445,1022,1828,1026),2,fill='#374047' if dark else '#ddd5c9')
    d.rounded_rectangle((1445,1022,1446+382*min(t/LENGTH,1),1026),2,fill=AMBER)

def heading(im,kicker,title,sub,local,dark=False):
    fg=WHITE if dark else INK
    shift=round((1-ease(local/.65))*24)
    txt(im,(105,167+shift),kicker,24,AMBER,latin=True)
    txt(im,(100,216+shift),title,67,fg,True)
    if sub:txt(im,(105,318+shift),sub,30,MUTED)

def pill(im,x,y,label,dark=False):
    width=ImageDraw.Draw(im).textlength(label,font=font(25))+42
    card(im,(x,y,x+width,y+50),'#30373b' if dark else '#e8dfd0',radius=25)
    txt(im,(x+21,y+8),label,25,WHITE if dark else INK)

def draw_check(im,x,y,progress,color=AMBER):
    pts=[(x,y+12),(x+12,y+24),(x+37,y-6)]
    p=min(1,max(0,progress))
    if p<.35:
        end=(x+12*p/.35,y+12+12*p/.35);line(im,(x,y+12,*end),color,5)
    else:
        line(im,(*pts[0],*pts[1]),color,5)
        a=(p-.35)/.65;line(im,(*pts[1],x+12+25*a,y+24-30*a),color,5)

def scene(s,t):
    local=t-CUTS[s]; dark=6<=s<=8
    im=background(dark).copy();d=ImageDraw.Draw(im)
    if s==0:
        txt(im,(105,205),'MEET YOUR QUIET COMPANION',25,AMBER,latin=True)
        txt(im,(94,275),'知核',176,INK,True)
        txt(im,(108,490),'小小身影，认真回应。',44,INK)
        txt(im,(108,570),'沉稳  ·  好奇  ·  有据可循',30,MUTED)
        pill(im,110,670,'你的工作小伙伴')
        cx=1370+(1-ease(local/1.1))*180
        pet(im,3,index(3,local*.65),cx,920,850)
        txt(im,(1370,944),'Z H I H E',28,AMBER,latin=True,anchor='mm')
    elif s in (1,2,3):
        titles={1:('FOCUS / 01','专注思考','把“正在努力”，变成看得见的状态。',7),2:('REVIEW / 02','认真检查','多看一眼，为完成留出检查的时间。',8),3:('WAIT / 03','耐心等你','需要你的指令时，安静地抬头等候。',6)}
        kick,title,sub,row=titles[s];heading(im,kick,title,sub,local)
        card(im,(105,429,833,865),'#faf7f0',LINE)
        if s==1:
            txt(im,(149,474),'思考进行中',32,INK,True)
            labels=['理解问题','整理线索','寻找路径']
            for j,lab in enumerate(labels):
                y=561+j*84
                d.ellipse((152,y,169,y+17),fill=AMBER if local>j*.7 else LINE)
                txt(im,(192,y-9),lab,29,MUTED)
                p=ease((local-j*.7)/2)
                card(im,(390,y+3,746,y+13),'#e6dfd3',radius=5)
                if p>0:card(im,(390,y+3,391+355*p,y+13),AMBER,radius=5)
        elif s==2:
            txt(im,(149,474),'认真，是一种习惯',32,INK,True)
            for j,lab in enumerate(['看清楚','想明白','再确认']):
                y=558+j*83;txt(im,(210,y-5),lab,29,INK)
                draw_check(im,153,y,ease((local-j*.75-.35)/.4))
                line(im,(208,y+48,765,y+48),LINE)
        else:
            txt(im,(149,474),'下一步，听你的。',36,INK,True)
            txt(im,(149,558),'准备好时，再一起继续。',30,MUTED)
            for j in range(3):
                pulse=(math.sin(local*3-j*.8)+1)/2
                d.ellipse((150+j*47,670-7*pulse,170+j*47,690-7*pulse),fill=AMBER)
            pill(im,150,751,'等待输入')
        pet(im,row,index(row,local),1335,930,765)
        txt(im,(1335,944),['','专注','检查','等待'][s],29,MUTED,anchor='mm')
    elif s==4:
        heading(im,'MOMENTUM / 04','为每一步进展雀跃','出发，遇到问题，再试一次，然后轻轻庆祝。',local)
        line(im,(110,880,1810,880),'#cfc5b4',3)
        if local<1.5:
            cx=230+ease(local/1.5)*800;row=1;ix=index(1,local)
        elif local<2.4:
            cx=1030;row=5;ix=index(5,(local-1.5)*1.1)
        else:
            cx=1030;row=4;ix=index(4,local-2.4)
        pet(im,row,ix,cx,895,630)
        if local>2.5:
            p=ease((local-2.5)/.5);draw_check(im,1460,615,p)
            txt(im,(1518,605),'完成一步',38,INK,True)
        txt(im,(112,926),'让进展有表情，让完成有仪式感。',30,MUTED)
    elif s==5:
        heading(im,'RESPONSIVE / 16 DIRECTIONS','目光，跟随你的方向','九种动作，十六个视线方向。',local)
        cx,cy=1005,630;rad=285
        phase=int(local/.19)%16;angle=phase*math.tau/16-math.pi/2
        for i in range(16):
            a=i*math.tau/16-math.pi/2;x=cx+rad*math.cos(a);y=cy+rad*math.sin(a)
            r=10 if i==phase else 4
            d.ellipse((x-r,y-r,x+r,y+r),fill=AMBER if i==phase else '#cfc5b4')
        pet(im,9+phase//8,phase%8,cx,865,625)
        px=cx+rad*math.cos(angle);py=cy+rad*math.sin(angle)
        d.polygon([(px+14,py+9),(px+14,py+45),(px+26,py+35),(px+40,py+34)],fill=INK)
        txt(im,(1465,505),'16',112,AMBER,latin=True)
        txt(im,(1470,638),'个方向',33,INK)
        txt(im,(140,536),'看向你，',42,INK,True);txt(im,(140,598),'回应你。',42,INK,True)
    elif s==6:
        heading(im,'MAKING OF / 01','从一排姿态开始','真实跳跃源图：蓄力 → 起跳 → 腾空 → 下降 → 落地',local,True)
        raw=SOURCE.resize((1698,566),Image.Resampling.LANCZOS)
        im.paste(raw,(111,394))
        p=ease((local-1)/3.4);wipe=round(1698*p)
        if wipe:
            clean=Image.new('RGB',(1698,566),'#263038');cd=ImageDraw.Draw(clean)
            for x in range(0,1698,28):
                for y in range(0,566,28):
                    if (x//28+y//28)%2==0:cd.rectangle((x,y,x+27,y+27),fill='#303b43')
            # Deterministic chroma removal from original pixels; no redraw.
            clean.paste(source_cutout(),(0,0),source_cutout())
            im.paste(clean.crop((0,0,wipe,566)),(111,394))
            line(im,(111+wipe,386,111+wipe,967),AMBER,4)
        for j in range(5):
            x=111+j*1698/5
            d.rectangle((x+4,398,x+1698/5-4,957),outline='#f6cc76',width=2)
            txt(im,(x+20,415),f'0{j+1}',25,WHITE,latin=True)
        pill(im,140,887,'背景移除  →  完整姿态提取',True)
    elif s==7:
        heading(im,'MAKING OF / 02','五幅画，开始跳跃','同一个角色、同一个比例；改变的是姿态与位置。',local,True)
        playback=.48*min(local,3.4)+max(0,local-3.4)
        active=index(4,playback)
        for j in range(5):
            x=107+j*218
            card(im,(x,430,x+201,674),'#253038',AMBER if j==active else '#465059',width=3)
            pet(im,4,j,x+100,660,219)
            txt(im,(x+100,700),f'FRAME {j+1:02d}',22,AMBER if j==active else MUTED,latin=True,anchor='mm')
        card(im,(1230,394,1812,924),'#ece6da',radius=28)
        pet(im,4,active,1521,906,515)
        txt(im,(1519,440),'PLAYBACK',24,INK,latin=True,anchor='mm')
        line(im,(118,818,1171,818),'#55616b',3)
        total=sum(DURATIONS[4])
        pos=118+1053*(playback%total)/total
        elapsed=0
        for duration in [0]+DURATIONS[4]:
            elapsed+=duration
            xx=118+1053*elapsed/total
            line(im,(xx,805,xx,832),'#75818a',2)
        d.polygon([(pos-9,781),(pos+9,781),(pos,795)],fill=AMBER)
        line(im,(pos,796,pos,856),AMBER,3)
        txt(im,(118,881),'序列帧 + 每帧停留时间 = 动画',32,WHITE,True)
        txt(im,(118,935),'先慢放看起落，再循环播放。',25,MUTED)
    elif s==8:
        heading(im,'MAKING OF / 03','把动作装进一张图','57 幅动作帧 + 16 幅视线姿态 = 73 幅有效姿态',local,True)
        gridx,gridy,cw,ch=110,397,75,49
        cells=[(r,c) for r,n in enumerate(COUNTS) for c in range(n)]
        k=int(local/.10)%73;r,c=cells[k]
        for rr in range(11):
            for cc in range(8):
                x=gridx+cc*cw;y=gridy+rr*ch
                d.rectangle((x,y,x+cw-3,y+ch-3),fill='#2d3840' if cc<COUNTS[rr] else '#1b2329',outline=AMBER if (rr,cc)==(r,c) else '#424e56',width=2)
                if cc<COUNTS[rr]:pet(im,rr,cc,x+cw/2,y+ch-4,48)
        txt(im,(111,960),'8 列 × 11 行  /  透明精灵图',23,MUTED)
        card(im,(790,397,1305,940),'#eee8dd',radius=28)
        pet(im,r,c,1048,917,510)
        txt(im,(1048,444),'FRAME SELECTOR',24,INK,latin=True,anchor='mm')
        line(im,(711,gridy+r*ch+ch/2,767,gridy+r*ch+ch/2),AMBER,3)
        txt(im,(1390,430),'73',100,AMBER,latin=True)
        txt(im,(1394,551),'幅有效姿态',30,WHITE)
        for j,label in enumerate(['统一尺寸与基线','透明边缘检查','方向辨识验证']):
            yy=665+j*80;draw_check(im,1390,yy,1)
            txt(im,(1450,yy-4),label,26,WHITE)
        txt(im,(1394,917),'这就是小伙伴的动作库。',25,MUTED)
    elif s==9:
        txt(im,(105,203),'MEET ZHIHE',28,AMBER,latin=True)
        txt(im,(94,275),'知核',146,INK,True)
        txt(im,(108,470),'认真做事，',58,INK,True)
        txt(im,(108,550),'也认真陪你。',58,INK,True)
        pill(im,111,685,'你的工作小伙伴')
        txt(im,(110,801),'从一帧帧姿态，到一个有回应的小伙伴。',28,MUTED)
        row=4 if local<1.7 else 3
        pet(im,row,index(row,local if row==4 else local-1.7,.7),1375,928,835)
        txt(im,(1375,959),'ZHIHE  /  MADE FRAME BY FRAME',24,AMBER,latin=True,anchor='mm')
    chrome(im,s,t,dark)
    return im

@lru_cache(None)
def source_cutout():
    im=SOURCE.convert('RGBA')
    pixels=[]
    for r,g,b,a in im.getdata():
        pixels.append((0,0,0,0) if (r-255)**2+g*g+(b-255)**2<96**2 else (r,g,b,a))
    im.putdata(pixels)
    return im.resize((1698,566),Image.Resampling.LANCZOS)

def render(t):
    s=min(len(CUTS)-2,bisect.bisect_right(CUTS,t)-1)
    result=scene(s,t)
    if s>0 and t-CUTS[s]<.32:
        result=Image.blend(scene(s-1,CUTS[s]-.001),result,ease((t-CUTS[s])/.32))
    if t<.4:result=Image.blend(background(False),result,ease(t/.4))
    if t>LENGTH-.6:result=Image.blend(result,Image.new('RGB',(W,H),CREAM),ease((t-(LENGTH-.6))/.6))
    return result

def make_audio(path):
    sr=24000;n=sr*LENGTH;signal=array.array('f',[0])*n
    def note(start,duration,freq,amp,kind='pluck'):
        begin=round(start*sr);count=min(round(duration*sr),n-begin)
        for i in range(max(0,count)):
            t=i/sr
            if kind=='kick':v=math.sin(math.tau*(48*t+9*(1-math.exp(-t*35))))*math.exp(-t*15)
            else:
                env=(1-math.exp(-t*110))*math.exp(-t*(4 if kind=='pluck' else 1.2))
                v=(math.sin(math.tau*freq*t)+.2*math.sin(math.tau*freq*2*t))*env
            signal[begin+i]+=amp*v
    chords=[[50,57,62,65],[46,53,58,62],[53,60,65,69],[48,55,60,64]]
    beat=.6
    for b in range(math.ceil(LENGTH/beat)):
        start=b*beat;chord=chords[(b//8)%4]
        note(start,.28,48,.10,'kick')
        note(start,1.2,440*2**((chord[0]-69)/12),.055,'pad')
        for off in (0,.3):
            midi=chord[(b+int(off>0))%4]+24
            note(start+off,.65,440*2**((midi-69)/12),.045,'pluck')
    for cut in CUTS[1:-1]:
        note(cut,.65,880,.055);note(cut+.08,.6,1320,.035)
    # Tiny original timing ticks in the frame-sequencing section.
    for k in range(35):note(34+k*.2,.05,1700,.018)
    data=array.array('h')
    for i,v in enumerate(signal):
        t=i/sr;fade=min(1,t/1.2,(LENGTH-t)/1.5)
        v=max(-.9,min(.9,v*fade))
        data.append(round(v*32767));data.append(round(v*32767))
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes(data.tobytes())

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default=str(ROOT/'output'));p.add_argument('--stills-only',action='store_true')
    a=p.parse_args();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
    qa=ROOT/'qa';qa.mkdir(exist_ok=True)
    times=[2.6,7.5,12,16.3,20.9,24.5,31.4,37.2,44.2,52.3]
    board=Image.new('RGB',(1920,1200),'#11171b')
    for i,t in enumerate(times):
        shot=render(t);shot.save(qa/f'shot-{i+1:02d}.png')
        thumb=shot.resize((576,324),Image.Resampling.LANCZOS)
        x=20+(i%3)*635;y=20+(i//3)*295
        if i<9:
            thumb=shot.resize((600,338),Image.Resampling.LANCZOS)
            # 3x3 storyboard; outro exported separately.
            board.paste(thumb,(20+(i%3)*635,20+(i//3)*390))
            txt(board,(24+(i%3)*635,365+(i//3)*390),f'{t:04.1f}s  /  {SCENES[i][1]}',23,WHITE)
    board.save(out/'storyboard.jpg',quality=93)
    render(2.6).save(out/'poster.jpg',quality=95)
    if a.stills_only:return
    audio=ROOT/'soundtrack.wav';make_audio(audio)
    ff=imageio_ffmpeg.get_ffmpeg_exe();video=out/'zhihe-promo.mp4'
    cmd=[ff,'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
         '-i',str(audio),'-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart','-shortest',str(video)]
    with (qa/'encode.log').open('wb') as log:
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log)
        for frame in range(FPS*LENGTH):
            process.stdin.write(render(frame/FPS).tobytes())
            if frame%(FPS*5)==0:print(f'rendered {frame/FPS:.0f}/{LENGTH}s',flush=True)
        process.stdin.close();rc=process.wait()
        if rc:raise RuntimeError('FFmpeg failed; inspect qa/encode.log')
    subprocess.run([ff,'-y','-ss','28','-i',str(video),'-t','21','-vf','fade=t=in:st=0:d=0.3,fade=t=out:st=20.5:d=0.5',
        '-af','afade=t=in:st=0:d=0.3,afade=t=out:st=20.5:d=0.5','-c:v','libx264','-crf','19','-preset','fast','-c:a','aac','-b:a','160k','-movflags','+faststart',str(out/'zhihe-making-of.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    # Low-bandwidth animated inline preview from exact rendered footage.
    subprocess.run([ff,'-y','-ss','34','-t','4.5','-i',str(video),'-vf','fps=10,scale=768:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse','-loop','0',str(out/'frames-to-animation.gif')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    manifest={'title':'知核 · 认真做事，也认真陪你','resolution':[W,H],'fps':FPS,'duration_seconds':LENGTH,'audio':'Original programmatically synthesized instrumental score and timing ticks; no voiceover.',
        'production':'Real approved pet frames reused; motion-graphics compositing and timing. Behind-the-scenes visualization uses actual source strip and atlas, not a screen recording.',
        'atlas_sha256':hashlib.sha256((ROOT/'assets/spritesheet.png').read_bytes()).hexdigest(),
        'scenes':[{'start':CUTS[i],'end':CUTS[i+1],'title':SCENES[i][1]} for i in range(10)]}
    (out/'production.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('DONE '+str(video),flush=True)

if __name__=='__main__':main()
