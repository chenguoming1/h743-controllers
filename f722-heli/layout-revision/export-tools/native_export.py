#!/usr/bin/env python3
"""Fail-closed F722 native export. Run with the pinned KiCad Python wrapper.

No source changes, zone refill, guessed placement corrections, or qualification.
The historical-control exception is bound to the original PCB AND parts hashes.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

import pcbnew

HERE = Path(__file__).resolve().parent
HISTORICAL_PCB = '4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f'
HISTORICAL_PARTS = '3dc37171d45add434f693219ea37f9f9ff2c9bc58830d2215f0c34760b2409d9'
REQUIRED_RECEIPTS = (
    'native-schematic-parity', 'firmware-pinmap', 'critical-signal-return-paths',
    'protection-paths', 'mechanical-process', 'via-mask-process',
    'electrical-power-review', 'warning-dispositions', 'parts-identity', 'zone-fill-replay',
)
LAYERS = {'F.Cu': 'gtl', 'In1.Cu': 'g1', 'In2.Cu': 'g2', 'In3.Cu': 'g3',
          'In4.Cu': 'g4', 'B.Cu': 'gbl', 'F.Mask': 'gts', 'B.Mask': 'gbs',
          'F.Paste': 'gtp', 'B.Paste': 'gbp', 'F.Silkscreen': 'gto',
          'B.Silkscreen': 'gbo', 'Edge.Cuts': 'gm1'}
MANUAL = {f'J{i}' for i in range(2, 9)}
BARE = {f'TP{i}' for i in range(1, 6)}
DEFAULT_NOTE = 'Exact identity retained; current stock and factory assembly acceptance not checked'
NOTES = {
    'J1': 'GCT vertical USB; mixed SMT/PTH; machine CPL covers placement only; solder all four plated shell slots; no shell paste; factory process/pickup/orientation approval required',
    'R16': 'HOLD: exact ERJ3RSFR12V/C4059772; assembly supply pending confirmation/private-stock route; no substitute; installed R16/C7/copper-loop qualification pending',
    'R31': 'YAGEO AC0201FR-0722RL/C144830; 0201; 0.05 W (50 mW); do not substitute former larger-package rating',
    **{r: 'Samtec exact HTSW-101-08-L-T-RA; no LCSC code; separate procurement and THT/manual assembly required; confirm actual supply and assembler handling' for r in MANUAL},
}


class GateError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise GateError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def refkey(ref):
    return tuple(int(x) if x.isdigit() else x for x in re.split(r'(\d+)', ref))


def source_identity(hardware):
    """Bind the entire CAD/parts/library input set, excluding UI state/backups."""
    suffixes = {'.kicad_pcb', '.kicad_pro', '.kicad_sch', '.kicad_dru',
                '.kicad_mod', '.kicad_sym', '.json'}
    paths = [p for p in hardware.rglob('*') if p.is_file() and
             (p.suffix in suffixes or p.name in {'fp-lib-table', 'sym-lib-table'})
             and not any(x.startswith('.') or x.endswith('-backups') for x in p.relative_to(hardware).parts)]
    files = {str(p.relative_to(hardware)): sha(p) for p in sorted(paths)}
    for required in ['f722-heli.kicad_pcb', 'f722-heli.kicad_pro', 'f722-heli.kicad_sch', 'parts.json']:
        require(required in files, f'Missing paired native input: {required}')
    return {'source_pcb_sha256': files['f722-heli.kicad_pcb'],
            'source_parts_sha256': files['parts.json'],
            'source_tree_sha256': digest(files), 'files': files}


def verify_receipts(path, identity, warning_hash):
    require(path is not None, 'Candidate exports require a validation receipt index; historical evidence cannot authorize a new board.')
    path = path.resolve()
    obj = json.loads(path.read_text())
    require(obj.get('schema') == 'f722-export-receipts-v1', 'Unknown receipt-index schema')
    for key in ['source_pcb_sha256', 'source_parts_sha256', 'source_tree_sha256']:
        require(obj.get(key) == identity[key], f'Receipt index has stale/missing {key}')
    entries = obj.get('receipts', {})
    require(set(entries) == set(REQUIRED_RECEIPTS), 'Receipt index must contain exactly the documented required scopes')
    verified = {}
    for name in REQUIRED_RECEIPTS:
        entry = entries[name]
        receipt_path = (path.parent / entry['path']).resolve()
        require(sha(receipt_path) == entry['sha256'], f'Receipt bytes changed: {name}')
        receipt = json.loads(receipt_path.read_text())
        require(receipt.get('schema') == 'f722-validation-receipt-v1', f'Unknown receipt schema: {name}')
        require(receipt.get('scope') == name and receipt.get('result') == 'pass', f'Receipt did not pass: {name}')
        for key in ['source_pcb_sha256', 'source_parts_sha256', 'source_tree_sha256']:
            require(receipt.get(key) == identity[key], f'Receipt {name} has stale/missing {key}')
        require(bool(receipt.get('method')) and bool(receipt.get('limitations')), f'Receipt {name} needs method and limits')
        evidence = receipt.get('evidence', [])
        require(bool(evidence), f'Receipt {name} has no underlying evidence')
        for item in evidence:
            require(sha(receipt_path.parent / item['path']) == item['sha256'], f'Evidence hash changed: {name}/{item["path"]}')
        if name == 'warning-dispositions':
            require(receipt.get('native_warning_signature_sha256') == warning_hash, 'Warning review does not match fresh unsuppressed native warnings')
        verified[name] = {'path': str(receipt_path), 'sha256': entry['sha256'],
                          'method': receipt['method'], 'limitations': receipt['limitations']}
    return verified


def native_inventory(board):
    footprints, pads, drills, outlines = {}, [], [], []
    for f in board.GetFootprints():
        ref = f.GetReference()
        require(ref not in footprints, f'Duplicate reference: {ref}')
        ident = f.GetFPID()
        attrs = f.GetAttributes()
        footprints[ref] = {
            'ref': ref, 'value': f.GetValue(),
            'footprint': str(ident.GetLibNickname()) + ':' + str(ident.GetLibItemName()),
            'package': str(ident.GetLibItemName()), 'x': f.GetPosition().x / 1e6,
            'y': -f.GetPosition().y / 1e6, 'rotation': f.GetOrientationDegrees(),
            'side': 'bottom' if f.GetLayer() == pcbnew.B_Cu else 'top',
            'dnp': bool(attrs & pcbnew.FP_DNP),
            'exclude_bom': bool(attrs & pcbnew.FP_EXCLUDE_FROM_BOM),
            'exclude_pos': bool(attrs & pcbnew.FP_EXCLUDE_FROM_POS_FILES),
            'smd': bool(attrs & pcbnew.FP_SMD), 'tht': bool(attrs & pcbnew.FP_THROUGH_HOLE),
            'fields': {x.GetName(): x.GetText() for x in f.GetFields()},
        }
        for p in f.Pads():
            pos, shape = p.GetPosition(), p.ShapePos(p.GetLayer())
            pads.append({'ref': ref, 'number': p.GetNumber(), 'net': p.GetNetname(),
                         'x': shape.x / 1e6, 'y': -shape.y / 1e6,
                         'layers': [board.GetLayerName(l) for l in p.GetLayerSet().Seq()]})
            size = p.GetDrillSize()
            if size.x and size.y:
                plating = 'NPTH' if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else 'PTH'
                cx, cy = pos.x / 1e6, -pos.y / 1e6
                dx, dy = size.x / 1e6, size.y / 1e6
                if abs(dx-dy) < 1e-9:
                    drills.append((plating, 'round', dx, cx, cy))
                else:
                    # Native PCB Y is inverted. Positive native angle becomes
                    # mathematical positive angle in the Gerber/Excellon frame.
                    angle = math.radians(p.GetOrientationDegrees())
                    vx, vy = ((dx-dy)/2, 0) if dx > dy else (0, (dy-dx)/2)
                    x = vx*math.cos(angle)-vy*math.sin(angle)
                    y = vx*math.sin(angle)+vy*math.cos(angle)
                    drills.append((plating, 'slot', min(dx, dy), cx-x, cy-y, cx+x, cy+y))
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            require(t.TopLayer() == pcbnew.F_Cu and t.BottomLayer() == pcbnew.B_Cu,
                    'Blind/buried via needs dedicated drill-file support')
            p = t.GetPosition()
            drills.append(('PTH', 'round', t.GetDrillValue()/1e6, p.x/1e6, -p.y/1e6))
    for item in board.GetDrawings():
        if item.GetLayer() == pcbnew.Edge_Cuts:
            require(item.GetShape() == pcbnew.SHAPE_T_SEGMENT, 'Only straight native outline segments supported by this verifier')
            a, b = item.GetStart(), item.GetEnd()
            outlines.append(((a.x/1e6, -a.y/1e6), (b.x/1e6, -b.y/1e6)))
    require(board.GetCopperLayerCount() == 6, 'This exporter requires exactly six copper layers')
    return {'footprints': footprints, 'pads': pads, 'drills': drills, 'outline': outlines,
            'copper_layers': board.GetCopperLayerCount()}


def verify_identities(inv, parts):
    fps = inv['footprints']
    excluded = {r for r, f in fps.items() if f['exclude_bom'] or f['exclude_pos']}
    require(excluded == BARE, f'Unexpected excluded references: {sorted(excluded)}')
    require(all(fps[r]['exclude_bom'] and fps[r]['exclude_pos'] for r in BARE), 'Test-pad BOM/position exclusions must both be explicit')
    require(not any(f['dnp'] for f in fps.values()), 'DNP set changed; explicit assembly policy review required')
    populated = set(fps) - BARE
    require(set(parts) == populated, 'Parts identity set differs from populated native references')
    manual = {r for r in populated if fps[r]['tht']}
    require(manual == MANUAL, f'Manual/THT classification changed: {sorted(manual)}')
    for ref in populated:
        f, p = fps[ref], parts[ref]
        require(p.get('proposed_footprint') == f['footprint'], f'Parts/native footprint mismatch: {ref}')
        require(p.get('manufacturer') and p.get('mpn'), f'Missing manufacturer or MPN: {ref}')
        require(ref in MANUAL or p.get('jlcpcb_lcsc_code'), f'SMT supplier code missing: {ref}')
        require(ref in MANUAL or f['smd'], f'Unclassified populated footprint: {ref}')
        for field, key in [('Manufacturer', 'manufacturer'), ('MPN', 'mpn'), ('LCSC', 'jlcpcb_lcsc_code')]:
            actual = f['fields'].get(field, '')
            require(not actual or actual == p.get(key), f'Native identity field mismatch: {ref}/{field}')
    # Notes are specific to these exact selected parts. Refuse silent note reuse.
    for ref, mpn, code in [('J1', 'USB4145-03-0170-C', 'C5181332'),
                           ('R16', 'ERJ3RSFR12V', 'C4059772'),
                           ('R31', 'AC0201FR-0722RL', 'C144830')]:
        require(parts[ref]['mpn'] == mpn and parts[ref]['jlcpcb_lcsc_code'] == code, f'{ref} handling policy needs review after identity change')
    require(all(parts[r]['mpn'] == 'HTSW-101-08-L-T-RA' and not parts[r].get('jlcpcb_lcsc_code') for r in MANUAL), 'Manual header identity/code policy changed')
    return populated


def write_csv(path, columns, rows):
    with Path(path).open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)


def read_csv(path):
    with Path(path).open(newline='') as f:
        return list(csv.DictReader(f))


def build_assembly(out, inv, parts):
    fps = inv['footprints']
    populated = verify_identities(inv, parts)
    native = read_csv(out/'native-all-pos.csv')
    require(len(native) == len(populated) and {r['Ref'] for r in native} == populated, 'Native position coverage/duplicates mismatch')
    poses = {r['Ref']: r for r in native}
    for ref, p in poses.items():
        f = fps[ref]
        require(p['Val'] == f['value'] and p['Package'] == f['package'] and p['Side'] == f['side'], f'Native position identity/side mismatch: {ref}')
        for column, key in [('PosX', 'x'), ('PosY', 'y'), ('Rot', 'rotation')]:
            require(abs(float(p[column])-f[key]) <= 0.0000011, f'Native position coordinate/rotation mismatch: {ref}/{column}')
    refs = sorted(populated, key=refkey)
    smt = [r for r in refs if r not in MANUAL]
    rows, groups = [], defaultdict(list)
    for ref in refs:
        f, p = fps[ref], parts[ref]
        note = NOTES.get(ref, DEFAULT_NOTE)
        rows.append([ref, 1, f['value'], p['manufacturer'], p['mpn'], p.get('jlcpcb_lcsc_code') or '',
                     f['footprint'], f['side'], 'Manual/THT' if ref in MANUAL else 'SMT candidate',
                     p.get('supplier_url', ''), p.get('datasheet_url', ''), note])
        groups[(f['value'], p['manufacturer'], p['mpn'], f['footprint'], p.get('jlcpcb_lcsc_code') or '', note)].append(ref)
    write_csv(out/'procurement-full-per-reference.csv', ['Reference','Quantity','Value','Manufacturer','MPN','LCSC Part #','Footprint','Side','Assembly route','Supplier URL','Datasheet URL','Notes'], rows)
    group_rows = [[','.join(rs), len(rs), *key] for key, rs in groups.items()]
    write_csv(out/'procurement-full-grouped.csv', ['Designator','Quantity','Value','Manufacturer','MPN','Footprint','LCSC Part #','Notes'], group_rows)
    bom_rows = [[key[0], ','.join(rs), key[3], key[4]] for key, rs in groups.items() if not set(rs) & MANUAL]
    write_csv(out/'jlc-bom-SMT-HELD.csv', ['Comment','Designator','Footprint','LCSC Part #'], bom_rows)
    write_csv(out/'jlc-cpl-SMT-HELD.csv', ['Designator','Mid X','Mid Y','Layer','Rotation'],
              [[r, poses[r]['PosX'], poses[r]['PosY'], poses[r]['Side'], poses[r]['Rot']] for r in smt])
    pose_columns = ['Reference','Value','MPN','Footprint','X mm','Y mm','Rotation deg','Side','Notes']
    def pose_row(r):
        return [r, fps[r]['value'], parts[r]['mpn'], fps[r]['footprint'], poses[r]['PosX'], poses[r]['PosY'], poses[r]['Rot'], poses[r]['Side'], NOTES.get(r, DEFAULT_NOTE)]
    write_csv(out/'placement-all-populated-reference.csv', pose_columns, [pose_row(r) for r in refs])
    write_csv(out/'placement-manual-THT.csv', pose_columns, [pose_row(r) for r in sorted(MANUAL, key=refkey)])
    write_csv(out/'excluded-board-features.csv', ['Reference','Value','Footprint','DNP','Excluded from BOM','Excluded from positions','Reason'],
              [[r, fps[r]['value'], fps[r]['footprint'], False, True, True, 'Bare PCB SWD test pad; no purchased or placed part; copper/mask retained'] for r in sorted(BARE, key=refkey)])
    write_csv(out/'factory-rotation-verification-required.csv', ['Reference','MPN','Footprint','Native rotation deg','Side','Applied correction deg','Factory placement preview'],
              [[r, parts[r]['mpn'], fps[r]['footprint'], poses[r]['Rot'], poses[r]['Side'], 0, 'REQUIRED: confirm supplier-library pin-1/polarity/pickup mapping against board, both sides'] for r in smt])
    # Re-open assembled CSVs and independently check set and grouped identity joins.
    bom = read_csv(out/'jlc-bom-SMT-HELD.csv')
    bom_refs = [ref for row in bom for ref in row['Designator'].split(',')]
    cpl = read_csv(out/'jlc-cpl-SMT-HELD.csv')
    require(Counter(bom_refs) == Counter(smt) == Counter(row['Designator'] for row in cpl), 'BOM/CPL reference coverage mismatch')
    for row in bom:
        for ref in row['Designator'].split(','):
            require(row['LCSC Part #'] == parts[ref]['jlcpcb_lcsc_code'] and row['Footprint'] == fps[ref]['footprint'] and row['Comment'] == fps[ref]['value'], f'BOM identity mismatch: {ref}')
    return {'board_footprints': len(fps), 'populated_procurement_refs': len(populated),
            'procurement_groups': len(groups), 'smt_cpl_refs': len(smt), 'smt_bom_groups': len(bom_rows),
            'smt_side_counts': dict(Counter(fps[r]['side'] for r in smt)),
            'manual_tht_refs': sorted(MANUAL, key=refkey), 'excluded_bare_test_pads': sorted(BARE, key=refkey),
            'position_origin_mm': [0, 0], 'output_y_is_negative_native_y': True,
            'rotation_corrections_applied': False, 'factory_placement_preview_required': True,
            'native_position_identity_coordinate_rotation_side_match': True}


def drill_key(item):
    plating, kind, diameter, *coords = item
    coords = [round(x, 3) for x in coords]
    if kind == 'slot':
        ends = sorted([tuple(coords[:2]), tuple(coords[2:])])
        coords = list(ends[0] + ends[1])
    return (plating, kind, round(diameter, 3), *coords)


def parse_drill(path, plating):
    content = path.read_text()
    require('METRIC' in content and 'G90' in content, 'Unexpected Excellon units/origin convention')
    tools, features, active, start = {}, [], None, None
    for line in content.splitlines():
        m = re.fullmatch(r'T(\d+)C([\d.]+)', line)
        if m:
            tools[int(m[1])] = float(m[2]); continue
        m = re.fullmatch(r'T(\d+)', line)
        if m:
            active = int(m[1]); continue
        m = re.fullmatch(r'(G00|G01)?X(-?[\d.]+)Y(-?[\d.]+)', line)
        if m:
            require(active in tools, 'Excellon hit with unknown tool')
            pos = (float(m[2]), float(m[3]))
            if m[1] == 'G00':
                start = pos
            elif m[1] == 'G01':
                require(start is not None, 'Excellon slot end without start')
                features.append((plating, 'slot', tools[active], *start, *pos)); start = None
            else:
                features.append((plating, 'round', tools[active], *pos))
        elif ('X' in line or 'Y' in line) and not line.startswith(';'):
            raise GateError(f'Unsupported Excellon motion: {line}')
    return features, tools


def parse_gerber(path):
    content = path.read_text()
    require('%FSLAX46Y46*%' in content and '%MOMM*%' in content, 'Unexpected Gerber coordinate format')
    pos, attr, flashes, segments = (0., 0.), None, [], []
    for line in content.splitlines():
        if line.startswith('%TO.P,'):
            attr = line.removeprefix('%TO.P,').removesuffix('*%').split(',')[:2]
        elif line.startswith('%TD'):
            attr = None
        m = re.fullmatch(r'(?:X(-?\d+))?(?:Y(-?\d+))?D0([123])\*', line)
        if m:
            new = (float(m[1])/1e6 if m[1] else pos[0], float(m[2])/1e6 if m[2] else pos[1])
            if m[3] == '3':
                flashes.append({'xy': new, 'pad': attr[:] if attr else None})
            elif m[3] == '1':
                segments.append((pos, new))
            pos = new
    return flashes, segments


def xykey(xy):
    return tuple(round(x, 5) for x in xy)


def verify_fabrication(out, inv):
    paths = {layer: out/'gerbers'/f'f722-heli-{layer.replace(".", "_")}.{ext}' for layer, ext in LAYERS.items()}
    require(all(p.is_file() and p.stat().st_size for p in paths.values()), 'Missing/empty required Gerber')
    require(len(list((out/'gerbers').glob('*'))) == 14, 'Unexpected Gerber layer/job inventory')
    results = {'gerber_files': len(paths), 'gerber_job_files': 1, 'drill_files': 2, 'drill_maps': 2,
               'all_physical_native_pad_objects': len(inv['pads']), 'origin_mm': [0, 0],
               'paste_flash_checks': {}, 'copper_flash_checks': {}, 'drill_checks': {}}
    for layer in ['F.Paste', 'B.Paste']:
        flashes, _ = parse_gerber(paths[layer])
        expected = Counter(xykey((p['x'], p['y'])) for p in inv['pads'] if layer in p['layers'])
        actual = Counter(xykey(f['xy']) for f in flashes)
        require(actual == expected, f'{layer} native pad/flash center multiset mismatch')
        results['paste_flash_checks'][layer] = {'flashes': len(flashes), 'native_paste_pads': sum(expected.values()), 'center_multiset_match': True,
                                                'aperture_shapes_independently_verified': False}
    for layer in ['F.Cu', 'B.Cu']:
        flashes, _ = parse_gerber(paths[layer])
        attributed = [f for f in flashes if f['pad']]
        require(bool(attributed), f'{layer} netlist pad attributes missing')
        expected = defaultdict(set)
        for p in inv['pads']:
            if layer in p['layers']:
                expected[(p['ref'], p['number'])].add(xykey((p['x'], p['y'])))
        for f in attributed:
            require(xykey(f['xy']) in expected[tuple(f['pad'])], f'{layer} attributed copper flash center mismatch: {f["pad"]}')
        results['copper_flash_checks'][layer] = {'attributed_pad_flashes_compared': len(attributed), 'center_mismatches': []}
    usb_pads = [p for p in inv['pads'] if p['ref'] == 'J1']
    results['usb_contact_paste_flashes'] = sum('F.Paste' in p['layers'] or 'B.Paste' in p['layers'] for p in usb_pads if p['number'] != 'S1')
    results['usb_shell_paste_flashes'] = sum('F.Paste' in p['layers'] or 'B.Paste' in p['layers'] for p in usb_pads if p['number'] == 'S1')
    require(results['usb_contact_paste_flashes'] == 16 and results['usb_shell_paste_flashes'] == 0, 'USB contact/shell paste policy changed')
    for plating in ['PTH', 'NPTH']:
        features, tools = parse_drill(out/'drill'/f'f722-heli-{plating}.drl', plating)
        expected = [d for d in inv['drills'] if d[0] == plating]
        require(Counter(map(drill_key, features)) == Counter(map(drill_key, expected)), f'{plating} native/Excellon hole or slot mismatch at 0.001 mm')
        require((out/'drill'/f'f722-heli-{plating}-drl_map.svg').is_file(), f'Missing {plating} drill map')
        slots = [{'tool_mm': d[2], 'start_mm': d[3:5], 'end_mm': d[5:7],
                  'finished_length_mm': round(math.dist(d[3:5], d[5:7])+d[2], 6)} for d in features if d[1] == 'slot']
        results['drill_checks'][plating] = {'round_holes': sum(d[1] == 'round' for d in features), 'routed_slots': len(slots),
                                            'total': len(features), 'tools_mm': tools, 'slot_details': slots,
                                            'native_coordinate_and_size_match_at_0_001mm': True}
    _, actual = parse_gerber(paths['Edge.Cuts'])
    segkey = lambda seg: tuple(sorted(map(xykey, seg)))
    require(Counter(map(segkey, actual)) == Counter(map(segkey, inv['outline'])), 'Export/native outline segments differ')
    adjacency = defaultdict(set)
    for a, b in inv['outline']:
        adjacency[xykey(a)].add(xykey(b)); adjacency[xykey(b)].add(xykey(a))
    require(adjacency and all(len(v) == 2 for v in adjacency.values()), 'Outline is not a closed contour')
    visited, stack = set(), [next(iter(adjacency))]
    while stack:
        cur = stack.pop()
        if cur not in visited:
            visited.add(cur); stack.extend(adjacency[cur] - visited)
    require(len(visited) == len(adjacency), 'Outline contains multiple contours')
    xs, ys = zip(*visited)
    results['outline_centerline_size_mm'] = [round(max(xs)-min(xs), 6), round(max(ys)-min(ys), 6)]
    results['outline_closed_single_contour'] = True
    results['outline_lines_match_native'] = True
    results['limits'] = 'Native coordinate/metadata and hole-size checks; no independent full copper/mask/paste CAM raster or aperture-shape comparison.'
    return results


def native_warning_signature(report):
    warnings = [x for x in report.get('violations', []) if x.get('severity') == 'warning']
    return digest(sorted(warnings, key=lambda x: json.dumps(x, sort_keys=True)))


def run(args):
    args.output_created = False
    exporter_hash = sha(Path(__file__))
    hardware = args.hardware.resolve()
    out = args.output.resolve()
    require(not out.is_relative_to(hardware), 'Output cannot be inside the hardware source tree')
    require(not out.exists(), 'Output directory already exists; use a new directory to prevent stale payload mixing')
    out.mkdir(parents=True)
    args.output_created = True
    (out/'verification').mkdir()
    source = source_identity(hardware)
    write_json(out/'verification'/'source-identity.json', source)
    require(args.expected_pcb_sha256 == source['source_pcb_sha256'], 'Expected source PCB SHA mismatch')
    require(pcbnew.Version() == '10.0.6', 'The pinned KiCad 10.0.6 Python runtime is required')
    cli = args.kicad_cli.resolve()
    cli_version = subprocess.check_output([str(cli), '--version'], text=True).strip()
    require(cli_version == '10.0.6', 'KiCad CLI version mismatch')
    runtime_provenance = {'pcbnew_reported_version': pcbnew.Version(),
                          'cli_reported_version': cli_version, 'cli_executable_sha256': sha(cli)}
    if args.runtime_provenance is not None:
        runtime_provenance['provided_provenance_sha256'] = sha(args.runtime_provenance)
    commands = []
    def command(label, *argv):
        result = subprocess.run([str(cli), *map(str, argv)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        (out/'verification'/f'{label}.log').write_text(result.stdout)
        commands.append({'label': label, 'argv': [str(cli), *map(str, argv)], 'exit_code': result.returncode})
        write_json(out/'verification'/'commands.json', commands)
        require(result.returncode == 0, f'Native command failed ({label}); see its log')
    boardpath = hardware/'f722-heli.kicad_pcb'
    schpath = hardware/'f722-heli.kicad_sch'
    command('drc', 'pcb', 'drc', '--format', 'json', '--all-track-errors', '--severity-all', '-o', out/'verification'/'drc.json', boardpath)
    drc = json.loads((out/'verification'/'drc.json').read_text())
    require(drc.get('kicad_version') == '10.0.6' and drc.get('source') == boardpath.name
            and 'violations' in drc and 'unconnected_items' in drc
            and set(drc.get('included_severities', [])) == {'error', 'warning', 'exclusion'},
            'Malformed/incomplete native DRC report')
    require(not drc.get('ignored_checks'), 'Native DRC has ignored checks; explicit review and exporter policy change required')
    opens = len(drc.get('unconnected_items', []))
    errors = [x for x in drc.get('violations', []) if x.get('severity') in ('error', 'exclusion')]
    warning_hash = native_warning_signature(drc)
    gate = {'source_pcb_sha256': source['source_pcb_sha256'], 'opens': opens, 'geometric_errors': len(errors),
            'native_warning_signature_sha256': warning_hash, 'drc_warning_count': sum(x.get('severity') == 'warning' for x in drc.get('violations', [])),
            'mode': args.mode, 'passed': False, 'production_or_flight_qualification': False}
    write_json(out/'verification'/'gate.json', gate)
    require(opens == 0 and len(errors) == 0, f'Native gate blocked: {opens} opens; {len(errors)} errors/exclusions. No manufacturing files exported.')
    command('erc', 'sch', 'erc', '--format', 'json', '--severity-all', '-o', out/'verification'/'erc.json', schpath)
    erc = json.loads((out/'verification'/'erc.json').read_text())
    require(erc.get('kicad_version') == '10.0.6' and erc.get('source') == schpath.name
            and len(erc.get('sheets', [])) == 9 and not erc.get('ignored_checks')
            and set(erc.get('included_severities', [])) == {'error', 'warning', 'exclusion'},
            'Malformed/incomplete native ERC report')
    erc_count = sum(len(s.get('violations', [])) for s in erc.get('sheets', []))
    require(erc_count == 0, f'Fresh native ERC has {erc_count} violations')
    gate['erc_violations'] = erc_count
    if args.mode == 'historical-control':
        require(source['source_pcb_sha256'] == HISTORICAL_PCB and source['source_parts_sha256'] == HISTORICAL_PARTS, 'Historical-control bypass allowed ONLY for exact original PCB and parts bytes')
        gate['receipt_exception'] = 'HISTORICAL EXPORTER CONTROL ONLY; no current-revision or release validation claimed'
        verified_receipts = {}
    else:
        verified_receipts = verify_receipts(args.receipts, source, warning_hash)
    require(source_identity(hardware) == source, 'Source changed during gate checks')
    gate['passed'] = True
    gate['meaning'] = 'Native export preconditions only; no production/flight qualification, factory acceptance, upload, or order'
    write_json(out/'verification'/'gate.json', gate)
    if args.gate_only:
        print(json.dumps(gate, sort_keys=True)); return
    board = pcbnew.LoadBoard(str(boardpath))
    inv = native_inventory(board)
    parts = json.loads((hardware/'parts.json').read_text())
    verify_identities(inv, parts)
    for name in ['gerbers', 'drill', 'assembly', 'previews']:
        (out/name).mkdir()
    command('gerbers', 'pcb', 'export', 'gerbers', '--layers', ','.join(LAYERS), '--precision', '6', '-o', out/'gerbers', boardpath)
    command('drill', 'pcb', 'export', 'drill', '--format', 'excellon', '--drill-origin', 'absolute', '--excellon-zeros-format', 'decimal', '--excellon-oval-format', 'route', '--excellon-units', 'mm', '--excellon-separate-th', '--generate-map', '--map-format', 'svg', '--generate-report', '--report-path', out/'drill'/'drill-report.txt', '-o', out/'drill', boardpath)
    command('positions', 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'both', '-o', out/'assembly'/'native-all-pos.csv', boardpath)
    assembly = build_assembly(out/'assembly', inv, parts)
    fabrication = verify_fabrication(out, inv)
    command('schematic-pdf', 'sch', 'export', 'pdf', '--no-background-color', '-o', out/'previews'/'f722-heli-schematic.pdf', schpath)
    for side, layer in [('front', 'F'), ('back', 'B')]:
        argv = ['pcb', 'export', 'svg', '--layers', f'{layer}.Cu,{layer}.Silkscreen,Edge.Cuts', '--mode-single', '--fit-page-to-board', '--exclude-drawing-sheet', '-o', out/'previews'/f'board-{side}.svg']
        if side == 'back':
            argv.append('--mirror')
        command(f'preview-{side}', *argv, boardpath)
    require(source_identity(hardware) == source, 'Source changed during export; outputs invalid')
    require(sha(Path(__file__)) == exporter_hash, 'Exporter changed while running; rerun with frozen tooling')
    require(sha(cli) == runtime_provenance['cli_executable_sha256'], 'KiCad CLI changed while running')
    if args.runtime_provenance is not None:
        require(sha(args.runtime_provenance) == runtime_provenance['provided_provenance_sha256'], 'Runtime provenance file changed while running')
    write_json(out/'verification'/'assembly-verification.json', assembly)
    write_json(out/'verification'/'export-verification.json', fabrication)
    write_json(out/'verification'/'validated-receipts.json', verified_receipts)
    status = ('HISTORICAL CONTROL ONLY — NOT CURRENT LAYOUT — NOT FOR ORDERING' if args.mode == 'historical-control' else
              'SOURCE-BOUND PROTOTYPE EXPORTS — FACTORY CAM/ASSEMBLY ACCEPTANCE REQUIRED')
    notes = f'''# {status}\n\nPCB SHA-256: {source['source_pcb_sha256']}\n\nGenerated natively with KiCad 10.0.6 without changing or refilling the source. This gate proves only the scoped checks in the manifest. DRC/ERC are not circuit, production, thermal, mechanical or flight qualification. All later source edits invalidate these exports and their validation receipts.\n\nSix copper layers plus front/back mask, paste and silk, Edge.Cuts, separate PTH/NPTH drills/maps, exact signed native placements, SMT BOM/CPL, manual/THT and excluded test-pad lists are included. Origin (0,0), millimetres; output Y is negative native PCB Y. No supplier rotation correction or bottom-side X flip is applied. Factory pin-1, polarity, pickup and placement preview remain required.\n\nJ2–J8 remain exact Samtec headers with separate procurement and manual/THT assembly. TP1–TP5 are bare test pads. J1 retains 16 SMT contact paste apertures; its four plated shell slots have no shell paste and require a separately accepted soldering process. R16 exact supply/private stock and installed circuit qualification remain open. R31 is 0201, 50 mW. No substitute or supplier stock assumption was introduced.\n\nFactory stackup, central prepreg, 0201/stencil/reflow capability, shell-slot solder filling, double-sided process, handling/panels, full connector maximum envelopes, harness conditions, and first-article functional/thermal testing remain separate acceptance gates. No files were uploaded or ordered.\n\nPreview files are native PCB/schematic drawings, not independent CAM renders. Export verification compares outline segments, pad/flash centres, attributed copper pad centres, actual drill and routed-slot sizes/coordinates, native positions and part identities. It does not independently validate full Gerber copper/mask/paste aperture geometry or provide factory CAM acceptance.\n'''
    (out/'README.md').write_text(notes)
    manifest = {'schema': 'f722-native-export-v1', 'status': status, 'mode': args.mode,
                'created_utc': datetime.now(timezone.utc).isoformat(),
                **{k: source[k] for k in ['source_pcb_sha256','source_parts_sha256','source_tree_sha256']},
                'native_runtime_version': pcbnew.Version(), 'source_unchanged': True,
                'exporter_sha256': exporter_hash,
                'runtime_provenance': runtime_provenance,
                'native_gerber_build_string': (out/'gerbers'/'f722-heli-Edge_Cuts.gm1').read_text().splitlines()[0],
                'gate': gate, 'assembly': assembly, 'fabrication': fabrication,
                'validated_receipt_scopes': sorted(verified_receipts),
                'production_or_flight_qualification': False, 'published_uploaded_ordered': False,
                'files': [{'path': str(p.relative_to(out)), 'size_bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(out.rglob('*')) if p.is_file()]}
    write_json(out/'export-manifest.json', manifest)
    (out/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(out)}\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))
    print(json.dumps({'status': status, 'output': str(out), 'source_unchanged': True, 'assembly': assembly, 'fabrication': fabrication}, sort_keys=True))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--hardware', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--expected-pcb-sha256', required=True)
    p.add_argument('--mode', choices=['candidate', 'historical-control'], default='candidate')
    p.add_argument('--receipts', type=Path)
    p.add_argument('--gate-only', action='store_true')
    p.add_argument('--kicad-cli', type=Path, required=True,
                   help='Explicit path to the KiCad 10.0.6 CLI executable or wrapper')
    p.add_argument('--runtime-provenance', type=Path,
                   help='Optional runtime/package provenance file to hash into the export manifest')
    args = p.parse_args()
    try:
        run(args)
    except (GateError, OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as exc:
        message = {'status': 'BLOCKED — NOT FOR MANUFACTURE', 'reason': str(exc)}
        source_file = args.output/'verification'/'source-identity.json'
        if source_file.is_file():
            try:
                message['source_unchanged'] = source_identity(args.hardware.resolve()) == json.loads(source_file.read_text())
            except (OSError, ValueError, GateError):
                message['source_unchanged'] = None
        if getattr(args, 'output_created', False) and args.output.is_dir():
            write_json(args.output/'BLOCKED.json', message)
        print(json.dumps(message), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
