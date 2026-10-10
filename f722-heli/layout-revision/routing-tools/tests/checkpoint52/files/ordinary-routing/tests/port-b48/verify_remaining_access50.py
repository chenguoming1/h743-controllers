"""Whole-outline, source-bound remaining-MCU access census; no copper mutation."""
import argparse, hashlib, json, math, pathlib, signal, sys, time
H=pathlib.Path(__file__).resolve().parent;R=H.parents[2]
sys.path.insert(0,str(H));import native_geometry as s
from shapely.geometry import Point
from shapely import unary_union
ap=argparse.ArgumentParser();ap.add_argument('--seconds',type=int,default=90);a=ap.parse_args()
signal.alarm(a.seconds+2);t0=time.monotonic();D=H/'candidate03';S=R/'ordinary-routing/candidate50'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
after=read(D/'f722-heli.native.json');before=read(S/'f722-heli.native.json');drc=read(D/'owner-drc.json');by={o['uuid']:o for o in after['objects']}
open_nets={by[i['uuid']]['net']for v in drc['unconnected_items']for i in v['items']if i['uuid']in by}
pads=sorted([o for o in after['objects']if o['kind']=='pad'and o['ref']=='U1'and o['net']in open_nets],key=lambda o:int(o['number']))
out=dict(schema='f722-remaining-MCU-access-source-comparison/v1',source_board_sha256=before['board_sha256'],board_sha256=after['board_sha256'],source_native_sha256=sha(S/'f722-heli.native.json'),native_sha256=sha(D/'f722-heli.native.json'),script_sha256=sha(pathlib.Path(__file__)),native_outline_bounds_mm=list(s.geom(after['outline_with_npth']['polygons']).bounds),search_roi='full native outline including NPTH',rows=[],complete=False,passed=False,scope='Independent conservative finite-width surface domains and legal via regions. No simultaneous multi-net routing, finite pad entry, or complete future function is inferred.')
dest=D/'remaining-MCU-access.json'
def save():dest.write_text(json.dumps(out,indent=2)+'\n')
def parts(g):return[p for p in (list(g.geoms)if hasattr(g,'geoms')else[g])if p.geom_type=='Polygon'and not p.is_empty]
def bind(n):
 s.N=n;s.OUTLINE=s.geom(n['outline_with_npth']['polygons']);s.EXPECTED=n['board_sha256'];s.OBJECTS=[(o,{l:s.geom(ps)for l,ps in o['copper'].items()},{l:s.geom(v['polygons'])for l,v in o.get('mask',{}).items()}if o.get('smd')else{},s.geom(o['drill']['outside'])if o.get('drill')else None)for o in n['objects']]
def expanded(obs):return unary_union([o['geometry'].buffer((o['required_center_distance_mm']+.0001)/math.cos(math.pi/128),quad_segs=32)for o in obs if o['category']!='edge_npth_copper'])
portals={'FLASH_CS':[23.90716,9.90146],'FLASH_SCK':[19.57724,10.43289],'FLASH_MISO':[25.40268,10.82928],'FLASH_MOSI':[21.27,11.59]}
for version,n in [('source50',before),('candidate22',after)]:
 bind(n);key={o['key']:o for o in n['objects']if o['kind']=='pad'}
 for pad0 in pads:
  if time.monotonic()-t0>a.seconds-2:save();sys.exit('Census budget reached; partial receipt saved')
  pad=key[pad0['key']];assert s.OUTLINE.covers(Point(pad['xy']));trace,via,_=s.obstacles(pad['net'],'B.Cu')
  for o,c,m,d in s.OBJECTS:
   if d is not None and not o.get('npth')and o['net']!=pad['net']:trace.append(dict(geometry=d,category='foreign_drill_to_track_copper',required_center_distance_mm=.2635))
  free=s.OUTLINE.buffer(-.3176).difference(expanded(trace));comp=next((g for g in parts(free)if g.covers(Point(pad['xy']))),None);regions=[]
  if comp is not None:
   legal=s.OUTLINE.buffer(-.4791).difference(expanded(via))
   for p in sorted(parts(comp.intersection(legal)),key=lambda p:-p.area):
    x=p.representative_point();z=s.check(x,via,True)[0];regions.append(dict(area_mm2=p.area,bounds_mm=list(p.bounds),representative_point_mm=list(x.coords[0]),nominal_extra_clearance_mm=z['extra_clearance_mm'],via_nominal_pass=z['pass_nominal']))
  selected=None
  if pad['net']in portals:
   x=Point(portals[pad['net']]);z=s.check(x,via,True);selected=dict(xy=list(x.coords[0]),via_nominal_pass=z[0]['pass_nominal'],nearest_checks=z[:3],reachable_in_surface_component=comp is not None and comp.covers(x))
  row=dict(version=version,pin=pad['key'],net=pad['net'],xy=pad['xy'],component_area_mm2=None if comp is None else comp.area,regions=regions,region_count=len(regions),selected_portal=selected);out['rows'].append(row);save();print(json.dumps({k:row[k]for k in ['version','pin','net','region_count','selected_portal']}),flush=True)
src={r['pin']:r for r in out['rows']if r['version']=='source50'};dst={r['pin']:r for r in out['rows']if r['version']=='candidate22'}
out['comparison']=[dict(pin=k,net=src[k]['net'],source_region_count=src[k]['region_count'],candidate_region_count=dst[k]['region_count'],source_accessible=src[k]['region_count']>0,candidate_accessible=dst[k]['region_count']>0,existing_no_access_preserved=src[k]['region_count']==dst[k]['region_count']==0)for k in src]
out['complete']=len(out['rows'])==2*len(pads);out['passed']=out['complete']and all(not r['source_accessible']or r['candidate_accessible']for r in out['comparison']);out['elapsed_seconds']=time.monotonic()-t0;save();print('COMPLETE',out['passed'],out['elapsed_seconds'],flush=True)
