import inspect_access as a
from shapely.geometry import Point
from shapely.ops import nearest_points
import json,hashlib
m=a.m;old=m.OBJECTS[:];new=json.loads((a.HERE/'candidate01/f722-heli.native.json').read_text());drc=json.loads((a.HERE.parents[1]/'candidate48/owner-drc.json').read_text());uids={it['uuid']for v in drc['unconnected_items']for it in v['items']if ' of U1 on 'in it['description']};keys=sorted({o['key']for o,c,ms,d in old if o['uuid']in uids});out={'source_board_sha256':m.EXPECTED,'board_sha256':new['board_sha256'],'pads':{},'reserved_RPM_portal_mm':[15.1,9.59]}
for stage in ['source','candidate']:
 if stage=='candidate':m.OBJECTS=[(o,{l:m.geom(ps)for l,ps in o['copper'].items()},{l:m.geom(q['polygons'])for l,q in o.get('mask',{}).items()}if o.get('smd')else{},m.geom(o['drill']['outside'])if o.get('drill')else None)for o in new['objects']]
 for key in keys:
  o=a.KEY[key];t,v,s=a.obs(o['net'],'B.Cu');free=m.OUTLINE.difference(a.solid(t));pt=Point(o['xy']);comp=next(p for p in a.parts(free)if p.covers(pt));legal=comp.difference(a.solid(v,bounds=comp.bounds));regs=[r for r in a.parts(legal)if r.area>.00002];regs.sort(key=lambda r:pt.distance(r));r=dict(net=o['net'],component_area_mm2=comp.area,component_bounds_mm=comp.bounds,legal_via_component_count=len(regs),legal_via_area_mm2=sum(r.area for r in regs),nearest_vias=[dict(xy=list(nearest_points(pt,g)[1].coords[0]),distance_mm=pt.distance(g),area_mm2=g.area,bounds_mm=g.bounds)for g in regs[:3]])
  out['pads'].setdefault(key,{})[stage]=r;print(stage,key,r['legal_via_component_count'],flush=True)
newly=[]
for key,row in out['pads'].items():
 if key=='U1.15':continue
 if row['source']['legal_via_component_count']>0 and row['candidate']['legal_via_component_count']==0:newly.append(key)
out.update(newly_sealed_unresolved_pad_via_access=newly,passed=not newly,limits=['Read-only continuous geometry screen at original width, clearance, drill/mask and hole rules, with 0.0001mm extra polygon margin.','Legal via access is necessary, not proof of a complete trunk or AC return. Source-existing pockets without legal via access remain explicit.','No peer proposal is adopted into this source48-only candidate.'])
assert not newly,newly
(a.HERE/'candidate01/remaining-access.json').write_text(json.dumps(out,indent=2)+'\n')
