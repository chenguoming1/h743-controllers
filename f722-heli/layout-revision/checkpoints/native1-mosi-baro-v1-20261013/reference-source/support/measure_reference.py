"""Preserved all-track projection source; see README for unresolved runtime inputs."""
import os,resource,signal,sys,json,gzip,hashlib,time
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(120,120));signal.alarm(120)
import portable_paths as portable
_inputs=portable.geometry_context(); O=portable.OUTPUT
import finite_kernel as k
from shapely.geometry import LineString,Point,box
from shapely.ops import unary_union,nearest_points
from shapely import wkb
read=portable.read
sha=portable.sha
canon=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
write=lambda p,x:Path(p).write_text(canon(x)+'\n')
C=portable.CHECKPOINT/'native'
plan={'source_board_sha256':_inputs['source_board_sha256'],'paths':{'source_native':str(portable.CHECKPOINT/_inputs['public_inputs']['source_native']['checkpoint_relative_path'])}}
manifest={'native':portable.native_binding(_inputs['public_inputs']['candidate_native'])}
source_manifest={'native':portable.native_binding(_inputs['public_inputs']['source_native'])}
_binding={'candidate_board_sha256':_inputs['candidate_board_sha256'],'candidate_native_logical_sha256':_inputs['public_inputs']['candidate_native']['logical_sha256']}
refs={'F.Cu':('In1.Cu',.0994),'In2.Cu':('In1.Cu',.25),'In3.Cu':('In4.Cu',.25),'B.Cu':('In4.Cu',.0994)}
guard_path=portable.DATA/'selected-native-records.json';guard=read(guard_path)
def extract(tag,path,binding):
 assert sha(path)==binding['compressed']['sha256']
 raw=gzip.open(path,'rb').read();assert hashlib.sha256(raw).hexdigest()==binding['uncompressed']['sha256'];d=json.loads(raw);del raw
 rows=k.native_records_with_fills(d);holes=k.hole_map(rows,d['copper_layers']);planes={}
 for layer in ['In1.Cu','In4.Cu']:
  planes[layer]=unary_union([k.native_polygons(z['filled'].get(layer,[])) for z in d['zones'] if not z['rule'] and z['net']=='GND']).difference(holes.get(layer,unary_union([])))
 needed={r['uuid'] for r in guard['guard_rows']};records={}
 for r in d['objects']:
  if r['kind']!='track' and r['uuid'] not in needed:continue
  shapes,_=k.conductive_shapes(r,holes)
  records[r['uuid']]={'uuid':r['uuid'],'net':r['net'],'kind':r['kind'],'record_sha256':hashlib.sha256(canon(r).encode()).hexdigest(),'shapes':{l:s.wkb_hex for l,s in shapes.items()},**{x:r[x] for x in ['start','end','width','key'] if x in r}}
 out={'board_sha256':d['board_sha256'],'native_logical_sha256':binding['uncompressed']['sha256'],'planes':{l:s.wkb_hex for l,s in planes.items()},'records':records,'native_polygon_error_mm':d['maximum_polygon_error_mm']}
 del d,rows,holes,planes,shapes
 import gc;gc.collect()
 with gzip.open(O/(tag+'-projection-input.json.gz'),'wt') as stream:json.dump(out,stream,sort_keys=True,separators=(',',':'),allow_nan=False)
 print(tag+' extraction saved',flush=True)
 return out
if sys.argv[1]=='extract':
 tag=sys.argv[2];extract(tag,Path(plan['paths']['source_native']) if tag=='source' else C/'after.native.json.gz',source_manifest['native'] if tag=='source' else manifest['native']);sys.exit()
a,b=[json.load(gzip.open(O/(tag+'-projection-input.json.gz'),'rt')) for tag in ['source','candidate']]
assert a['board_sha256']==plan['source_board_sha256'] and a['native_logical_sha256']=='a4fddb679e9d73dd2a7b6300fa8888be47e30ab6f139bd5b78ab308d9192563c'
assert b['board_sha256']==_binding['candidate_board_sha256'] and b['native_logical_sha256']==_binding['candidate_native_logical_sha256']
planes=[{l:wkb.loads(h,hex=True) for l,h in d['planes'].items()} for d in [a,b]];lost={l:planes[0][l].difference(planes[1][l]) for l in planes[0]};gained={l:planes[1][l].difference(planes[0][l]) for l in planes[0]}
def evidence(s):return {'area_mm2':s.area,'length_mm':s.length,'wkb_hex':s.wkb_hex}
def gap(s,change,oldplane,newplane):
 if s.is_empty or change.is_empty:return None
 x,y=nearest_points(s,change);line=LineString([x,y]);return {'distance_mm':s.distance(change),'projection_xy':list(x.coords[0]),'lost_GND_xy':list(y.coords[0]),'witness_length_mm':line.length,'source_GND_covered_length_mm':line.intersection(oldplane).length,'candidate_GND_covered_length_mm':line.intersection(newplane).length,'candidate_uncovered_WKB_hex':line.difference(newplane).wkb_hex,'local_witness_only':True}
