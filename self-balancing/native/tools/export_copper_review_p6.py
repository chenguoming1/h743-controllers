#!/usr/bin/python3
"""Export all six actual native copper layers after an exact P6 hash gate.

This intentionally does not edit the inherited exporter or save native CAD.
The rear view is mirrored for human inspection; CPL is never touched.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

D = Path(__file__).resolve().parents[1]
O = D / 'review'
B = D / 'controller.kicad_pcb'
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--expected-board-sha256', required=True)
ap.add_argument('--width', type=int, default=3400)
a = ap.parse_args()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert a.width >= 3200, 'Use at least 3200px actual copper width'
assert sha(B) == a.expected_board_sha256, 'Native board is not the agreed frozen source'
revision = json.loads((O / 'green-routing-targets.json').read_text())['revision']
assert revision == 'R3-S6-P6', 'Do not label a copied baseline P6'
report = json.loads((O / 'routing-drc.json').read_text())
erc = json.loads((O / 'erc.json').read_text())
counts = {
    'erc': sum(len(s['violations']) for s in erc['sheets']),
    'physical_drc': len(report['violations']),
    'parity': len(report['schematic_parity']),
    'unconnected': len(report['unconnected_items']),
}
assert all(v == 0 for v in counts.values()), counts
env = os.environ.copy()
env['XDG_CONFIG_HOME'] = '/tmp/controller-p6-inkscape-config'
env['XDG_CACHE_HOME'] = '/tmp/controller-p6-inkscape-cache'
Path(env['XDG_CONFIG_HOME']).mkdir(exist_ok=True)
cli = ['sh', str(D / 'tools/kicad_cli.sh')]
scale = a.width / 1700
font = lambda px: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', round(px * scale))
files = []
views = []
layers = [
    ('front-copper', 'F.Cu', 'F.SilkS', False, 'FRONT'),
    ('In1-Cu', 'In1.Cu', None, False, 'L2 GROUND'),
    ('In2-Cu', 'In2.Cu', None, False, 'L3 SIGNALS AND POWER'),
    ('In3-Cu', 'In3.Cu', None, False, 'L4 GROUND'),
    ('In4-Cu', 'In4.Cu', None, False, 'L5 GROUND'),
    ('rear-copper', 'B.Cu', 'B.SilkS', True, 'REAR'),
]
for name, layer, silk, mirror, label in layers:
    assert sha(B) == a.expected_board_sha256, 'Frozen board changed before export'
    svg = O / f'controller-r3s-{name}.svg'
    raw = O / f'controller-r3s-{name}-raw.png'
    png = O / f'controller-r3s-{name}.png'
    shown = [layer] + ([silk] if silk else []) + ['Edge.Cuts']
    cmd = cli + ['pcb', 'export', 'svg', '--mode-single', '--layers', ','.join(shown),
        '--fit-page-to-board', '--exclude-drawing-sheet', '--drill-shape-opt', '2', '--output', str(svg)]
    if mirror:
        cmd.append('--mirror')
    subprocess.run(cmd + [str(B)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['inkscape', str(svg), '--export-type=png', '--export-filename=' + str(raw),
        '--export-width=' + str(a.width), '--export-background=white', '--export-background-opacity=1'],
        env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    im = Image.open(raw).convert('RGB')
    w, h = im.size
    x, top, bottom = round(80 * scale), round(150 * scale), round(110 * scale)
    canvas = Image.new('RGB', (w + 2 * x, h + top + bottom), '#0b1923')
    canvas.paste(im, (x, top))
    draw = ImageDraw.Draw(canvas)
    draw.text((x, round(28 * scale)), f'{revision} H743 | {label} actual copper', font=font(37), fill='#f4faf8')
    draw.text((x, round(88 * scale)), '38 x 38 mm | six layers | Routed prototype CAD; hardware validation pending', font=font(23), fill='#83d8bd')
    orientation = 'Mirrored component-side view for human inspection; CPL remains unmirrored' if mirror else 'Native top-plan view; actual filled copper and holes'
    draw.text((x, h + top + round(23 * scale)), orientation, font=font(22), fill='#e3ece9')
    draw.text((x, h + top + round(57 * scale)), f'PCB SHA256 {a.expected_board_sha256[:20]}... | Drawing is not to print scale', font=font(19), fill='#b7c9c3')
    canvas.save(png)
    raw.unlink()
    files.extend([svg, png])
    views.append({'layer': layer, 'svg': str(svg), 'png': str(png), 'copper_width_px': w,
        'orientation': orientation, 'native_board_sha256': a.expected_board_sha256})
assert sha(B) == a.expected_board_sha256, 'Native board changed during preview export'
manifest = {'revision': revision, 'native_sha256': a.expected_board_sha256, 'check_counts': counts,
    'file_sha256': {p.name: sha(p) for p in files}, 'views': views,
    'visual_QA': {'status': 'PENDING', 'reviewed_files': [], 'no_provisional_markers': False, 'matches_actual_native_copper': False},
    'qualifications': ['Routed prototype CAD only; hardware validation and supplier acceptance remain pending'],
    'rear_view': 'Mirrored for human inspection only; CPL remains unmirrored'}
(O / 'copper-review-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'native_sha256': a.expected_board_sha256, 'check_counts': counts, 'views': views}, indent=2))
