"""Bounded fixed-pose quiet R52 return alternatives; no board mutations."""
import pathlib,json,time,math
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union
import native_geometry_sbus17 as m
H=pathlib.Path(__file__).resolve().parent;T=H/'dedicated-u12-ground15';D=H.parent/'rpm17/candidate01';read=lambda p:json.loads(p.read_text());start=time.monotonic();n=read(D/'f722-heli.native.json');p=read(T/'separated-returns14-proposal.json');remove=set(p['remove_ids']) if 'remove_ids'in p else set(p['removed_ids']);m.N=n;m.EXPECTED=n['board_sha256'];m.OUTLINE=m.geom(n['outline_with_npth']['polygons']);m.OBJECTS=[(o,{l:m.geom(s)for l,s in o['copper'].items()},{l:m.geom(s['polygons'])for l,s in o.get('mask',{}).items()}if o.get('smd')else{},m.geom(o['drill']['outside'])if o.get('drill')else None)for o in n['objects']if o['uuid']not in remove]
region=box(10,10.7,17.5,19.2);m.HALF=.1;obs,_,_=m.obstacles('GND','F.Cu');U12=LineString([[12.6,11.8875],[12.6,12.72],[13.5984,12.92],[13.5984,13.4847]]).buffer(.125/math.cos(math.pi/512),quad_segs=128);uv=Point(13.5984,13.4847).buffer(.225/math.cos(math.pi/512),quad_segs=128);isolate=unary_union([U12,uv]);ob=[o['geometry'].buffer(o['required_center_distance_mm']+m.ERROR,quad_segs=64)for o in obs if o['geometry'].distance(region)<1]
free=region.intersection(m.OUTLINE.buffer(-(.254+.1+m.ERROR))).difference(unary_union(ob)).difference(isolate.buffer(.227+m.ERROR,quad_segs=128))
def pcs(x):return[x]if x.geom_type=='Polygon'else[a for a in getattr(x,'geoms',[])if a.geom_type=='Polygon']
def serial(x):return[dict(outer=list(a.exterior.coords),holes=[list(r.coords)for r in a.interiors],area_mm2=a.area,bounds_mm=list(a.bounds))for a in pcs(x)]
a=[14.1,15.49];components=pcs(free);component=next((x for x in components if x.covers(Point(a))),Polygon());targets={'R51_pad':[12.21,14.55],'R51_new_via':[12.045672,13.000917],'R51_lead_mid':[11.95,14.15],'U5_8_via':[14.15,17.23],'U5_8_pad':next(o['xy']for o in n['objects']if o.get('key')=='U5.8'),'C30_2':[15.25,15.52]};trials=[]
for name,b in targets.items():
 best=None
 for pts in m.paths2(a,b):
  line=LineString(pts);viol=m.check(line,obs);v=[x for x in viol if x['extra_clearance_mm']<m.ERROR];gap=line.buffer(.1/math.cos(math.pi/512),quad_segs=128).distance(isolate)
  row=dict(points=pts,violations=v,independent_U12_gap_mm=gap,length_mm=line.length)
  if best is None or len(v)<len(best['violations']):best=row
 trials.append(dict(target=name,xy=b,same_complete_F_region=component.covers(Point(b)),short_path_screen=best))
out=dict(schema='f722-quiet-return-alternatives-fixed-pose/v1',board_sha256=n['board_sha256'],search_bounds_mm=list(region.bounds),width_mm=.2,removed_ground_tracks=sorted(remove),U12_discharge_reserved_separately=True,R52_reachable_area_mm2=component.area,R52_reachable_region=serial(component),targets=trials,elapsed_seconds=time.monotonic()-start,limits=['Bounded exact F.Cu fixed-pose domain with all signal/analog copper preserved. A disconnected domain is a local structural blocker, not global infeasibility.','20nm source polygon reserve; no snapping or geometry normalization.','R51 quiet return may be shared, but U12 local copper and first via are reserved at normal copper clearance.']);(T/'quiet-return-alternatives14.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='R52_reachable_region'}))
