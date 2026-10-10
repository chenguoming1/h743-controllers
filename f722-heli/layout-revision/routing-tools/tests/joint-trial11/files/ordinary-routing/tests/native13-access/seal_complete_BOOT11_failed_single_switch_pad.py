"""Actual BOOT terminals and full finite peer audit, no native qualification claim."""
import hashlib,json,signal,time
from pathlib import Path
import composite_native11_complete_BOOT as g
from shapely.geometry import Point,LineString
start=time.monotonic();signal.alarm(15);s=g.s
out=dict(source=g.binding(),native_candidate=False,pending_B_divider=True,pending_native_refill_reference_power=True,checks=[])
for r in g.BOOT_ROUTES:
 s.OBJECTS=g.BASE;s.HALF=r['width']/2
 ch=s.check(LineString(r['points']),s.obstacles(r['net'],r['layer'])[0],True)
 out['checks'].append(dict(name=r['name'],width=r['width'],passed=all(x['pass_with_polygon_error']for x in ch),failures=[x for x in ch if not x['pass_with_polygon_error']]))
for v in g.BOOT_VIAS:
 s.OBJECTS=[q for q in g.BASE if q[0]['uuid']!=v['name']];s.HALF=.0635
 ch=s.check(Point(v['xy']),s.obstacles(v['net'],'B.Cu')[1],True)
 out['checks'].append(dict(name=v['name'],passed=all(x['pass_with_polygon_error']for x in ch),failures=[x for x in ch if not x['pass_with_polygon_error']]))
items=[q for q in g.BASE if q[0]['net']=='BOOT0'];parents=list(range(len(items)));edges=[]
def find(i):
 while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
 return i
for i,(o,c,m,d)in enumerate(items):
 for j in range(i):
  oo,cc,_,_=items[j];layers=[l for l in c if l in cc and c[l].intersects(cc[l])]
  if layers:parents[find(i)]=find(j);edges.append(dict(a=o['uuid'],b=oo['uuid'],layers=layers))
terminals={k:[i for i,q in enumerate(items)if q[0].get('key')==k]for k in ['U1.60','R2.1','SW1.2']}
assert all(len(v)==1 for v in terminals.values()),terminals
groups={k:find(v[0])for k,v in terminals.items()}
out.update(actual_terminal_groups=groups,contact_edges=edges,complete_actual_BOOT_tree=len(set(groups.values()))==1,all_finite_pass=all(x['passed']for x in out['checks']),constructed_B_duplicate_omitted=g.BOOT['routes'][0],all_signal_layers_ordinary=all(r['layer']in ['F.Cu','In2.Cu','In3.Cu','B.Cu']for r in g.BOOT_ROUTES),new_route_length_mm=sum(r['length_mm']for r in g.BOOT_ROUTES),new_vias=len(g.BOOT_VIAS),seconds=time.monotonic()-start,overlay_sha256=hashlib.sha256(Path(g.__file__).read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
p=Path(__file__).with_name('BOOT-complete-current-peer-sealed11.json');assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
print('TERMINAL',out['complete_actual_BOOT_tree'],out['all_finite_pass'],out['seconds'])
assert out['complete_actual_BOOT_tree']and out['all_finite_pass']
