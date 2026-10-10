import pathlib,json,sys
H=pathlib.Path(__file__).resolve().parent
exec((H/'ser1_complete17_geometry.py').read_text())
from shapely.ops import polygonize,unary_union
from shapely.geometry import box
base=list(m.OBJECTS);checks=[]
for i,r in enumerate(plan['routes']):
 net='SERVO1_SOURCE'if r['net']=='SERVO1_MCU'and r.get('branch')==0 else r['net'];m.HALF=r.get('width',.127)/2;obs=q.obs(net,r['layer'])[0]
 if net=='SERVO1_SOURCE':obs=[o for o in obs if o['object']!='U12.1']
 rr=m.check(LineString(r['points']),obs,True);checks.append(dict(kind='track',index=i,net=r['net'],minimum=rr[0],violations=[v for v in rr if v['extra_clearance_mm']<m.ERROR]))
for i,v in enumerate(plan['vias']):
 idx=len(base)-len(plan['vias'])+i;m.OBJECTS=[r for j,r in enumerate(base)if j!=idx];net='SERVO1_SOURCE'if v['net']=='SERVO1_MCU'and v.get('branch')==0 else v['net'];m.HALF=.0635;rr=m.check(Point(v['xy']),q.obs(net,'F.Cu')[1],True);checks.append(dict(kind='via',index=i,net=v['net'],minimum=rr[0],violations=[r for r in rr if r['extra_clearance_mm']<m.ERROR]))
m.OBJECTS=base;m.HALF=0
for o,c,mask,d in base:
 if o.get('ref')!='R50':continue
 rr=m.check(c['F.Cu'],q.obs(o['net'],'F.Cu')[0],True);bad=[r for r in rr if r['extra_clearance_mm']<m.ERROR]
 mb=[]
 for oo,cc,mm,dd in base:
  if dd is None:continue
  for l,g in mask.items():
   margin=g.distance(dd)-.20
   if margin<m.ERROR:mb.append(dict(uuid=oo['uuid'],face=l,extra_clearance_mm=margin))
 checks.append(dict(kind='pad',key=o['key'],minimum=rr[0],violations=bad,mask_drill_violations=mb))
cy={}
for f in n['footprints']:
 if f['side']!='F.Cu':continue
 ls=[]
 for g in f['graphics']:
  if g['layer']!='F.Courtyard':continue
  if g['shape']=='Rect':ls.append(box(*g['start'],*g['end']).boundary)
  elif g['shape']=='Line':ls.append(LineString([g['start'],g['end']]))
 cy[f['ref']]=unary_union(list(polygonize(ls)))
r50=affinity.translate(cy['R50'],.25,0);cb=[k for k,g in cy.items()if k!='R50'and r50.intersection(g).area>1e-10]
out=dict(source_board_sha256=m.EXPECTED,bindings=bindings,checks=checks,courtyard_conflicts=cb,passed=not cb and all(not r['violations']and not r.get('mask_drill_violations')for r in checks),scope='Exact fixed geometry screen against native SBUS17 and future flash/LED. Native saved refill, support and actual pad cuts pending.')
(H/'servo1-complete-geometry17.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(passed=out['passed'],courtyard=cb,failed=[dict(kind=r['kind'],index=r.get('index'),key=r.get('key'),violations=[(v['object'],v['net'],v['extra_clearance_mm'])for v in r['violations']],mask=r.get('mask_drill_violations'))for r in checks if r['violations']or r.get('mask_drill_violations')])))
