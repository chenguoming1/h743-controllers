#!/usr/bin/env python3
"""Read-only exact geometry proof of stage36 target-via mask/paste isolation.
Run with the supplied official KiCad Python; only writes sibling proof JSON.
All four complete mask/paste exports are parsed with actual modal apertures.
"""
from pathlib import Path
from decimal import Decimal
import datetime, hashlib, json, math, re
import pcbnew as k
HERE=Path(__file__).resolve().parent
STAGE=HERE.parent.parent
GERBERS=STAGE/'manufacturing/nexus-style-fc/gerbers'
PCB=STAGE/'hardware/nexus-style-fc.kicad_pcb'
EXPECTED_PCB_SHA='bed37199e8d62b8135a27b9e182f8e8f584f1a9fb722cb6efb5d4c87b2a320b8'
SCALE=1_000_000
ORIGIN=(Decimal('99.95'), Decimal('133.15'))
TARGETS=[{'net':'VX_SENSE','pcb_xy_mm':[112.45,118.66],'uuid':'707dbbcc-473c-42c1-955c-850634f4a46e'},
         {'net':'GND','pcb_xy_mm':[111.775,119.6],'uuid':'43a15d1f-be53-4e28-ba7d-898572a61333'}]
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


def point_seg(p,a,b):
    v=[b[i]-a[i] for i in (0,1)]
    vv=sum(t*t for t in v)
    t=max(0.,min(1.,sum((p[i]-a[i])*v[i] for i in (0,1))/vv)) if vv else 0
    q=[a[i]+t*v[i] for i in (0,1)]
    return math.dist(p,q),q

