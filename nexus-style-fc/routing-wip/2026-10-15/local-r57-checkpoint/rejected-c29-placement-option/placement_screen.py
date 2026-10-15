"""Read-only analytic screen of one hypothetical C29 move. Writes report only."""
import sys, math, json, hashlib, copy
from pathlib import Path
sys.path.insert(0,'/workspace/shared/nexus-usb-stack-review/r55-donors')
import source_context as c
from static_clearance import point_seg, seg_seg
OUT=Path('/workspace/shared/nexus-usb-stack-review/r55-c29-option/placement-screen.json')
def rnd(x):
 if isinstance(x,float): return round(x,12)
 if isinstance(x,list) or isinstance(x,tuple):return [rnd(v) for v in x]
 if isinstance(x,dict):return {k:rnd(v) for k,v in x.items()}
 return x
def inside(pt,poly):
 if len(poly)<3:return False
 x,y=pt; hit=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if point_seg(pt,a,b)[0]<1e-10:return True
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:hit=not hit
 return hit
def edges(poly):return list(zip(poly,poly[1:]+poly[:1]))
def poly_dist(a,b):
 if any(inside(p,b) for p in a) or any(inside(p,a) for p in b):return 0.
 return min(seg_seg(p,q,r,s) for p,q in edges(a) for r,s in edges(b))
def transform(pt,at,ang):
 q=math.radians(ang);co=math.cos(q);si=math.sin(q)
 return [at[0]+co*pt[0]+si*pt[1],at[1]-si*pt[0]+co*pt[1]]
def corners(cx,cy,ang,at):return [transform(p,at,ang) for p in [(-cx,-cy),(cx,-cy),(cx,cy),(-cx,cy)]]
def shape(p):
 sx,sy=p['size'];kind=p['shape']
 if kind=='rect':r=0.
 elif kind=='roundrect':r=min(sx,sy)*p['roundrect_rratio']
 elif kind=='circle':r=sx/2
 elif kind=='oval':r=min(sx,sy)/2
 else:raise ValueError('Unsupported relevant pad shape '+kind)
 return corners(sx/2-r,sy/2-r,p['rotation'],p['at']),r
raw={c.val(p,'uuid'):p for f in c.allc(c.b,'footprint') for p in c.allc(f,'pad')}
pads=copy.deepcopy(c.pads)
for p in pads:
 if p['shape']=='roundrect':p['roundrect_rratio']=float(c.val(raw[p['uuid']],'roundrect_rratio'))
original=[p for p in pads if p['ref']=='C29'];moved=copy.deepcopy(original)
for p in moved:p['at'][0]-=.211
fixed=[p for p in pads if p['ref']!='C29' and ('F.Cu' in p['layers'] or '*.Cu' in p['layers'])]
tracks=[t for t in c.tracks if t['layer']=='F.Cu']
vias=[v for v in c.vias if 'F.Cu' in v['layers']]
fills=[]
for z in c.allc(c.b,'zone'):
 for i,f in enumerate(c.allc(z,'filled_polygon')):
  if c.val(f,'layer')=='F.Cu':fills.append(dict(net=c.val(z,'net'),uuid=c.val(z,'uuid'),index=i,poly=[list(map(float,p[1:3])) for p in c.one(f,'pts')[1:]]))
def info(p):
 poly,r=shape(p);xs=[v[0] for v in poly];ys=[v[1] for v in poly]
 return dict(pin=p['pin'],net=p['net'],at=p['at'],uuid=p['uuid'],local_size_mm=p['size'],rotation_deg=p['rotation'],roundrect_rratio=p['roundrect_rratio'],rounding_radius_mm=r,core_rectangle_vertices_mm=poly,copper_bbox_mm=[min(xs)-r,min(ys)-r,max(xs)+r,max(ys)+r])
def check(ps):
 out=[];counts={}
 for p in ps:
  a,r=shape(p)
  for q in fixed+([ps[1]] if p['pin']=='1' else [ps[0]]):
   b,s=shape(q);g=poly_dist(a,b)-r-s
   out.append(dict(pad='C29.'+p['pin'],net=p['net'],other_kind='pad',other_ref=q['ref']+'.'+q['pin'],other_net=q['net'],other_uuid=q['uuid'],gap_mm=g,same_net=p['net']==q['net'],required_mm=.2 if q['type']=='np_thru_hole' else .127))
  for t in tracks:
   g=poly_dist(a,[t['start'],t['end']])-r-t['width']/2
   out.append(dict(pad='C29.'+p['pin'],net=p['net'],other_kind='track',other_net=t['net'],other_uuid=t['uuid'],gap_mm=g,same_net=p['net']==t['net'],required_mm=.127,start=t['start'],end=t['end'],width_mm=t['width']))
  for v in vias:
   g=poly_dist(a,[v['at']])-r-v['diameter']/2
   out.append(dict(pad='C29.'+p['pin'],net=p['net'],other_kind='via',other_net=v['net'],other_uuid=v['uuid'],gap_mm=g,same_net=p['net']==v['net'],required_mm=.127,at=v['at'],diameter_mm=v['diameter']))
  for z in fills:
   g=poly_dist(a,z['poly'])-r
   out.append(dict(pad='C29.'+p['pin'],net=p['net'],other_kind='stored_filled_polygon',other_net=z['net'],other_uuid=z['uuid'],filled_polygon_index=z['index'],gap_mm=g,same_net=p['net']==z['net'],required_mm=.127))
 return sorted(out,key=lambda r:r['gap_mm'])
