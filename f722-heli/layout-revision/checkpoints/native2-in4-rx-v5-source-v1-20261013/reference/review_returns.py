"""Bounded actual source/candidate return geometry; no native or route execution."""
import sys,os,resource,signal,time,json,hashlib,importlib.util,math,heapq
from pathlib import Path
import portable_paths as portable
P=portable.OUTPUT
S=portable.CHECKPOINT/'../native3-r35-cleanup-v1-20261012/current/after.native.json.gz'
C=portable.CHECKPOINT/'native/after.native.json.gz'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
 assert sys.argv[1:]==['--run-authorized-local-review']
 resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(120,121));resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('120 second local review')));signal.alarm(120);start=time.monotonic()
 assert sha(S)=='fa9edf10e18b76701e60ff534987c63830421630dd2bf5b2d49851f865f7d3ff';assert sha(C)=='c193b7e9988bbf0d72bf08365ba01268244a349db41c832a5a6785f91b8f0cef'
 portable.geometry_context()
 import stream_native as m
 from shapely.geometry import Polygon,Point,LineString
 from shapely.ops import unary_union,nearest_points
 from shapely.strtree import STRtree
 def poly(rows):
  ps=[Polygon(p['outer'],p.get('holes',[])) for p in rows];assert all(x.is_valid for x in ps);return unary_union(ps)
 rows={};holes=[]
 for o in m.stream_field(S,'objects',True):
  if o.get('drill'):holes.append(poly(o['drill']['outside']))
  if o['net'] in ['GND','PORT_C_RX_MCU','PORT_C_RX_EXT']:rows[o['uuid']]=o
 holes=unary_union(holes)
 zones={}
 for label,f in [('source',S),('candidate',C)]:
  zones[label]={l:poly(ps).difference(holes) for z in m.stream_field(f,'zones',True) if not z['rule'] and z['net']=='GND' for l,ps in z['filled'].items()}
  assert set(zones[label])=={'In1.Cu','In4.Cu'}
 before,after=zones['source']['In4.Cu'],zones['candidate']['In4.Cu'];loss=before.difference(after);zone_losses={l:zones['source'][l].difference(zones['candidate'][l]) for l in ['In1.Cu','In4.Cu']}
 ground={u:o for u,o in rows.items() if o['net']=='GND'};shapes={(u,l):poly(ps).difference(holes) for u,o in ground.items() for l,ps in o['copper'].items()};layers={l:[(u,g) for (u,ll),g in shapes.items() if ll==l] for l in ['F.Cu','B.Cu']};trees={l:STRtree([g for u,g in a]) for l,a in layers.items()}
 def surf_path(pad):
  layer=next(iter(pad['copper']));pending=[(0,pad['uuid'],[])];best={};out=[]
  while pending:
   distance,u,path=heapq.heappop(pending)
   if u in best:continue
   best[u]=distance;o=ground[u];path=path+[u]
   if o['kind']=='via':out.append({'via_uuid':u,'via_xy':o['xy'],'path_UUIDs':path,'sum_track_centerline_lengths_mm':distance});continue
   for idx in trees[layer].query(shapes[(u,layer)]):
    v,g=layers[layer][int(idx)]
    if v not in best and v!=u and shapes[(u,layer)].intersection(g).area>0:
     q=ground[v];w=math.dist(q['start'],q['end']) if q['kind']=='track' else 0;heapq.heappush(pending,(distance+w,v,path))
  return sorted(out,key=lambda x:(x['sum_track_centerline_lengths_mm'],x['via_uuid']))
 def entry(v):
  center=Point(v['xy']);res={'via_uuid':v['uuid'],'xy':v['xy'],'source_full_record_sha256':digest(v),'diameter_mm':v['width'],'drill_mm':v['drill']['width'],'layers':{}}
  for layer in ['In1.Cu','In4.Cu']:
   annulus=shapes[(v['uuid'],layer)];s=zones['source'][layer];c=zones['candidate'][layer];delta=zone_losses[layer]
   res['layers'][layer]={'source_annular_overlap_mm2':annulus.intersection(s).area,'candidate_annular_overlap_mm2':annulus.intersection(c).area,'annular_attachment_loss_mm2':annulus.intersection(delta).area,'nearest_new_loss_from_annulus_mm':annulus.distance(delta) if not delta.is_empty else None,'within_1mm_source_plane_area_mm2':s.intersection(center.buffer(1,quad_segs=32)).area,'within_1mm_candidate_plane_area_mm2':c.intersection(center.buffer(1,quad_segs=32)).area}
  # Finite fully-connected annular collar around the original bore, all angles.
  bore=poly(v['drill']['outside']);base=annulus=None
  collar={}
  for label,g in [('source',before),('candidate',after)]:
   # Distance to foreign voids/exterior after filling ONLY this owned bore.
   filled=g.union(bore);collar[label+'_minimum_radial_copper_radius_mm']=center.distance(filled.boundary) if filled.covers(center) else 0
  collar['minimum_residual_radial_land_mm']=min(collar.values())-v['drill']['width']/2;collar['interpretation']='Exact all-direction circular attachment collar, not a whole-plane/global-neck or transient qualification.';res['In4_finite_attachment_collar']=collar
  return res
 fp={f['ref']:{k:f[k] for k in ['ref','value','xy','side']} for f in m.stream_field(S,'footprints',True)}
 refs={ref for ref,f in fp.items() if any(x in f['value'].upper() for x in ['ESD','CLAMP','SMF'])}
 returns=[];used={}
 for pad in sorted((o for o in ground.values() if o['kind']=='pad' and (o.get('ref') in refs or o.get('key')=='J11.4')),key=lambda o:o['key']):
  paths=surf_path(pad);bounds=poly(next(iter(pad['copper'].values()))).bounds
  for x in paths:used[x['via_uuid']]=entry(ground[x['via_uuid']])
  returns.append({'key':pad['key'],'uuid':pad['uuid'],'xy':pad['xy'],'side':next(iter(pad['copper'])),'part':fp[pad['ref']]['value'],'record_sha256':digest(pad),'first_return_via_paths':paths,'In4_projection_to_new_loss_mm':poly(next(iter(pad['copper'].values()))).distance(loss),'GND_pad_DC_connected_in_native_receipt':True})
 transitions=[]
 for uid in ['772ddcac-065d-5d1d-88d4-24a832e0f2be','a5df4a3c-85c0-54f1-8a9a-c0a73de16d7a']:
  rx=rows[uid];near=[]
  for u,v in ground.items():
   if v['kind']!='via':continue
   e=entry(v)
   if all(e['layers'][l]['candidate_annular_overlap_mm2']>0 for l in ['In1.Cu','In4.Cu']):
    d=math.dist(rx['xy'],v['xy']);near.append({'via_uuid':u,'xy':v['xy'],'center_distance_mm':d,'edge_to_edge_nominal_mm':d-rx['width']/2-v['width']/2,'actual_both_plane_attachment':e})
  near.sort(key=lambda x:x['center_distance_mm']);transitions.append({'RX_barrel_uuid':uid,'xy':rx['xy'],'nearest_actual_dual_plane_GND_stitches':near[:3],'nearby_via_proximity_alone_not_return_qualification':True})
 result={'schema':'f722-source3-In4-actual-return-geometry/v1','source':{'path':str(S),'sha256':sha(S),'board_sha256':'c3183f7841bae96a59b29fd13ce9789cf47386a9db452a327ca797187d2ca8a8'},'candidate':{'path':str(C),'sha256':sha(C),'board_sha256':'7d9af57e9b22064fc6b2fd9cde4f2f5b72dc252cdbb1b104e706472bfdbbcdcb'},'script_sha256':sha(Path(__file__)),'geometry_error_allowance_mm':.00002,'all_source_return_records_retained_exact_by_native_diagnostic':True,'protection_footprint_refs':sorted(refs),'actual_protection_GND_entries':returns,'selected_return_via_attachments':used,'RX_transition_GND_stitches':transitions,'source_In1_own_drilled_exact':zones['source']['In1.Cu'].equals(zones['candidate']['In1.Cu']),'actual_In4_loss_mm2':loss.area,'global_or_ESD_transient_acceptance':False,'elapsed_seconds':time.monotonic()-start,'peak_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 out=P/'actual-return-geometry.json';assert not out.exists();out.write_text(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n');assert out.stat().st_size<1024**2;print(json.dumps({'path':str(out),'sha256':sha(out),'seconds':result['elapsed_seconds'],'RSS_KiB':result['peak_RSS_KiB'],'return_pads':len(returns),'vias':len(used)}))
if __name__=='__main__':main()
