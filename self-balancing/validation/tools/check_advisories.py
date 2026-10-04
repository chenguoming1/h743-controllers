#!/usr/bin/python3
"""Uncapped foreign mask-aperture and foreign via-hole clearance census.

Mask polygons are freshly exported from the exact candidate into an explicitly
diagnostic directory. They are not a fabrication release. All same-net contacts
and escapes are separated from foreign copper. Every via hole is compared to
all other-net copper objects on every copper layer, including filled zones.
"""
import argparse,collections,hashlib,json,math,os,pathlib,re,subprocess
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=pathlib.Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();assert sha(a.candidate)==a.sha256
mm=lambda v:round(p.ToMM(v),6);xy=lambda v:[mm(v.x),mm(v.y)];uid=lambda q:q.m_Uuid.AsString();b=p.LoadBoard(str(a.candidate));layers=list(b.GetEnabledLayers().CuStack());tracks=list(b.GetTracks());pads=[pd for f in b.GetFootprints() for pd in f.Pads()];vias=[v for v in tracks if isinstance(v,p.PCB_VIA)];O=a.out/'diagnostic-mask-exports';O.mkdir(exist_ok=True)
cli=['sh',str(pathlib.Path(__file__).resolve().parent/'frozen-tools/kicad_cli.sh')];subprocess.run(cli+['pcb','export','gerbers','--layers','F.Mask,B.Mask','--precision','6','--subtract-soldermask','--use-drill-file-origin','--output',str(O),str(a.candidate)],check=True,stdout=subprocess.DEVNULL)
def box(s):
 bb=s.BBox();return bb.GetLeft(),bb.GetTop(),bb.GetRight(),bb.GetBottom()
def distance(a,b):return math.hypot(max(0,a[0]-b[2],b[0]-a[2]),max(0,a[1]-b[3],b[1]-a[3]))
def regions(path):
 polygons=[];pts=None
 for line in path.read_text().splitlines():
  if line=='G36*':assert pts is None;pts=[]
  elif line=='G37*':
   assert pts and pts[0]==pts[-1];poly=p.SHAPE_POLY_SET();poly.NewOutline()
   for x,y in pts[:-1]:poly.Append(x,38000000-y)
   polygons.append(poly);pts=None
  elif pts is not None:
   m=re.fullmatch(r'X(-?\d+)Y(-?\d+)D0([12])\*',line)
   if m:pts.append((int(m[1]),int(m[2])))
   else:assert line=='G01*','Unexpected mask primitive: '+line
 assert pts is None;return polygons
errors=[];masks={}
for mask,cu,ext in [(p.F_Mask,p.F_Cu,'gts'),(p.B_Mask,p.B_Cu,'gbs')]:
 paths=list(O.glob('*.'+ext));assert len(paths)==1;path=paths[0];polys=regions(path);ps=[pd for pd in pads if pd.IsOnLayer(mask)];objs=[(t,t.GetEffectiveShape(cu)) for t in tracks if t.IsOnLayer(cu)];objs=[(t,s,box(s)) for t,s in objs];near=[];samecontacts=[];foreignoverlap=[];unmatched=[];owners_report=[];minimum=None
 for index,poly in enumerate(polys):
  pb=box(poly);owners=[pd for pd in ps if poly.Collide(pd.GetPosition(),0)];nets={pd.GetNetCode() for pd in owners};labels=sorted({pd.GetParentFootprint().GetReference()+'.'+pd.GetNumber() for pd in owners});owners_report.append({'index':index,'owners':labels,'native_bounds_mm':[mm(v) for v in pb]})
  if not owners:unmatched.append(index)
  for t,shape,tb in objs:
   if distance(pb,tb)>=200000:continue
   gap=poly.GetClearance(shape)
   if gap>=200000:continue
   same=t.GetNetCode() in nets;row={'region':index,'owners':labels,'object_uuid':uid(t),'object_net':t.GetNetname(),'kind':t.GetClass(),'gap_mm':mm(gap),'same_net':same}
   if not gap:
    if same:samecontacts.append(row)
    else:foreignoverlap.append(row)
   else:near.append(row)
   if not same and (minimum is None or gap<minimum):minimum=gap
 bad=[r for r in near if not r['same_net'] and r['gap_mm']<.1]
 if unmatched:errors.append(b.GetLayerName(mask)+' unassigned mask openings')
 if foreignoverlap:errors.append(b.GetLayerName(mask)+' foreign copper overlaps mask opening')
 if bad:errors.append(b.GetLayerName(mask)+' foreign copper closer than .100mm to mask opening')
 masks[b.GetLayerName(mask)]={'mask_sha256':sha(path),'polygon_count':len(polys),'native_mask_pad_count':len(ps),'unassigned_regions':unmatched,'minimum_foreign_clearance_mm':mm(minimum) if minimum is not None else None,'foreign_overlaps':foreignoverlap,'foreign_below_0100mm':bad,'same_net_contacts':samecontacts,'same_net_disjoint_below_0100mm':[r for r in near if r['same_net'] and r['gap_mm']<.1],'all_pairs_below_0200mm':sorted(near,key=lambda r:r['gap_mm']),'regions':owners_report}
