import json
from pathlib import Path
from PIL import Image

root = Path(__file__).parent
frames = root / 'frames' / 'waving'
backup = root / 'unregistered-frames'
backup.mkdir(exist_ok=True)
items = []
for path in sorted(frames.glob('*.png')):
    im = Image.open(path).convert('RGBA')
    im.save(backup / path.name)
    points = [(x, y) for y in range(175, 208) for x in range(192)
              if (lambda p: p[3] > 200 and p[0] > p[1] * 1.15 and p[1] > p[2] * 1.5)(im.getpixel((x, y)))]
    bounds = [min(x for x,y in points), min(y for x,y in points),
              max(x for x,y in points)+1, max(y for x,y in points)+1]
    items.append((path, im, bounds, (bounds[0]+bounds[2])/2))
target = items[0][3]
report = []
for path, im, bounds, center in items:
    dx = round(target-center)
    bb = im.getbbox()
    assert bb[0]+dx >= 0 and bb[2]+dx <= 192
    out = Image.new('RGBA', im.size)
    out.alpha_composite(im, (dx, 0))
    assert sum(p[3] for p in out.getdata()) == sum(p[3] for p in im.getdata())
    out.save(path)
    report.append({'frame': path.name, 'feet_bbox_before':bounds, 'feet_center_before':center,
                   'target_center':target, 'translation':[dx,0], 'scale':1,
                   'alpha_mass_preserved':True})
(root/'registration-correction.json').write_text(json.dumps({'method':'integer translation from amber feet bbox center; no redrawing or resizing', 'frames':report}, indent=2),encoding='utf-8')
