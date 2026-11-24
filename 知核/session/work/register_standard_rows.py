"""Correct row-wide extraction scales; retain generated motion and per-row proportions."""
import json
from pathlib import Path
from PIL import Image

run = Path(__file__).parent / 'pets' / 'zhihe'
states = ['idle', 'running-right', 'running-left', 'waving', 'jumping', 'failed', 'waiting', 'running', 'review']
report = {'reason': 'Independent row extraction fills cells differently. Apply a constant affine scale per row, never per pose; preserve vertical displacement.', 'rows': []}
manifest = {'ok': True, 'rows': []}
for state in states:
    root = run / 'qa' / 'rows' / state / 'frames' / state
    paths = sorted(root.glob('*.png'))
    if not paths:
        raise RuntimeError(f'Missing frames {state}')
    first = Image.open(paths[0]).convert('RGBA')
    box = first.getchannel('A').point(lambda p: 255 if p > 16 else 0).getbbox()
    scale = 146 / (box[3] - box[1])
    baseline = box[3]
    target = run / 'qa' / 'frames' / state
    target.mkdir(parents=True, exist_ok=True)
    for path in paths:
        cell = Image.open(path).convert('RGBA')
        resized = cell.resize((round(192 * scale), round(208 * scale)), Image.Resampling.LANCZOS)
        result = Image.new('RGBA', (192, 208))
        result.alpha_composite(resized, (round(96 - 96 * scale), round(196 - baseline * scale)))
        result.save(target / path.name)
    report['rows'].append({'state': state, 'scale': scale, 'source_first_bbox': box, 'target_first_height': 146, 'target_ground_baseline': 196})
    manifest['rows'].append({'state': state, 'method': 'components', 'frames': [str(target / x.name) for x in paths]})
(run / 'qa' / 'row-registration.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
(run / 'qa' / 'frames' / 'frames-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