objects=[]
for t in tracks+pads:
 for l in layers:
  if t.IsOnLayer(l):
   s=t.GetEffectiveShape(l);objects.append((uid(t),t.GetNetCode(),t.GetNetname(),t.GetClass(),l,s,box(s)))
for z in b.Zones():
 if z.GetIsRuleArea():continue
 for l in layers:
  if z.IsOnLayer(l) and z.HasFilledPolysForLayer(l):
   s=z.GetFilledPolysList(l);objects.append((uid(z),z.GetNetCode(),z.GetNetname(),'filled_zone',l,s,box(s)))
near=[];minimum=None;tested=0
for v in vias:
 hole=v.GetEffectiveHoleShape();vb=box(hole)
 for identity,netcode,net,kind,layer,s,bounds in objects:
  if netcode==v.GetNetCode() or not v.IsOnLayer(layer) or distance(vb,bounds)>=300000:continue
  gap=hole.GetClearance(s);tested+=1
  if minimum is None or gap<minimum:minimum=gap
  if gap<300000:near.append({'via_uuid':uid(v),'via_net':v.GetNetname(),'via_xy_mm':xy(v.GetPosition()),'drill_mm':mm(v.GetDrillValue()),'other_uuid':identity,'other_net':net,'other_kind':kind,'layer':b.GetLayerName(layer),'hole_edge_to_copper_gap_mm':mm(gap)})
bad=[r for r in near if r['hole_edge_to_copper_gap_mm']<.2]
if bad:errors.append('Foreign copper closer than .200mm to via hole')
assert sha(a.candidate)==a.sha256,'Source changed during census'
report={'status':'PASS UNCAPPED MASK/VIA-HOLE CENSUS' if not errors else 'NOT PASSED','native_sha256':a.sha256,'errors':errors,'limits_mm':{'foreign_mask_to_trace_or_via':.100,'foreign_via_hole_to_copper':.200},'mask_results':masks,'via_holes':{'via_count':len(vias),'tested_near_pairs':tested,'minimum_gap_mm':mm(minimum) if minimum is not None else None,'foreign_below_0200mm':bad,'all_pairs_below_0300mm':sorted(near,key=lambda r:r['hole_edge_to_copper_gap_mm'])},'method':__doc__,'limits':'CAD manufacturing geometry only; supplier advisory classifiers and physical process capability are distinct.'}
(a.out/'advisory-clearance-census.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'errors':errors,'masks':{name:{'minimum_foreign_gap_mm':r['minimum_foreign_clearance_mm'],'foreign_overlaps':len(r['foreign_overlaps']),'foreign_below_0100mm':len(r['foreign_below_0100mm']),'same_net_disjoint_below_0100mm':len(r['same_net_disjoint_below_0100mm'])} for name,r in masks.items()},'minimum_foreign_via_hole_gap_mm':report['via_holes']['minimum_gap_mm']},indent=2));raise SystemExit(bool(errors))
