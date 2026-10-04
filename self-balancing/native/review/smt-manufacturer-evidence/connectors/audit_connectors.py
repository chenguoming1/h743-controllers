#!/usr/bin/python3
"""Read-only P3 connector geometry extraction and optional-shape clearance study."""
import os
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pathlib, json, hashlib, csv, math, datetime
import pcbnew as p
D=pathlib.Path('/workspace/shared/storm32-redesign/controller-r3s-green')
O=pathlib.Path(__file__).parent
S=D/'controller.kicad_pcb'
EXPECTED='0850991d8aacd22138487804c24eefbae634a21ba218c18196f13fad795c3696'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(S)==EXPECTED
b=p.LoadBoard(str(S));mm=lambda x:round(p.ToMM(x),6);xy=lambda v:[mm(v.x),mm(v.y)]
bounds=lambda pts:[min(q[0] for q in pts),min(q[1] for q in pts),max(q[0] for q in pts),max(q[1] for q in pts)]
refs={f.GetReference():f for f in b.GetFootprints() if f.GetReference() in ['J2','J3','J4','J5']}
rec={}
for r,f in refs.items():
    pads=[]; shapes=[]
    for q in f.Pads():
        x,y=xy(q.GetPosition());sx,sy=xy(q.GetSize());a=q.GetOrientationDegrees()%360
        assert abs(a%90)<1e-6
        if a in [90,270]:sx,sy=sy,sx
        pads.append({'number':q.GetNumber(),'net':q.GetNetname(),'native_xy_mm':[x,y],'size_local_mm':xy(q.GetSize()),'angle_deg':a,'bbox_mm':[round(x-sx/2,6),round(y-sy/2,6),round(x+sx/2,6),round(y+sy/2,6)],'drill_local_mm':xy(q.GetDrillSize()),'attribute':int(q.GetAttribute()),'layers':[b.GetLayerName(l) for l in q.GetLayerSet().Seq()],'has_paste':q.IsOnLayer(p.F_Paste) or q.IsOnLayer(p.B_Paste)})
    for s in f.GraphicalItems():
        if s.GetClass()=='PCB_SHAPE':shapes.append({'layer':b.GetLayerName(s.GetLayer()),'shape':s.GetShapeStr(),'start_mm':xy(s.GetStart()),'end_mm':xy(s.GetEnd())})
    boxes={}
    for layer in ['F.Fab','B.Fab','F.Courtyard','B.Courtyard']:
        pts=[s[k] for s in shapes if s['layer']==layer for k in ['start_mm','end_mm']]
        if pts:boxes[layer]=bounds(pts)
    body=boxes.get('B.Fab',boxes.get('F.Fab'))
    record={'native_anchor_mm':xy(f.GetPosition()),'native_angle_deg':f.GetOrientationDegrees()%360,'side':'Bottom' if f.GetLayer()==p.B_Cu else 'Top','footprint':str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),'pads':pads,'graphics':shapes,'graphic_bounds_mm':boxes,'native_body_center_mm':[round((body[0]+body[2])/2,6),round((body[1]+body[3])/2,6)]}
    if r!='J2':
        assert all(q['attribute']==p.PAD_ATTRIB_SMD and q['drill_local_mm']==[0,0] for q in pads)
        inset=body[0] if r in ['J3','J4'] else 38-body[2]
        padinset=min(q['bbox_mm'][0] for q in pads) if r in ['J3','J4'] else 38-max(q['bbox_mm'][2] for q in pads)
        record.update(nominal_body_edge_inset_mm=round(inset,6),nearest_copper_edge_inset_mm=round(padinset,6),body_overhang_mm=0.0,courtyard_overhang_mm=.08)
        assert abs(inset-.625)<1e-6 and abs(padinset-.425)<1e-6
    rec[r]=record
cpl={}
for name in ['JLC_BOM.csv','JLC_CPL.csv','JLC_CPL_NATIVE_AUDIT.csv']:
    rows=list(csv.DictReader((D/'release/assembly'/name).open()))
    cpl[name]=[q for q in rows if any(r in q.values() for r in refs)]
# Optional front-slot copper change, represented as a new mathematical capsule.
# The loaded board and all native objects are untouched.
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def distance(a,z,cap=3.0):
    hi=p.FromMM(cap)
    if not a.Collide(z,hi): return None
    lo=0
    if a.Collide(z,0): return 0
    while hi-lo>100:
        mid=(hi+lo)//2
        if a.Collide(z,mid):hi=mid
        else:lo=mid
    return mm(hi)
study=[]
allpads=[q for f in b.GetFootprints() for q in f.Pads()]
tracks=list(b.GetTracks())
copperlayers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu]
for y in [15.68,24.32]:
    geom=p.SHAPE_SEGMENT(v(35.0,y),v(35.8,y),p.FromMM(1.0))
    near=[]
    for layer in copperlayers:
        for q in allpads+tracks:
            if not q.IsOnLayer(layer) or q.GetNetname()=='GND':continue
            dist=distance(geom,q.GetEffectiveShape(layer))
            if dist is None:continue
            desc=q.GetParentFootprint().GetReference()+'.'+q.GetNumber() if isinstance(q,p.PAD) else q.GetClass()
            near.append({'item':desc,'net':q.GetNetname(),'layer':b.GetLayerName(layer),'gap_mm':dist,'xy_mm':xy(q.GetPosition())})
        for z in b.Zones():
            if not z.IsOnLayer(layer) or z.GetNetname()=='GND':continue
            shape=z.GetEffectiveShape(layer)
            dist=distance(geom,shape)
            if dist is not None:near.append({'item':'ZONE','net':z.GetNetname(),'layer':b.GetLayerName(layer),'gap_mm':dist})
    study.append({'center_native_mm':[35.4,y],'optional_drill_local_mm':[.6,1.4],'optional_copper_local_mm':[1.0,1.8],'copper_rightmost_x_mm':36.3,'edge_clearance_mm':1.7,'nearest_foreign_copper':sorted(near,key=lambda x:x['gap_mm'])[:10]})
inputs=[S,D/'release/assembly/JLC_BOM.csv',D/'release/assembly/JLC_CPL.csv',D/'release/assembly/JLC_CPL_NATIVE_AUDIT.csv',D.parent/'research/controller-r3s-stage05-assembly-audit/sources/typec.pdf',D.parent/'research/controller-r3s-manufacturing-sources/jst-sh.pdf',D.parent/'research/controller-r3s-manufacturing-sources/lian-xin-c7527621.pdf']
result={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_sha256':EXPECTED,'kicad_version':p.Version(),'coordinate_contract':'Native X right, Y down; PCB origin 0,38; raw CPL X=native X,Y=38-native Y; no bottom mirror. Supplier-corrected CPL is separate.','connectors':rec,'release_rows':cpl,'optional_front_slot_shape_study':study,'inputs_sha256':{str(x):sha(x) for x in inputs},'board_unchanged':sha(S)==EXPECTED}
(O/'native-connectors.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'board_unchanged':result['board_unchanged'],'optional_front_slot_shape_study':study},indent=2))
