#!/usr/bin/env python3
"""Read-only, native KiCad 10 validation for a Nexus F722 board reroute.

Run with a Python environment that provides KiCad 10 pcbnew. No third-party
Python packages are required. Does not modify boards, projects, or reports.
Exit 0 = every supplied/required gate passes; 1 = failed gate; 2 = incomplete
or invalid input. Reports are external evidence, not rerun by this script.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

import pcbnew

MIN_TRACK_IU = 127000
VIA_DIAMETER_IU = 450000
VIA_DRILL_IU = 200000
MIN_ANNULUS_IU = 125000
POWER_NETS = ('VX', '5V_BUCK', 'SW_5V', '5V', 'VBUS', 'VBUS_C', 'VSYS', '3V3_DSM', '3V3_SENS', 'SW_3V3', '3V3')
SILK_TYPES = {'silk_overlap', 'silk_over_copper', 'silk_edge_clearance'}
NUMBER = re.compile(r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$')
TOKEN = re.compile(r'\s+|;[^\n]*|\(|\)|"(?:\\.|[^"\\])*"|[^\s()"]+')


def stable(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(stable(value).encode()).hexdigest()


def file_record(path):
    p = Path(path)
    return {'path': str(p.resolve()), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
            'bytes': p.stat().st_size}


def parse_sexpr(text):
    """Token-preserving reader; numeric spelling/whitespace are not semantics."""
    roots, stack, pos = [], [], 0
    for m in TOKEN.finditer(text):
        if m.start() != pos:
            raise ValueError(f'Invalid S-expression text at byte {pos}')
        pos = m.end()
        token = m.group()
        if token.isspace() or token.startswith(';'):
            continue
        if token == '(':
            node = []
            (stack[-1] if stack else roots).append(node)
            stack.append(node)
        elif token == ')':
            if not stack:
                raise ValueError('Unbalanced closing parenthesis')
            stack.pop()
        else:
            if not stack:
                raise ValueError('Atom outside S-expression')
            if token.startswith('"'):
                # Keep quoted values distinct from numeric atoms, including pad numbers.
                value = token[1:-1]  # Preserve escapes conservatively; do not erase unknown escapes.
                stack[-1].append(('string', value))
            else:
                stack[-1].append(token)
    if stack or len(roots) != 1 or pos != len(text):
        raise ValueError('Invalid or incomplete S-expression')
    return roots[0]


def children(node, tag):
    return [x for x in node if isinstance(x, list) and x and x[0] == tag]


def atom(value):
    return value[1] if isinstance(value, tuple) else value


def canonical(node):
    if isinstance(node, list):
        # Net numeric codes are serialization-local; exact native net names and
        # pad assignments are independently checked. Keep any supplied net name.
        if node and node[0] == 'net' and len(node) == 3:
            return ['net', canonical(node[2])]
        return [canonical(x) for x in node]
    if isinstance(node, tuple):
        return ['string', node[1]]
    if isinstance(node, str) and NUMBER.fullmatch(node):
        value = Decimal(node)
        return ['number', '0' if not value else format(value.normalize(), 'f')]
    return node


def uid(obj):
    return obj.m_Uuid.AsString()


def xy(obj):
    p = obj.GetPosition()
    return [int(p.x), int(p.y)]


def mm(iu):
    return round(float(pcbnew.ToMM(iu)), 9)


def source_uuid(node):
    values = children(node, 'uuid')
    if len(values) != 1:
        raise ValueError(f'Expected one UUID in {node[0]}')
    return atom(values[0][1])


def keyed_nodes(nodes):
    result = {}
    for n in nodes:
        key = source_uuid(n)
        if key in result:
            raise ValueError(f'Duplicate source UUID: {key}')
        result[key] = canonical(n)
    return result



def zone_definitions(tree):
    """Preserve every board-zone definition except native refill result data."""
    normalized = []
    for zone in children(tree, 'zone'):
        definition = []
        for node in zone:
            if isinstance(node, list) and node:
                if node[0] in {'filled_polygon', 'fill_segments'}:
                    continue
                if node[0] == 'fill':
                    # The direct optional yes/no atom indicates fill-cache state.
                    # Nested fill rules, mode, and every other atom remain exact.
                    node = [node[0]] + [x for x in node[1:] if not (isinstance(x, str) and x in {'yes', 'no'})]
                    if len(node) == 1:
                        continue
            definition.append(node)
        normalized.append(definition)
    return keyed_nodes(normalized)


def zone_counts(tree):
    zones = children(tree, 'zone')
    keepouts = [z for z in zones if children(z, 'keepout')]
    ground = [z for z in zones if not children(z, 'keepout') and
              any(len(n) >= 2 and atom(n[-1]) == 'GND' for n in children(z, 'net'))]
    return {'total': len(zones), 'keepouts': len(keepouts), 'ground_copper_zones': len(ground)}


def native_footprints(board):
    result = {}
    for fp in board.GetFootprints():
        pads = []
        for pad in fp.Pads():
            pads.append({'uuid': uid(pad), 'number': pad.GetNumber(),
                         'net': pad.GetNetname(), 'position_iu': xy(pad),
                         'orientation_degrees': pad.GetOrientationDegrees(),
                         'layers': list(pad.GetLayerSet().Seq()),
                         'attribute': int(pad.GetAttribute()),
                         'size_iu': [int(pad.GetSize().x), int(pad.GetSize().y)],
                         'drill_iu': [int(pad.GetDrillSize().x), int(pad.GetDrillSize().y)],
                         'shape': int(pad.GetShape())})
        key = uid(fp)
        if key in result:
            raise ValueError(f'Duplicate footprint UUID: {key}')
        result[key] = {'reference': fp.GetReference(), 'value': fp.GetValue(),
                       'library_id': str(fp.GetFPID().GetLibNickname()) + ':' + str(fp.GetFPID().GetLibItemName()), 'position_iu': xy(fp),
                       'orientation_degrees': fp.GetOrientationDegrees(),
                       'layer': int(fp.GetLayer()), 'attributes': int(fp.GetAttributes()),
                       'pads': sorted(pads, key=lambda p: p['uuid'])}
    return result


def edge_nodes(node):
    out = []
    if isinstance(node, list):
        if any(len(x) > 1 and atom(x[1]) == 'Edge.Cuts' for x in children(node, 'layer')):
            out.append(canonical(node))
        for x in node:
            if isinstance(x, list):
                out.extend(edge_nodes(x))
    return sorted(out, key=stable)


def compare(label, baseline, candidate):
    same = baseline == candidate
    out = {'status': 'pass' if same else 'fail', 'baseline_sha256': digest(baseline),
           'candidate_sha256': digest(candidate)}
    if not same:
        if isinstance(baseline, dict) and isinstance(candidate, dict):
            out['removed_keys'] = sorted(set(baseline) - set(candidate))
            out['added_keys'] = sorted(set(candidate) - set(baseline))
            out['changed_keys'] = sorted(k for k in set(baseline) & set(candidate)
                                          if baseline[k] != candidate[k])
        out['description'] = f'{label} changed'
    return out


def invariant_checks(baseline, candidate, btree, ctree):
    bfp, cfp = native_footprints(baseline), native_footprints(candidate)
    checks = {
        'footprint_and_pad_native_geometry': compare('Native footprint/pad geometry', bfp, cfp),
        'complete_footprint_definitions': compare('Complete footprint definitions',
            keyed_nodes(children(btree, 'footprint')), keyed_nodes(children(ctree, 'footprint'))),
        'net_names': compare('Net names', sorted(n.GetNetname() for _, n in baseline.GetNetsByNetcode().items()),
                            sorted(n.GetNetname() for _, n in candidate.GetNetsByNetcode().items())),
        'outline': compare('Edge.Cuts definitions', edge_nodes(btree), edge_nodes(ctree)),
        'zone_and_keepout_definitions': compare('Zone/keepout definitions', zone_definitions(btree), zone_definitions(ctree)),
        'copper_layer_count': compare('Copper layer count', baseline.GetCopperLayerCount(), candidate.GetCopperLayerCount()),
    }
    for key in ['layers', 'setup', 'general']:
        checks[key] = compare(key, canonical(children(btree, key)), canonical(children(ctree, key)))
    return {'status': 'pass' if all(x['status'] == 'pass' for x in checks.values()) else 'fail',
            'checks': checks,
            'counts': {'baseline_footprints': len(bfp), 'candidate_footprints': len(cfp),
                       'baseline_pads': sum(len(x['pads']) for x in bfp.values()),
                       'candidate_pads': sum(len(x['pads']) for x in cfp.values()),
                       'baseline_copper_layers': baseline.GetCopperLayerCount(),
                       'candidate_copper_layers': candidate.GetCopperLayerCount(),
                       'baseline_zones': zone_counts(btree), 'candidate_zones': zone_counts(ctree)},
            'normalization': 'Whitespace, equivalent decimal spelling, and net-code renumbering only; native net names/pad connectivity remain exact. Top-level generation metadata is not an invariant. Board-zone definitions ignore only direct filled_polygon/fill_segments children and direct optional yes/no fill-state atoms within fill; a resulting empty fill node is omitted. All other zone/keepout fields and nested fill rules remain exact.'}


def route_profile(board):
    nets, narrow, bad_vias = {}, [], []
    copper = [x for x in board.GetEnabledLayers().CuStack()]
    for item in board.GetTracks():
        name = item.GetNetname()
        entry = nets.setdefault(name, {'segments': 0, 'arcs': 0, 'vias': 0, 'length_mm': 0.,
                                      'width_count': Counter(), 'width_profile': {}, 'layer_profile': {}, 'via_profile': Counter()})
        if isinstance(item, pcbnew.PCB_VIA):
            entry['vias'] += 1
            widths = {board.GetLayerName(layer): item.GetWidth(layer) for layer in copper if item.IsOnLayer(layer)}
            drill = item.GetDrillValue()
            annuli_twice = {layer: diameter - drill for layer, diameter in widths.items()}
            pair = [board.GetLayerName(item.TopLayer()), board.GetLayerName(item.BottomLayer())]
            profile = {'type': int(item.GetViaType()), 'layers': pair, 'drill_mm': mm(drill),
                       'diameters_mm': {k: mm(v) for k, v in widths.items()},
                       'annuli_mm': {k: mm(v) / 2 for k, v in annuli_twice.items()}}
            entry['via_profile'][stable(profile)] += 1
            if (drill != VIA_DRILL_IU or not widths or any(w != VIA_DIAMETER_IU for w in widths.values())
                    or any(a < 2 * MIN_ANNULUS_IU for a in annuli_twice.values())
                    or item.GetViaType() != pcbnew.VIATYPE_THROUGH):
                bad_vias.append({'uuid': uid(item), 'net': name, 'position_iu': xy(item), **profile})
        else:
            width, length = item.GetWidth(), mm(item.GetLength())
            layer = board.GetLayerName(item.GetLayer())
            key = f'{mm(width):.6f}'
            entry['arcs' if isinstance(item, pcbnew.PCB_ARC) else 'segments'] += 1
            entry['length_mm'] += length
            entry['width_count'][key] += 1
            wp = entry['width_profile'].setdefault(key, {'items': 0, 'length_mm': 0.})
            wp['items'] += 1
            wp['length_mm'] += length
            lp = entry['layer_profile'].setdefault(layer, {'items': 0, 'length_mm': 0., 'width_count': Counter(), 'width_profile': {}})
            lp['items'] += 1
            lp['length_mm'] += length
            lp['width_count'][key] += 1
            lwp = lp['width_profile'].setdefault(key, {'items': 0, 'length_mm': 0.})
            lwp['items'] += 1
            lwp['length_mm'] += length
            if width < MIN_TRACK_IU:
                narrow.append({'uuid': uid(item), 'net': name, 'width_mm': mm(width), 'layer': layer,
                               'start_iu': [item.GetStart().x, item.GetStart().y],
                               'end_iu': [item.GetEnd().x, item.GetEnd().y]})
    for entry in nets.values():
        entry['length_mm'] = round(entry['length_mm'], 9)
        entry['width_count'] = dict(sorted(entry['width_count'].items()))
        for wp in entry['width_profile'].values():
            wp['length_mm'] = round(wp['length_mm'], 9)
        entry['via_profile'] = [{'count': count, **json.loads(key)} for key, count in sorted(entry['via_profile'].items())]
        for lp in entry['layer_profile'].values():
            lp['length_mm'] = round(lp['length_mm'], 9)
            lp['width_count'] = dict(sorted(lp['width_count'].items()))
            for wp in lp['width_profile'].values():
                wp['length_mm'] = round(wp['length_mm'], 9)
    nets = dict(sorted(nets.items()))
    return {'per_net': nets, 'usb_profile': {k: v for k, v in nets.items() if 'usb' in k.casefold()},
            'totals': {'segments': sum(n['segments'] for n in nets.values()),
                       'arcs': sum(n['arcs'] for n in nets.values()), 'vias': sum(n['vias'] for n in nets.values()),
                       'route_length_mm': round(sum(n['length_mm'] for n in nets.values()), 9)},
            'subminimum_tracks': narrow, 'nonconforming_vias': bad_vias,
            'qualification': 'Lengths are sums of native track/arc geometry; via barrel length is excluded. USB substring selection, layer usage, and via counts are descriptive only, not signal-integrity, impedance, current, thermal, or fabrication qualification.'}



def power_width_preservation(baseline, candidate):
    """Coarse named-net floor only; never an ampacity certification."""
    def tracks(board):
        result = defaultdict(list)
        for t in board.GetTracks():
            if not isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() in POWER_NETS:
                result[t.GetNetname()].append(t)
        return result
    b, c = tracks(baseline), tracks(candidate)
    results, bad = {}, []
    for net in POWER_NETS:
        bt, ct = b.get(net, []), c.get(net, [])
        base_min = min((t.GetWidth() for t in bt), default=None)
        cand_min = min((t.GetWidth() for t in ct), default=None)
        floor = max(MIN_TRACK_IU, base_min or MIN_TRACK_IU)
        narrow = [{'uuid': uid(t), 'width_mm': mm(t.GetWidth()), 'layer': candidate.GetLayerName(t.GetLayer()),
                   'length_mm': mm(t.GetLength())} for t in ct if t.GetWidth() < floor]
        missing = bool(bt and not ct)
        status = 'fail' if narrow or missing else ('not_applicable' if not bt and not ct else 'pass')
        results[net] = {'status': status, 'baseline_minimum_mm': mm(base_min) if base_min is not None else None,
                        'candidate_minimum_mm': mm(cand_min) if cand_min is not None else None,
                        'required_floor_mm': mm(floor), 'baseline_items': len(bt), 'candidate_items': len(ct),
                        'candidate_missing_baseline_routes': missing, 'below_floor': narrow}
        if status == 'fail':
            bad.append(net)
    return {'status': 'fail' if bad else 'pass', 'failing_nets': bad, 'per_net': results,
            'policy': 'Each named power net must retain at least max(0.127 mm, its actual baseline minimum track/arc width). Missing all baseline routes also fails.',
            'limitation': 'An aggregate minimum-width floor cannot establish branch-specific ampacity or preserve high-current trunk topology. Review width-binned lengths and geometry separately; no current-capacity qualification is claimed.'}


def drill_paste_contacts(board):
    pads = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            for copper, paste in [(pcbnew.F_Cu, pcbnew.F_Paste), (pcbnew.B_Cu, pcbnew.B_Paste)]:
                if pad.IsOnLayer(copper) and pad.IsOnLayer(paste):
                    pads.append((fp, pad, copper, pad.GetEffectiveShape(copper)))
    contacts = []
    for via in board.GetTracks():
        if not isinstance(via, pcbnew.PCB_VIA):
            continue
        drill = via.GetDrillValue()
        if drill < 0:
            raise ValueError(f'Unresolved drill diameter on via {uid(via)}')
        # Native exact round drill shape, not an inflated rectangle or mask/paste aperture.
        # KiCad coordinates are integer nanometers. Odd diameter rounds up by 0.5 nm.
        circle = pcbnew.SHAPE_CIRCLE(via.GetPosition(), (drill + 1) // 2)
        for fp, pad, layer, shape in pads:
            if via.IsOnLayer(layer) and shape.Collide(circle, 0):
                contacts.append({'via_uuid': uid(via), 'via_position_iu': xy(via), 'drill_mm': mm(drill),
                                 'via_net': via.GetNetname(), 'footprint': fp.GetReference(),
                                 'pad': pad.GetNumber(), 'pad_uuid': uid(pad), 'pad_net': pad.GetNetname(),
                                 'layer': board.GetLayerName(layer),
                                 'same_net': via.GetNetCode() == pad.GetNetCode()})
    return sorted(contacts, key=stable)


def contact_summary(contacts):
    return {'contact_pairs': len(contacts), 'unique_vias': len({x['via_uuid'] for x in contacts}),
            'same_net_pairs': sum(x['same_net'] for x in contacts),
            'different_net_pairs': sum(not x['same_net'] for x in contacts)}


def added_records(baseline, candidate):
    extra = Counter(map(stable, candidate)) - Counter(map(stable, baseline))
    return [json.loads(key) for key, count in sorted(extra.items()) for _ in range(count)]


def project_suppressions(bpath, cpath):
    if not bpath or not cpath or not Path(bpath).is_file() or not Path(cpath).is_file():
        return {'status': 'incomplete', 'reason': 'Both baseline and candidate .kicad_pro files are required to compare suppressions.'}
    b, c = (json.loads(Path(p).read_text()) for p in [bpath, cpath])
    changes, blocking = [], []
    levels = {'error': 3, 'warning': 2, 'ignore': 0}
    for label, bs, cs in [('drc', b['board']['design_settings'], c['board']['design_settings']), ('erc', b['erc'], c['erc'])]:
        key = label + '_exclusions'
        for scope in (bs, cs):
            if not isinstance(scope.get(key), list) or not isinstance(scope.get('rule_severities'), dict):
                raise ValueError(f'Missing or invalid {label.upper()} exclusion/severity settings')
        before, after = bs.get(key, []), cs.get(key, [])
        if before != after:
            changes.append({'scope': label, 'field': key, 'before': before, 'after': after})
        for record in added_records(before, after):
            blocking.append({'scope': label, 'new_exclusion': record})
        before, after = bs.get('rule_severities', {}), cs.get('rule_severities', {})
        for rule in sorted(set(before) | set(after)):
            bv, cv = before.get(rule), after.get(rule)
            if bv != cv:
                record = {'scope': label, 'rule': rule, 'before': bv, 'after': cv}
                changes.append(record)
                if cv == 'ignore' or cv is None or (bv in levels and cv in levels and levels[cv] < levels[bv]):
                    blocking.append(record)
        if label == 'erc' and bs.get('pin_map') != cs.get('pin_map'):
            blocking.append({'scope': label, 'field': 'pin_map', 'reason': 'ERC pin interaction matrix changed; manual review required.'})
    return {'status': 'fail' if blocking else 'pass', 'changes': changes, 'new_or_relaxed_suppressions': blocking,
            'baseline': file_record(bpath), 'candidate': file_record(cpath)}


def native_report(path, kind):
    if not path:
        return None
    data = json.loads(Path(path).read_text())
    if data.get('$schema') != f'https://schemas.kicad.org/{kind}.v1.json':
        raise ValueError(f'{path} is not a native {kind.upper()} v1 JSON report')
    if not str(data.get('kicad_version', '')).startswith('10.'):
        raise ValueError(f'{path} is not a KiCad 10 report')
    required = ['violations', 'unconnected_items', 'schematic_parity'] if kind == 'drc' else ['sheets']
    for key in required:
        if not isinstance(data.get(key), list):
            raise ValueError(f'{path}: missing/invalid {key}')
    if kind == 'erc' and (not data['sheets'] or any(not isinstance(sheet.get('violations'), list) for sheet in data['sheets'])):
        raise ValueError(f'{path}: invalid sheet violations')
    return data


def report_metadata(data, path):
    return {**file_record(path), 'kicad_version': data.get('kicad_version'), 'source': data.get('source'),
            'date': data.get('date'), 'included_severities': data.get('included_severities'),
            'ignored_checks': data.get('ignored_checks')}


def violation_signature(v):
    # Ignore item ordering only. Include geometry/text as well as UUIDs, so a moved
    # or otherwise changed violation cannot silently count as inherited.
    copy = dict(v)
    copy['items'] = sorted(copy.get('items', []), key=stable)
    return copy


def drc_checks(bpath, cpath):
    b, c = native_report(bpath, 'drc'), native_report(cpath, 'drc')
    if c is None:
        return {'status': 'incomplete', 'reason': 'Candidate native DRC report was not supplied.'}
    items = c['violations'] + c['unconnected_items'] + c['schematic_parity']
    counts = Counter(v.get('severity', 'unknown') for v in items)
    unknown = sorted(set(counts) - {'error', 'warning', 'exclusion'})
    out = {'candidate': report_metadata(c, cpath), 'errors': counts['error'], 'warnings': counts['warning'],
           'exclusions': counts['exclusion'], 'opens': len(c['unconnected_items']),
           'schematic_parity': len(c['schematic_parity']),
           'violations_by_type': dict(sorted(Counter(v.get('type', 'unknown') for v in items).items())),
           'silkscreen_warnings': sum(v.get('severity') == 'warning' and v.get('type') in SILK_TYPES for v in items),
           'other_warnings': sum(v.get('severity') == 'warning' and v.get('type') not in SILK_TYPES for v in items)}
    if b is None:
        out.update(status='incomplete', reason='Baseline native DRC report is required to test for new violations.')
        return out
    out['baseline'] = report_metadata(b, bpath)
    before = b['violations'] + b['unconnected_items'] + b['schematic_parity']
    out['new_violations'] = added_records(list(map(violation_signature, before)), list(map(violation_signature, items)))
    out['new_ignored_checks'] = added_records(b.get('ignored_checks', []), c.get('ignored_checks', []))
    out['baseline_silkscreen_warnings'] = sum(v.get('severity') == 'warning' and v.get('type') in SILK_TYPES for v in before)
    out['severity_coverage_complete'] = all({'error', 'warning', 'exclusion'} <= set(d.get('included_severities', [])) for d in [b, c])
    if not out['severity_coverage_complete'] or unknown:
        out.update(status='incomplete', reason='Report severity coverage is incomplete or contains unknown severities.')
    else:
        out['status'] = 'pass' if not (out['errors'] or out['opens'] or out['schematic_parity'] or out['new_violations'] or out['new_ignored_checks']) else 'fail'
    out['warning_policy'] = 'Only unchanged baseline violations can remain. Silkscreen warnings and other inherited warnings are reported separately; a pass does not waive them.'
    return out


def erc_checks(path):
    data = native_report(path, 'erc')
    if data is None:
        return {'status': 'incomplete', 'reason': 'Native ERC report was not supplied.'}
    items = [v for sheet in data['sheets'] for v in sheet['violations']]
    counts = Counter(v.get('severity', 'unknown') for v in items)
    complete = {'error', 'warning', 'exclusion'} <= set(data.get('included_severities', [])) and not (set(counts) - {'error', 'warning', 'exclusion'})
    return {'status': ('fail' if counts['error'] else 'pass') if complete else 'incomplete',
            'report': report_metadata(data, path), 'errors': counts['error'], 'warnings': counts['warning'],
            'exclusions': counts['exclusion'], 'severity_coverage_complete': complete,
            'violations_by_type': dict(sorted(Counter(v.get('type', 'unknown') for v in items).items()))}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--baseline', required=True, type=Path)
    ap.add_argument('--candidate', required=True, type=Path)
    ap.add_argument('--baseline-project', type=Path, help='Default: baseline board path with .kicad_pro suffix')
    ap.add_argument('--candidate-project', type=Path, help='Default: candidate board path with .kicad_pro suffix')
    ap.add_argument('--baseline-drc', type=Path)
    ap.add_argument('--drc', type=Path, help='Candidate native pcb drc JSON, generated with --schematic-parity')
    ap.add_argument('--erc', type=Path, help='Candidate native sch erc JSON')
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    if args.output.resolve() in {p.resolve() for p in [args.baseline, args.candidate, args.baseline_project or args.baseline.with_suffix('.kicad_pro'), args.candidate_project or args.candidate.with_suffix('.kicad_pro'), args.baseline_drc, args.drc, args.erc, Path(__file__)] if p}:
        ap.error('--output must not overwrite any input')
    report = {'schema': 'nexus-reroute-validation.v1', 'created_utc': datetime.now(timezone.utc).isoformat(),
              'native': {'pcbnew_version': pcbnew.Version(), 'build_version': pcbnew.GetBuildVersion(),
                         'python': sys.version, 'pcbnew_module': pcbnew.__file__},
              'policy': {'minimum_track_mm': .127, 'via_diameter_mm': .45, 'via_drill_mm': .20,
                         'minimum_via_annulus_mm': .125, 'new_drill_pasted_smd_contacts_allowed': 0},
              'limitations': ['This is a reroute invariant/geometric regression gate, not manufacturing release approval.',
                             'Native DRC/ERC JSON is supplied evidence. JSON does not bind source contents cryptographically; run fresh native reports against these exact hashed sources.',
                             'An empty schematic_parity array alone cannot prove --schematic-parity was enabled; the DRC invocation must be recorded and reviewed.',
                             'Inherited drill/pasted-SMD contacts are counted explicitly; the gate forbids new contacts and does not certify inherited contacts as manufacturable.',
                             'No impedance, current capacity, thermal, EMC, USB compliance, component or fabrication qualification is performed.']}
    try:
        if not pcbnew.Version().startswith('10.'):
            raise ValueError('KiCad 10 pcbnew is required')
        report['inputs'] = {'baseline': file_record(args.baseline), 'candidate': file_record(args.candidate),
                            'validator': file_record(Path(__file__))}
        btree, ctree = [parse_sexpr(p.read_text()) for p in [args.baseline, args.candidate]]
        if btree[0] != 'kicad_pcb' or ctree[0] != 'kicad_pcb':
            raise ValueError('Both inputs must be KiCad PCB files')
        baseline, candidate = [pcbnew.LoadBoard(str(p)) for p in [args.baseline, args.candidate]]
        report['invariants'] = invariant_checks(baseline, candidate, btree, ctree)
        bp, cp = route_profile(baseline), route_profile(candidate)
        report['routes'] = {'baseline': bp, 'candidate': cp}
        report['power_width_preservation'] = power_width_preservation(baseline, candidate)
        bc, cc = drill_paste_contacts(baseline), drill_paste_contacts(candidate)
        new_contacts = added_records(bc, cc)
        report['drill_pasted_smd'] = {'status': 'fail' if new_contacts else 'pass',
            'method': 'Native PAD.GetEffectiveShape(copper_layer).Collide(SHAPE_CIRCLE(via_position, drill_radius), 0), for SMD pads with matching copper and paste layers; includes same-net and different-net contact, including boundary touch.',
            'baseline_summary': contact_summary(bc), 'candidate_summary': contact_summary(cc),
            'baseline_contacts': bc, 'candidate_contacts': cc, 'new_contacts': new_contacts,
            'resolved_contacts': added_records(cc, bc)}
        report['manufacturing_geometry_gate'] = {
            'status': 'fail' if cp['subminimum_tracks'] or cp['nonconforming_vias'] or new_contacts else 'pass',
            'subminimum_tracks': len(cp['subminimum_tracks']), 'nonconforming_vias': len(cp['nonconforming_vias']),
            'new_drill_pasted_smd_contact_pairs': len(new_contacts)}
        report['project_suppressions'] = project_suppressions(args.baseline_project or args.baseline.with_suffix('.kicad_pro'),
                                                             args.candidate_project or args.candidate.with_suffix('.kicad_pro'))
        report['native_drc'] = drc_checks(args.baseline_drc, args.drc)
        report['native_erc'] = erc_checks(args.erc)
        # Detect input changes during this run; do not claim a moving target was verified.
        for label, path in [('baseline', args.baseline), ('candidate', args.candidate)]:
            if file_record(path)['sha256'] != report['inputs'][label]['sha256']:
                raise ValueError(f'{label} board changed during validation')
        gates = ['invariants', 'manufacturing_geometry_gate', 'power_width_preservation', 'project_suppressions', 'native_drc', 'native_erc']
        statuses = {g: report[g]['status'] for g in gates}
        report['overall'] = {'status': 'fail' if 'fail' in statuses.values() else ('incomplete' if 'incomplete' in statuses.values() else 'pass'),
                             'gates': statuses}
    except Exception as exc:
        report['overall'] = {'status': 'incomplete', 'error': f'{type(exc).__name__}: {exc}'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'output': str(args.output.resolve()), 'overall': report['overall'],
                      'manufacturing_geometry_gate': report.get('manufacturing_geometry_gate'),
                      'candidate_drill_paste_contacts': report.get('drill_pasted_smd', {}).get('candidate_summary')}, indent=2))
    return {'pass': 0, 'fail': 1, 'incomplete': 2}[report['overall']['status']]


if __name__ == '__main__':
    raise SystemExit(main())