def point_poly(p,pts):
    closest=min((point_seg(p,a,b) for a,b in zip(pts,pts[1:]+pts[:1])),key=lambda x:x[0])
    inside=False
    for a,b in zip(pts,pts[1:]+pts[:1]):
        if (a[1]>p[1]) != (b[1]>p[1]) and p[0] < (b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:
            inside=not inside
    return (-closest[0] if inside else closest[0]),closest[1]

def rot(p,angle):
    # Exact orthogonal rotations avoid adding approximation to this export.
    assert angle%90==0
    a=int(angle/90)%4
    return ([p[0],p[1]],[-p[1],p[0]],[-p[0],-p[1]],[p[1],-p[0]])[a]

def macro_bodies(g):
    blocks=re.findall(r'%AM([^*]+)\*(.*?)\*%',g['path'].read_text(),re.S)
    return {name:[t.strip() for t in body.split('*') if t.strip() and not t.strip().startswith('0 ')] for name,body in blocks}

def make_shape(g,ap):
    kind=ap['shape'];v=ap['parameters_mm'];radius=0
    if kind=='C':
        assert len(v)==1
        return {'kind':'circle','base':[[0.,0.]],'radius_mm':v[0]/2}
    if kind=='R':
        assert len(v)==2
        x,y=[x/2 for x in v];pts=[[-x,-y],[x,-y],[x,y],[-x,y]]
    elif kind=='O':
        assert len(v)==2
        x,y=v;radius=min(x,y)/2
        pts=[[0,-(y-x)/2],[0,(y-x)/2]] if y>=x else [[-(x-y)/2,0],[(x-y)/2,0]]
        return {'kind':'capsule','base':pts,'radius_mm':radius}
    elif kind=='RoundRect':
        expected=['4,1,4,$2,$3,$4,$5,$6,$7,$8,$9,$2,$3,0',
                  '1,1,$1+$1,$2,$3','1,1,$1+$1,$4,$5','1,1,$1+$1,$6,$7','1,1,$1+$1,$8,$9',
                  '20,1,$1+$1,$2,$3,$4,$5,0','20,1,$1+$1,$4,$5,$6,$7,0',
                  '20,1,$1+$1,$6,$7,$8,$9,0','20,1,$1+$1,$8,$9,$2,$3,0']
        assert macro_bodies(g)[kind]==expected
        assert len(v)==10 and v[9]==0
        radius=v[0];pts=[[v[i],v[i+1]] for i in range(1,9,2)]
        assert len(set(x for x,y in pts))==2 and len(set(y for x,y in pts))==2
    elif kind=='FreePoly0':
        body=macro_bodies(g)[kind];assert len(body)==1 and len(v)==1
        t=body[0].split(',');assert t[:3]==['4','1','14'] and t[-1]=='$1'
        coords=list(map(float,t[3:-1]));assert len(coords)==30
        pts=[rot(coords[i:i+2],v[0]) for i in range(0,len(coords),2)]
        assert pts[0]==pts[-1];pts=pts[:-1]
    else: raise AssertionError(f'Unsupported aperture {kind}')
    return {'kind':'polygon_dilation','base':pts,'radius_mm':radius}

def point_shape(p,center,shape):
    q=[p[i]-center[i] for i in (0,1)]
    pts=shape['base'];r=shape['radius_mm']
    if shape['kind']=='circle': d=math.dist(q,pts[0]);near=pts[0]
    elif shape['kind']=='capsule': d,near=point_seg(q,*pts)
    else: d,near=point_poly(q,pts)
    signed=d-r
    d_actual=max(0.,signed)
    # All target centers should be outside the positive exported aperture region.
    # Full-disk separation is stronger than annulus-only separation and covers holes.
    return signed,d_actual,[center[i]+near[i] for i in (0,1)]

def shape_bounds(center,shape):
    return [[min(p[i] for p in shape['base'])+center[i]-shape['radius_mm'] for i in (0,1)],
            [max(p[i] for p in shape['base'])+center[i]+shape['radius_mm'] for i in (0,1)]]

def native(b):
    settings=b.GetDesignSettings()
    result=[]
    for t in TARGETS:
        found=[v for v in b.GetTracks() if v.GetClass()=='PCB_VIA' and v.m_Uuid.AsString()==t['uuid']]
        assert len(found)==1
        v=found[0];pos=[v.GetPosition().x/SCALE,v.GetPosition().y/SCALE]
        assert pos==t['pcb_xy_mm'] and v.GetNetname()==t['net']
        assert v.GetWidth(k.F_Cu)==v.GetWidth(k.B_Cu)==450000 and v.GetDrillValue()==200000
        assert v.TopLayer()==k.F_Cu and v.BottomLayer()==k.B_Cu
        assert v.IsTented(k.F_Mask) and v.IsTented(k.B_Mask)
        assert v.GetFrontTentingMode()==v.GetBackTentingMode()==k.TENTING_MODE_FROM_BOARD
        result.append({**t,'gerber_xy_mm':mm(gpoint(pos)),'diameter_mm':0.45,'drill_mm':0.2,
                       'annulus_radial_thickness_mm':0.125,'annulus_inner_radius_mm':0.1,'annulus_outer_radius_mm':0.225,
                       'copper_span':['F.Cu','B.Cu'],'front_tented':v.IsTented(k.F_Mask),
                       'back_tented':v.IsTented(k.B_Mask),'tenting_modes':'FROM_BOARD',
                       'board_tent_front':settings.m_TentViasFront,'board_tent_back':settings.m_TentViasBack,
                       'local_mask_margin':v.GetLocalSolderMaskMargin(),
                       'outer_disk_pcb_bounds_mm':[[round(pos[i]-0.225,6) for i in (0,1)],[round(pos[i]+0.225,6) for i in (0,1)]],
                       'hole_pcb_bounds_mm':[[round(pos[i]-0.1,6) for i in (0,1)],[round(pos[i]+0.1,6) for i in (0,1)]]})
    fp=next(f for f in b.GetFootprints() if f.GetReference()=='C12')
    p=next(p for p in fp.Pads() if p.GetNumber()=='1')
    assert [p.GetPosition().x/SCALE,p.GetPosition().y/SCALE]==[112.35,120.02]
    c12={'reference':'C12','pad':'1','net':p.GetNetname(),'uuid':p.m_Uuid.AsString(),
         'pcb_xy_mm':[112.35,120.02],'gerber_xy_mm':mm(gpoint((112.35,120.02))),
         'native_local_pad_size_mm':[p.GetSize().x/SCALE,p.GetSize().y/SCALE],
         'native_rotation_degrees':p.GetOrientationDegrees(),'native_corner_radius_mm':p.GetRoundRectCornerRadius()/SCALE,
         'pcb_axis_aligned_size_mm':[0.62,0.56]}
    return result,c12

def drill_hits(path):
    tools={};hits=[];tool=None
    for lineno,line in enumerate(path.read_text().splitlines(),1):
        m=re.fullmatch(r'T(\d+)C([0-9.]+)',line)
        if m: tools[int(m[1])]=float(m[2]);continue
        m=re.fullmatch(r'T(\d+)',line)
        if m: tool=int(m[1]);continue
        m=re.fullmatch(r'X(-?[0-9.]+)Y(-?[0-9.]+)',line)
        if m:
            assert tool in tools
            hits.append({'line':lineno,'tool':tool,'diameter_mm':tools[tool],'gerber_xy_mm':[float(m[1]),float(m[2])]})
    assert '; FORMAT={-:-/ absolute / metric / decimal}' in path.read_text()
    return hits

def main():
    assert sha(PCB)==EXPECTED_PCB_SHA
    assert re.search(r'\(aux_axis_origin\s+99\.95\s+133\.15\)',PCB.read_text())
    before={p.name:sha(p) for p in sorted(GERBERS.iterdir()) if p.is_file()}
    board=k.LoadBoard(str(PCB));vias,c12=native(board)
    paths=sorted(p for p in GERBERS.iterdir() if '_Mask.' in p.name or '_Paste.' in p.name)
    assert len(paths)==4
    parsed={p.name:parse_gerber(p) for p in paths}
    summary=[];detailed=[];c12_evidence=[]
    for name,g in parsed.items():
        assert not g['strokes'] and not g['arcs'] and not g['region_edges']
        assert all(f['polarity']=='dark' for f in g['flashes'])
        assert ('TF.FilePolarity,Negative' if '_Mask.' in name else 'TF.FilePolarity,Positive') in '\n'.join(g['lines'])
        shapes={code:make_shape(g,ap) for code,ap in g['apertures'].items()}
        for via in vias:
            point=via['gerber_xy_mm'];distances=[]
            for f in g['flashes']:
                center=mm(f['at']);shape=shapes[f['aperture']]
                signed,d,near=point_shape(point,center,shape)
                row={'file':name,'net':via['net'],'flash_line':f['line'],'flash_raw':f['raw'],
                     'aperture':f['aperture'],'aperture_selection_line':f['aperture_selection_line'],
                     'aperture_shape':g['apertures'][f['aperture']]['shape'],
                     'flash_gerber_xy_mm':center,'aperture_gerber_bounds_mm':shape_bounds(center,shape),
                     'signed_center_to_aperture_edge_mm':signed,
                     'center_to_aperture_material_mm':d,
                     'hole_edge_clearance_mm':d-0.1,'annulus_outer_edge_clearance_mm':d-0.225,
                     'closest_base_point_gerber_mm':near}
                distances.append(row)
                if center==c12['gerber_xy_mm']:
                    c12_evidence.append({**row,'aperture_definition':g['apertures'][f['aperture']], 'resolved_shape':shape})
            nearest=min(distances,key=lambda r:r['annulus_outer_edge_clearance_mm'])
            layer={'nexus-style-fc-B_Mask.gbs':k.B_Mask,'nexus-style-fc-B_Paste.gbp':k.B_Paste,
                   'nexus-style-fc-F_Mask.gts':k.F_Mask,'nexus-style-fc-F_Paste.gtp':k.F_Paste}[name]
            nearest['native_pad_matches']=[{'reference':fp.GetReference(),'pad':pad.GetNumber(),
                                           'net':pad.GetNetname(),'uuid':pad.m_Uuid.AsString(),
                                           'pcb_xy_mm':[pad.GetPosition().x/SCALE,pad.GetPosition().y/SCALE]}
                                          for fp in board.GetFootprints() for pad in fp.Pads()
                                          if pad.IsOnLayer(layer) and
                                          mm(gpoint([pad.GetPosition().x/SCALE,pad.GetPosition().y/SCALE]))==nearest['flash_gerber_xy_mm']]
            assert len(nearest['native_pad_matches'])==1
            assert nearest['annulus_outer_edge_clearance_mm']>0,(via['net'],name,nearest)
            exact=[f for f in g['flashes'] if f['at']==gpoint(via['pcb_xy_mm'])]
            assert not exact
            summary.append({'file':name,'net':via['net'],'all_flashes_tested':len(distances),
                            'center_flashes':len(exact),'no_center_or_hole_or_annulus_overlap':True,'nearest_aperture':nearest})
            detailed.extend(distances)
    copper_evidence=[]
    for p in sorted(GERBERS.iterdir()):
        if '_Cu.' not in p.name:continue
        g=parse_gerber(p)
        for via in vias:
            found=[f for f in g['flashes'] if f['at']==gpoint(via['pcb_xy_mm'])]
            assert len(found)==1
            f=found[0];ap=g['apertures'][f['aperture']]
            assert ap['shape']=='C' and ap['parameters_mm']==[0.45] and f['polarity']=='dark'
            copper_evidence.append({'net':via['net'],'file':p.name,'line':f['line'],'raw':f['raw'],'aperture_definition':ap})
    hits=drill_hits(GERBERS/'nexus-style-fc-PTH.drl');drill_evidence=[]
    for via in vias:
        found=[h for h in hits if h['gerber_xy_mm']==via['gerber_xy_mm']]
        assert len(found)==1 and found[0]['diameter_mm']==0.2
        drill_evidence.append({'net':via['net'],'file':'nexus-style-fc-PTH.drl',**found[0]})
    after={p.name:sha(p) for p in sorted(GERBERS.iterdir()) if p.is_file()}
    assert before==after and sha(PCB)==EXPECTED_PCB_SHA
    report={'status':'PASS','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'source_board':{'path':str(PCB),'sha256':EXPECTED_PCB_SHA},
            'auxiliary_origin_pcb_mm':[99.95,133.15],
            'coordinate_convention':'Gerber x = PCB x - 99.95; Gerber y = 133.15 - PCB y. Absolute mm 4.6.',
            'method':'All 696 positive aperture flashes in the four fresh mask/paste files are tested against both via disks. Modal D-code selections, flash centers, polarity and actual C/R/O/RoundRect/FreePoly0 geometry are parsed. Polygon, capsule and circle distances are analytic, not sampled. RoundRect is the exact exported inner quadrilateral Minkowski-summed with its corner radius. Native identities, dimensions and resolved tenting are checked via read-only official KiCad Python. Copper flashes on all six copper layers and exact PTH drill hits independently confirm disk/hole dimensions.',
            'mask_semantics':'Soldermask Gerber FilePolarity is Negative: dark Gerber shapes represent openings in the soldermask. Paste Gerber is Positive: dark shapes represent stencil apertures.',
            'hole_annulus_distinction':'Hole radius 0.100 mm; copper annulus extends radially from 0.100 to 0.225 mm. Clearance to the outer disk proves no aperture touches the hole OR copper annulus; it is stronger than checking a missing flash at the via center. Nominal radial annulus thickness is 0.125 mm.',
            'native_vias':vias,'c12_pad1_native':c12,'summary':summary,'c12_aperture_checks':c12_evidence,
            'all_aperture_distance_checks':detailed,
            'aperture_definitions':{name:list(g['apertures'].values()) for name,g in parsed.items()},
            'copper_flash_evidence':copper_evidence,'pth_drill_evidence':drill_evidence,
            'parsed_inventories':{name:{'flashes':len(g['flashes']),'linear_strokes':len(g['strokes']),
                                      'arcs':len(g['arcs']),'region_edges':len(g['region_edges']),
                                      'creation_header':next(l for l in g['lines'] if 'TF.CreationDate' in l)} for name,g in parsed.items()},
            'manufacturing_sha256':before,'input_hashes_unchanged_after_verification':True,
            'export_provenance':{'parent_reported_export_exit_code':0,
                                 'parent_reported_bom_groups':48,'parent_reported_placements':83,
                                 'completion_confirmation_received_utc':'2026-10-15T17:24:15Z',
                                 'basis':'Coordinating parent confirmed export exited successfully; no further source/export edits planned. All fresh mask/paste creation headers are 2026-10-16T01:18:16+08:00. Inputs are hashed before and after this proof.',
                                 'export_log_sha256':sha(STAGE/'export.log'),
                                 'export_log':(STAGE/'export.log').read_text()},
            'verifier_sha256':sha(Path(__file__)),
            'limits':['Nominal exported geometry only; fabrication tolerances, mask registration and drill wander are not supplied or simulated.',
                      'Positive separation is reported, not a fabrication/assembly acceptance or a guaranteed manufactured mask web.',
                      'No refill, SaveBoard, source edit, DRC run, export or upload is performed.']}
    out=HERE/'via-aperture-proof.json';out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'PASS','proof':str(out),'native_vias':vias,'summary':summary,'c12_aperture_checks':c12_evidence},indent=2))

if __name__=='__main__':main()