if sys.argv[1]=='inventory':
 out=O/'all-track-projections.jsonl';summary={};count=0;changed=[];in4=[]
 with out.open('w') as stream:
  for uid,r in sorted(b['records'].items()):
   if r['kind']!='track':continue
   for layer,h in r['shapes'].items():
    shape=wkb.loads(h,hex=True);line=LineString([r['start'],r['end']]);base={'uuid':uid,'net':r['net'],'layer':layer,'start':r['start'],'end':r['end'],'width_mm':r['width'],'length_mm':line.length,'source_record_exact':uid in a['records'] and r['record_sha256']==a['records'][uid]['record_sha256']}
    if layer=='In4.Cu':
     base.update(reference_layer=None,coplanar_In4_gap_mm=shape.distance(planes[1]['In4.Cu']),remote_In1_surface_separation_mm=.7332,remote_In1_unsupported_mm2=shape.difference(planes[1]['In1.Cu']).area,remote_reference_equivalence=False);in4.append(base);stream.write(canon(base)+'\n');continue
    ref,dielectric=refs[layer];oldplane,newplane=planes[0][ref],planes[1][ref];oldshape=wkb.loads(a['records'][uid]['shapes'][layer],hex=True);prior=oldshape.difference(oldplane);unsupported=shape.difference(newplane);newloss=shape.intersection(lost[ref]);centerloss=line.intersection(lost[ref]);gain=shape.intersection(gained[ref])
    base.update(reference_layer=ref,dielectric_surface_mm=dielectric,source_unsupported=evidence(prior),candidate_unsupported=evidence(unsupported),newly_lost_reference=evidence(newloss),newly_lost_centerline=evidence(centerloss),newly_gained_reference_mm2=gain.area,full_width_projection_to_newly_lost_GND=gap(shape,lost[ref],oldplane,newplane))
    stream.write(canon(base)+'\n');count+=1
    q=summary.setdefault(r['net'],{'tracks':0,'source_unsupported_mm2':0.,'candidate_unsupported_mm2':0.,'newly_lost_mm2':0.,'newly_lost_centerline_mm':0.,'by_layer':{}});q['tracks']+=1;q['source_unsupported_mm2']+=prior.area;q['candidate_unsupported_mm2']+=unsupported.area;q['newly_lost_mm2']+=newloss.area;q['newly_lost_centerline_mm']+=centerloss.length;q['by_layer'][layer]=q['by_layer'].get(layer,0)+1
    if newloss.area>0:changed.append({x:base[x] for x in ['uuid','net','layer','start','end','width_mm','length_mm'] }|{'newly_lost_mm2':newloss.area,'newly_lost_centerline_mm':centerloss.length,'newly_lost_bounds_mm':list(newloss.bounds)})
 write(O/'inventory-summary.json',{'source':{k:a[k] for k in ['board_sha256','native_logical_sha256']},'candidate':{k:b[k] for k in ['board_sha256','native_logical_sha256']},'source_bound_guard_manifest_sha256':sha(guard_path),'plane_changes':{l:{'source_area_mm2':planes[0][l].area,'candidate_area_mm2':planes[1][l].area,'exactly_equal':planes[0][l].equals(planes[1][l]),'lost':evidence(lost[l]),'gained':evidence(gained[l])} for l in planes[0]},'routed_net_count':len(summary),'track_projection_count':count,'net_summaries':summary,'newly_lost_track_projections':changed,'In4_signal_tracks':in4,'all_track_projections_sha256':sha(out),'resource_limits':{'CPU':1,'address_space_MiB':512,'seconds':120},'acceptance':'PENDING_FINITE_RETURN_CURRENT_AND_ESD_REVIEW'})
 print(canon({'routed_nets':len(summary),'tracks':count,'affected_nets':{net:s for net,s in summary.items() if s['newly_lost_mm2']>0},'In4_track_count':len(in4),'changed_track_count':len(changed)}))