baseline=check(original);proposed=check(moved)
lookup={(o['pad'],o['other_kind'],o['other_uuid'],o.get('filled_polygon_index')):o for o in baseline}
for o in proposed:
 old=lookup[(o['pad'],o['other_kind'],o['other_uuid'],o.get('filled_polygon_index'))]
 o['baseline_gap_mm']=old['gap_mm'];o['new_violation']=o['gap_mm']<o['required_mm']-1e-9 and old['gap_mm']>=old['required_mm']-1e-9
# Actual source courtyard contours, including circular courtyards. No 3D/body inference.
courts=[]
for f in c.allc(c.b,'footprint'):
 if c.val(f,'layer')!='F.Cu':continue
 ref=next(p[2] for p in c.allc(f,'property') if p[1]=='Reference')
 at=c.vec(f,'at');av=c.one(f,'at');ang=float(av[3]) if len(av)>3 else 0
 rects=[];lines=[];circles=[]
 for g in f:
  if not isinstance(g,list) or c.val(g,'layer')!='F.CrtYd':continue
  if g[0]=='fp_rect':
   (x1,y1),(x2,y2)=c.vec(g,'start'),c.vec(g,'end');rects.append([transform(p,at,ang) for p in [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]])
  elif g[0]=='fp_line':lines.append([transform(c.vec(g,'start'),at,ang),transform(c.vec(g,'end'),at,ang)])
  elif g[0]=='fp_circle':circles.append((transform(c.vec(g,'center'),at,ang),math.dist(c.vec(g,'center'),c.vec(g,'end'))))
  else:raise ValueError('Unsupported courtyard '+g[0])
 while lines:
  a,b=lines.pop();poly=[a,b]
  while math.dist(poly[-1],poly[0])>1e-8:
   ix=next((i for i,(a,b) in enumerate(lines) if math.dist(a,poly[-1])<1e-8 or math.dist(b,poly[-1])<1e-8),None)
   if ix is None:raise ValueError('Unclosed courtyard '+ref)
   a,b=lines.pop(ix);poly.append(b if math.dist(a,poly[-1])<1e-8 else a)
  rects.append(poly[:-1])
 courts.append(dict(ref=ref,polygons=rects,circles=circles))
cc=next(v for v in courts if v['ref']=='C29');oldpoly=cc['polygons'][0];newpoly=[[x-.211,y] for x,y in oldpoly]
court_results=[]
for q in courts:
 if q['ref']=='C29':continue
 distances=[poly_dist(newpoly,p) for p in q['polygons']]
 olddist=[poly_dist(oldpoly,p) for p in q['polygons']]
 for center,rad in q['circles']:
  distances.append(max(0,poly_dist(newpoly,[center])-rad));olddist.append(max(0,poly_dist(oldpoly,[center])-rad))
 if not distances:continue
 court_results.append(dict(ref=q['ref'],gap_mm=min(distances),baseline_gap_mm=min(olddist),overlap_or_touch=min(distances)<1e-9,geometry=q))
court_results.sort(key=lambda x:x['gap_mm'])
roles=[]
for f in c.allc(c.b,'footprint'):
 ref=next(p[2] for p in c.allc(f,'property') if p[1]=='Reference')
 if ref not in ['C29','R16','R17','U1']:continue
 roles.append(dict(ref=ref,value=next(p[2] for p in c.allc(f,'property') if p[1]=='Value'),description=next((p[2] for p in c.allc(f,'property') if p[1]=='Description'),''),pads=[{'pin':p[1],'net':c.val(p,'net'),'uuid':c.val(p,'uuid')} for p in c.allc(f,'pad') if ref!='U1' or c.val(p,'net')=='VX_SENSE']))
