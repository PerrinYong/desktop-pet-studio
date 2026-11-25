"""Render delivery previews from exact final atlas cells; never alter pet artwork."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw

p = argparse.ArgumentParser()
p.add_argument('atlas')
p.add_argument('output')
p.add_argument('skill_scripts')
a = p.parse_args()
out = Path(a.output)
out.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, a.skill_scripts)
from render_animation_previews import ROW_DURATIONS, save_preview

atlas = Image.open(a.atlas).convert('RGBA')
states = list(ROW_DURATIONS)
frames = {}
for row, state in enumerate(states):
    target = out / 'frames' / state
    target.mkdir(parents=True, exist_ok=True)
    frames[state] = []
    for col in range(len(ROW_DURATIONS[state])):
        cell = atlas.crop((col * 192, row * 208, (col + 1) * 192, (row + 1) * 208))
        cell.save(target / f'{col:02d}.png')
        frames[state].append(cell)
subprocess.run([sys.executable, str(Path(a.skill_scripts) / 'render_animation_previews.py'),
                '--frames-root', str(out / 'frames'), '--output-dir', str(out)], check=True)

def labeled(cell, label):
    result = Image.new('RGB', (256, 256), '#f4f1eb')
    result.paste(cell, (32, 12), cell)
    ImageDraw.Draw(result).text((12, 232), label, fill='#333333')
    return result

all_frames, durations = [], []
for state in states:
    for i, cell in enumerate(frames[state]):
        all_frames.append(labeled(cell, f'{state} / {i + 1}'))
        durations.append(ROW_DURATIONS[state][i])
save_preview(all_frames, durations, out / 'all-states.gif')
transition = frames['idle'] + frames['jumping'] + frames['idle']
save_preview(transition, ROW_DURATIONS['idle'] + ROW_DURATIONS['jumping'] + ROW_DURATIONS['idle'], out / 'idle-jump-idle.gif')
look_frames = [atlas.crop((i % 8 * 192, (9 + i // 8) * 208, (i % 8 + 1) * 192, (10 + i // 8) * 208)) for i in range(16)]
save_preview(look_frames, [160] * 16, out / 'look-loop.gif')
stills = Image.new('RGB', (1024, 256), '#f4f1eb')
for i, (state, index) in enumerate([('idle', 0), ('waving', 1), ('jumping', 2), ('review', 3)]):
    stills.paste(labeled(frames[state][index], f'{state} / frame {index + 1}'), (i * 256, 0))
stills.save(out / 'motion-stills.png')
cmd = [imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-i', str(out / 'all-states.gif'), '-movflags', '+faststart', '-pix_fmt', 'yuv420p', str(out / 'all-states.mp4')]
subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
print(json.dumps({'ok': True, 'output': str(out.resolve())}))
