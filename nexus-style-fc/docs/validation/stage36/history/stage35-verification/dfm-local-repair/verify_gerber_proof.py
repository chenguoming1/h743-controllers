#!/usr/bin/env python3
"""Read-only, source-bound local Gerber proof. Writes only the proof JSON beside this file.

Uses only Python standard library. Strictly parses this KiCad export's modal
apertures, absolute 4.6 mm coordinates, strokes/arcs, flashes, polarity and regions.
Region edges are not mistaken for aperture-width track strokes. No CAD execution.
"""
from pathlib import Path
from decimal import Decimal
import datetime
import hashlib
import json
import math
import re

HERE = Path(__file__).resolve().parent
STAGE = HERE.parent.parent
GERBERS = STAGE / 'manufacturing/nexus-style-fc/gerbers'
PCB = STAGE / 'hardware/nexus-style-fc.kicad_pcb'
EXPECTED_PCB_SHA = 'bf9a10563839b18071dedd1c4a71af60c25ac19e94f392adb1917955b1f4e95d'
SCALE = 1_000_000
ORIGIN = (Decimal('99.95'), Decimal('133.15'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def gpoint(p):
    x, y = map(lambda v: Decimal(str(v)), p)
    return (int((x - ORIGIN[0]) * SCALE), int((ORIGIN[1] - y) * SCALE))

def mm(p):
    return [v / SCALE for v in p]

def parse_gerber(p):
    ap = {}; strokes = []; flashes = []; region_edges = []; arcs = []
    current = None; aperture = None; selection_line = None
    interpolation = None; region = False; polarity = None; macro = False
    saw_format = saw_units = saw_end = False
    lines = p.read_text().splitlines()
    for lineno, line in enumerate(lines, 1):
        if macro:
            macro = not line.endswith('%')
            continue
        if line.startswith('%AM'):
            macro = not line.endswith('*%')
            continue
        if not line or line.startswith('G04 '):
            continue
        if line == '%FSLAX46Y46*%': saw_format = True; continue
        if line == '%MOMM*%': saw_units = True; continue
        if line in ('%LPD*%', '%LPC*%'):
            polarity = 'dark' if line == '%LPD*%' else 'clear'; continue
        match = re.fullmatch(r'%ADD(\d+)([^,*]+)(?:,([^*]+))?\*%', line)
        if match:
            code, shape, params = match.groups()
            ap[int(code)] = {'code': int(code), 'shape': shape,
                'parameters_mm': [float(v) for v in params.split('X')] if params else [],
                'declaration_line': lineno, 'declaration': line}
            continue
        if line in ('G01*', 'G02*', 'G03*'):
            interpolation = int(line[1:3]); continue
        if line == 'G75*': continue
        if line == 'G36*': assert not region; region = True; continue
        if line == 'G37*': assert region; region = False; continue
        if line == 'M02*': saw_end = True; continue
        match = re.fullmatch(r'D(\d+)\*', line)
        if match:
            aperture = int(match.group(1)); assert aperture in ap
            selection_line = lineno; continue
        match = re.fullmatch(r'(?:X(-?\d+))?(?:Y(-?\d+))?(?:I(-?\d+))?(?:J(-?\d+))?D0([123])\*', line)
        if match:
            assert saw_format and saw_units and polarity and aperture is not None
            x, y, i, j, operation = match.groups()
            assert x is not None or y is not None
            target = (int(x) if x is not None else current[0],
                      int(y) if y is not None else current[1])
            item = {'line': lineno, 'raw': line, 'aperture': aperture,
                    'aperture_selection_line': selection_line, 'polarity': polarity}
            if operation == '1':
                assert current is not None and interpolation is not None
                item.update(start=current, end=target, interpolation=interpolation)
                if region:
                    region_edges.append(item)
                elif interpolation == 1:
                    assert i is None and j is None
                    strokes.append(item)
                else:
                    item.update(center_offset=(int(i or 0), int(j or 0)))
                    arcs.append(item)
            elif operation == '3':
                assert not region
                item['at'] = target; flashes.append(item)
            current = target
            continue
        raise AssertionError(f'Unsupported Gerber token {p.name}:{lineno}: {line}')
    assert saw_format and saw_units and saw_end and not macro and not region
    return {'path': p, 'apertures': ap, 'strokes': strokes, 'flashes': flashes,
            'arcs': arcs, 'region_edges': region_edges, 'lines': lines}

def matching_strokes(g, a, b):
    a, b = gpoint(a), gpoint(b)
    return [s for s in g['strokes'] if (s['start'], s['end']) in ((a,b),(b,a))]

def evidence(g, item):
    result = {**item, 'file': g['path'].name,
              'aperture_definition': g['apertures'][item['aperture']]}
    for key in ('start','end','at','center_offset'):
        if key in result:
            result[key+'_gerber_mm'] = mm(result.pop(key))
    return result

def distance_point_segment(p, a, b):
    ab = [b[i]-a[i] for i in (0,1)]
    t = max(0., min(1., sum((p[i]-a[i])*ab[i] for i in (0,1)) / sum(v*v for v in ab)))
    q = [a[i]+t*ab[i] for i in (0,1)]
    return math.dist(p,q), list(p), q

def cross(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

def distance_segments(a,b,c,d):
    # These disjoint target segments are analytically handled by endpoint projection.
    assert not (cross(a,b,c)*cross(a,b,d) < 0 and cross(c,d,a)*cross(c,d,b) < 0)
    candidates = [distance_point_segment(a,c,d), distance_point_segment(b,c,d)]
    for p in (c,d):
        distance, pp, qq = distance_point_segment(p,a,b)
        candidates.append((distance,qq,pp))
    return min(candidates, key=lambda v:v[0])

def main():
    assert sha(PCB) == EXPECTED_PCB_SHA, 'Source board hash does not match accepted stage35'
    pcb_text = PCB.read_text()
    assert re.search(r'\(aux_axis_origin\s+99\.95\s+133\.15\)', pcb_text)
    before = {p.name:sha(p) for p in sorted(GERBERS.iterdir()) if p.is_file()}
    parsed = {p.name:parse_gerber(p) for p in sorted(GERBERS.iterdir())
              if p.suffix not in ('.drl','.gbrjob')}
    bottom = parsed['nexus-style-fc-B_Cu.gbl']
    front = parsed['nexus-style-fc-F_Cu.gtl']
    path = [(103.55,110.15),(103.55,110.65),(102.6,111.675)]
    path_evidence = []
    for a,b in zip(path,path[1:]):
        found = matching_strokes(bottom,a,b)
        assert len(found) == 1, (a,b,found)
        stroke = found[0]
        aperture = bottom['apertures'][stroke['aperture']]
        assert aperture['shape']=='C' and aperture['parameters_mm']==[0.25]
        assert stroke['polarity']=='dark'
        path_evidence.append(evidence(bottom,stroke))
    pad_evidence=[]
    for filename in ('nexus-style-fc-B_Cu.gbl','nexus-style-fc-B_Mask.gbs','nexus-style-fc-B_Paste.gbp'):
        g = parsed[filename]
        found = [f for f in g['flashes'] if f['at']==gpoint((103.05,110.15))]
        assert len(found)==1
        aperture = g['apertures'][found[0]['aperture']]
        assert aperture['shape']=='O' and aperture['parameters_mm']==[0.28,0.85]
        assert found[0]['polarity']=='dark'
        pad_evidence.append(evidence(g,found[0]))
    oval_center=mm(gpoint((103.05,110.15)))
    oval_radius=0.28/2
    oval_half_spine=(0.85-0.28)/2
    oval_a=[oval_center[0],oval_center[1]-oval_half_spine]
    oval_b=[oval_center[0],oval_center[1]+oval_half_spine]
    gaps=[]
    for a,b in zip(path,path[1:]):
        distance,trace_point,oval_point=distance_segments(mm(gpoint(a)),mm(gpoint(b)),oval_a,oval_b)
        gaps.append({'pcb_segment_mm':[a,b], 'centerline_distance_mm':distance,
                     'trace_closest_gerber_mm':trace_point, 'oval_spine_closest_gerber_mm':oval_point,
                     'edge_gap_mm':distance-oval_radius-0.25/2})
    min_gap=min(g['edge_gap_mm'] for g in gaps)
    assert abs(min_gap-0.235)<1e-12
    absent=[]
    def absence(g,a,b,reason):
        found=matching_strokes(g,a,b)
        assert not found, (reason,found)
        absent.append({'description':reason,'file':g['path'].name,'pcb_endpoints_mm':[a,b],
                       'gerber_endpoints_mm':[mm(gpoint(a)),mm(gpoint(b))],
                       'matching_linear_stroke_count_either_direction_any_aperture':len(found)})
    absence(bottom,path[0],path[-1],'Former direct SW_5V diagonal')
    dead=[(121.320142,110.390037),(119.266,110.395),(118.984415,110.156542),
          (118.894,110.024),(118.879858,108.918253)]
    for index,(a,b) in enumerate(zip(dead,dead[1:]),1):
        absence(front,a,b,f'Front dead sensor branch segment {index}')
    absence(bottom,(120.85,109.9),dead[0],'Bottom dead sensor branch segment')
    via_absence=[]
    for filename,g in parsed.items():
        if '_Cu.' not in filename: continue
        found=[f for f in g['flashes'] if f['at']==gpoint(dead[0])]
        assert not found,(filename,found)
        via_absence.append({'file':filename,'flash_count_any_aperture_at_exact_center':len(found)})
    drill=GERBERS/'nexus-style-fc-PTH.drl'
    tools={}; hits=[]; tool=None
    for lineno,line in enumerate(drill.read_text().splitlines(),1):
        m=re.fullmatch(r'T(\d+)C([0-9.]+)',line)
        if m: tools[int(m[1])]=float(m[2]);continue
        m=re.fullmatch(r'T(\d+)',line)
        if m: tool=int(m[1]);continue
        m=re.fullmatch(r'X(-?[0-9.]+)Y(-?[0-9.]+)',line)
        if m:
            assert tool in tools
            hits.append({'line':lineno,'tool':tool,'diameter_mm':tools[tool],
                         'at_gerber_mm':[float(m[1]),float(m[2])]})
    assert hits and '; FORMAT={-:-/ absolute / metric / decimal}' in drill.read_text()
    via_center=mm(gpoint(dead[0]))
    nearest=min(hits,key=lambda h:math.dist(h['at_gerber_mm'],via_center))
    nearest_distance=math.dist(nearest['at_gerber_mm'],via_center)
    assert nearest_distance>math.sqrt(2)*0.0005, 'A drill coincides within 0.001 mm output rounding'
    after={p.name:sha(p) for p in sorted(GERBERS.iterdir()) if p.is_file()}
    assert before==after and sha(PCB)==EXPECTED_PCB_SHA, 'Source or exports changed during proof'
    report={
        'status':'PASS','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_board':{'path':str(PCB),'sha256':EXPECTED_PCB_SHA,'auxiliary_origin_pcb_mm':[99.95,133.15]},
        'coordinate_convention':'Gerber x = PCB x - 99.95; Gerber y = 133.15 - PCB y; absolute mm, 4.6',
        'method':'Strict modal Gerber primitive/aperture parser; exact integer-coordinate matches, both segment directions; region edges excluded from track-stroke inventory. Names U5.3/SW_5V/sensor describe task targets; geometric assertions use exact coordinates and apertures, not labels.',
        'replacement_path':{'pcb_points_mm':path,'width_mm':0.25,'evidence':path_evidence},
        'u5_pin3_aperture':{'pcb_center_mm':[103.05,110.15],'shape':'vertical oval','size_mm':[0.28,0.85],
                            'copper_mask_paste_geometry_identical':True,'evidence':pad_evidence},
        'whole_new_path_gap':{'method':'Minimum segment-to-oval-spine distance minus 0.125 mm track radius and 0.14 mm oval radius; includes full segments and circular endcaps.',
                              'oval_spine_gerber_mm':[oval_a,oval_b],'per_segment':gaps,
                              'minimum_edge_gap_mm':min_gap,'applies_to':['B.Cu U5.3','B.Mask U5.3 opening','B.Paste U5.3 aperture']},
        'removed_stroke_checks':absent,
        'removed_through_via':{'pcb_center_mm':dead[0],'former_copper_diameter_mm':0.45,'former_drill_mm':0.20,
                               'gerber_center_mm':via_center,'all_copper_layers':via_absence,
                               'pth_drill_absence':{'file':drill.name,'nearest_drill':nearest,
                                                   'nearest_distance_mm':nearest_distance,'rounding_allowance_mm':math.sqrt(2)*0.0005}},
        'manufacturing_sha256':before,
        'parsed_inventories':{name:{'apertures':len(g['apertures']),'linear_strokes':len(g['strokes']),
                                   'arc_strokes':len(g['arcs']),'flashes':len(g['flashes']),
                                   'region_edges':len(g['region_edges'])} for name,g in parsed.items()},
        'input_hashes_unchanged_after_verification':True,
        'verifier_sha256':sha(Path(__file__)),
        'limits':['This is the bounded manufacturing-geometry proof, not a new fabrication/assembly acceptance or electrical qualification.',
                  'No refill, native SaveBoard, DRC, export, source edit or external upload performed. Native 0-error/0-open/0-parity acceptance is supplied context, not rerun here.']}
    out=HERE/'gerber-proof.json'
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'proof':str(out),'min_gap_mm':min_gap,
                      'removed_strokes_proved':len(absent),'via_copper_layers_checked':len(via_absence),
                      'nearest_drill_distance_mm':nearest_distance},indent=2))

if __name__=='__main__':
    main()