viol=[v for v in proposed if not v['same_net'] and v['gap_mm']<v['required_mm']-1e-9]
report=dict(source=str(c.S),sha256=c.H,read_only=True,hypothesis=dict(ref='C29',old_center_mm=[111.39,121.55],new_center_mm=[111.179,121.55],translation_mm=[-.211,0],rotation_deg=90,all_other_objects_fixed=True),method=dict(name='Exact Minkowski-core clearance for rectangle/roundrect/oval/circle pads; analytic segment capsules, via circles, and stored filled-polygon edges',caveats=['Nonpositive rounded-core separation proves copper overlap; reported negative magnitude is not a complete polygon penetration metric.','Stored filled polygons are baseline copper and were not regenerated for the hypothetical move; future refill could change these zone results.','Source courtyards checked as actual line/rect/circle contours, not line-stroke envelopes or inferred 3D bodies.','Static geometry only: no placement change, native KiCad, DRC, refill, connectivity or reachability claim.'],copper_clearance_mm=.127,hole_clearance_mm=.2),new_pad_geometry=[info(p) for p in moved],baseline_pad_geometry=[info(p) for p in original],corridor=dict(c29_pad_right_x_mm=111.489,j5_pad6_left_x_mm=112.18,gap_mm=.691,pair_outer_width_mm=.437,side_clearances_total_mm=.254,residual_margin_mm=0),screen_counts=dict(fixed_front_or_through_pads=len(fixed),front_tracks=len(tracks),front_vias=len(vias),front_stored_filled_polygons=len(fills),front_courtyard_footprints=len(court_results)),foreign_net_conflicts=viol,nearest_foreign_objects=[v for v in proposed if not v['same_net'] and v['gap_mm']<.8],same_net_contacts=[v for v in proposed if v['same_net'] and v['gap_mm']<=0],courtyard=dict(new_vertices_mm=newpoly,new_bbox_mm=[110.719,120.64,111.639,122.46],stroke_mm=.05,conflicts=[v for v in court_results if v['overlap_or_touch']],nearest=court_results[:5]),source_adc_role=roles,source_adc_role_caveat='PCB net names and source properties only, no assertion of end-to-end connectivity or ADC performance.',decision='REJECT proposed C29-only west move: creates VX_SENSE-to-GND track overlap and upper GND via copper clearance violation; nominal east corridor has zero residual slack.',max_west_move_from_upper_via_clearance_mm=.137142,corridor_shortfall_at_that_max_west_move_mm=.073858)
limit_track=next(t for t in tracks if t['uuid']=='a4eae8e6-eaf8-44a3-ba6e-de8237538fcb')
factor=abs(limit_track['end'][1]-limit_track['start'][1])/math.dist(limit_track['start'],limit_track['end'])
oldgap=next(v['baseline_gap_mm'] for v in viol if v['other_uuid']==limit_track['uuid'])
limit=(oldgap-.127)/factor
report['stronger_fixed_track_limit']=dict(track_uuid=limit_track['uuid'],baseline_c29_pad2_clearance_mm=oldgap,west_translation_to_0_127_clearance_mm=limit,limiting_region='Nearest pad-core corner and segment interior; roundrect radius 0.14 mm included',corridor_gap_at_that_limit_mm=.480+limit,corridor_shortfall_at_that_limit_mm=.211-limit)
report['schematic_role_evidence']=dict(source=str(c.S.with_suffix('.kicad_sch')),source_sha256=hashlib.sha256(c.S.with_suffix('.kicad_sch').read_bytes()).hexdigest(),annotation='ADC divider filters | VX_SENSE -> U1.9; 5V_SENSE -> U1.10',u1_pin9_name='PC1',role='R16 52.3k VX to VX_SENSE, R17 10k VX_SENSE to GND, C29 100nF VX_SENSE to GND; source-net role, not connectivity certification')
hole_conflicts=[]
for p in moved:
 a,r=shape(p);old=next(o for o in original if o['pin']==p['pin']);oa,orr=shape(old)
 for v in vias:
  if v['net']==p['net']:continue
  g=poly_dist(a,[v['at']])-r-v['drill']/2
  if g<.2-1e-9:
   hole_conflicts.append(dict(pad='C29.'+p['pin'],net=p['net'],via_uuid=v['uuid'],via_net=v['net'],via_at_mm=v['at'],drill_mm=v['drill'],gap_mm=g,baseline_gap_mm=poly_dist(oa,[v['at']])-orr-v['drill']/2,required_mm=.2))
report['foreign_via_drill_to_copper_conflicts']=hole_conflicts
OUT.write_text(json.dumps(rnd(report),indent=2)+'\n')
assert hashlib.sha256(c.S.read_bytes()).hexdigest()==c.H
print(json.dumps(rnd(dict(report=str(OUT),conflicts=viol,courtyard_nearest=court_results[:3],same_net_contacts=[v for v in proposed if v['same_net'] and v['gap_mm']<=0])),indent=2))
