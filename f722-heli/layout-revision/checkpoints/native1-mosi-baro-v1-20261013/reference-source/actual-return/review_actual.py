"""Inert, bounded actual-fill return witness review. No board mutation or electrical solve."""
from pathlib import Path
import argparse,ast,collections,fcntl,gzip,hashlib,heapq,json,math,os,resource,shutil,signal,sys,time,traceback,types
H=Path(__file__).resolve().parent;O=H/'outputs';R={};DEADLINE=None
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.load(gzip.open(p,'rt'))if str(p).endswith('.gz')else json.loads(Path(p).read_text())
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(name,x):
 O.mkdir(exist_ok=True);raw=(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
 if name.endswith('.gz'):raw=gzip.compress(raw,compresslevel=1,mtime=0)
 assert sum(p.stat().st_size for p in O.iterdir()if p.is_file()and p.name!=name)+len(raw)<16*1024**2
 (O/name).write_bytes(raw)
def tick(phase):
 assert time.monotonic()<DEADLINE,'115 s cooperative limit';assert shutil.disk_usage(H).free>=128*1024**2,'128 MiB reserve';R['phase']=phase;save('result.json',R)
def poly(rows):
 q=[Polygon(r['outer'],r.get('holes',[]))for r in rows];assert all(g.is_valid for g in q),'Invalid native polygon, no repair';return unary_union(q)
def parts(g):return []if g.is_empty else[g]if g.geom_type=='Polygon'else[q for q in g.geoms if q.geom_type=='Polygon']
def paths2(a,b):
 yield[a,b];yield[a,[a[0],b[1]],b];yield[a,[b[0],a[1]],b]
def core(path):
 tree=ast.parse(Path(path).read_text());f=next(q for q in tree.body if isinstance(q,ast.FunctionDef)and q.name=='route');ns={'heapq':heapq,'math':math,'time':time,'shapely':shapely,'Point':Point,'LineString':LineString,'s':types.SimpleNamespace(paths2=paths2)};exec(compile(ast.Module(body=[f],type_ignores=[]),str(path),'exec'),ns);return ns['route']
def perform(p):
 global DEADLINE
 DEADLINE=time.monotonic()+115;R.update(status='RUNNING',source=p['source'],candidate=p['candidate'],candidate_adopted=False,board_mutation=False)
 tick('bind exact drilled native fills and unchanged ground metal')
 raw=gzip.decompress(Path(p['inputs']['candidate_native']['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==p['candidate']['native_logical_sha256'];n=json.loads(raw);del raw;assert n['board_sha256']==p['candidate']['board_sha256'];by={r['uuid']:r for r in n['objects']}
 source=read(p['inputs']['source_projection']['path']);assert source['board_sha256']==p['source']['board_sha256']and source['native_logical_sha256']==p['source']['native_logical_sha256'];hashes=read(p['inputs']['source_ground_record_hashes']['path']);assert all(digest(r)==hashes[r['uuid']]for r in n['objects']if r['net']=='GND')
 delta=read(p['inputs']['delta']['path']);newvias={q['uuid']for q in delta['add_vias']};holes=unary_union([poly(q['drill']['outside'])for q in n['objects']if q.get('drill')]);oldholes=unary_union([poly(q['drill']['outside'])for q in n['objects']if q.get('drill')and q['uuid']not in newvias]);planes={};zoneplanes={};sourceplanes={};annuli={};receipts=[]
 for l in ['In1.Cu','In4.Cu']:
  zones=unary_union([poly(z['filled'].get(l,[]))for z in n['zones']if not z['rule']and z['net']=='GND']).difference(holes);lands=unary_union([poly(r['copper'][l])for r in n['objects']if r['net']=='GND'and l in r['copper']]);zoneplanes[l]=zones;planes[l]=unary_union([zones,lands]).difference(holes);sourceplanes[l]=unary_union([shapely.from_wkb(bytes.fromhex(source['planes'][l])),lands]).difference(oldholes)
 for u in p['GND_via_UUIDs']:
  r=by[u];assert r['kind']=='via'and r['net']=='GND';annuli[u]={}
  for l in planes:
   a=poly(r['copper'][l]).difference(holes);annuli[u][l]=a;receipts.append({'uuid':u,'xy':r['xy'],'layer':l,'record_sha256':digest(r),'annulus_mm2':a.area,'zone_fill_overlap_mm2':a.intersection(zoneplanes[l]).area,'full_GND_copper_covers_annulus':planes[l].covers(a),'source_full_GND_covers_annulus':sourceplanes[l].covers(a)})
 assert all(q['zone_fill_overlap_mm2']>0 and q['full_GND_copper_covers_annulus']for q in receipts)
 loss={l:sourceplanes[l].difference(planes[l])for l in planes};R['plane_change_mm2']={l:{'lost':loss[l].area,'gained':planes[l].difference(sourceplanes[l]).area,'candidate_components':len(parts(planes[l]))}for l in planes};R['ground_annular_contacts']=receipts
 tick('measure actual source-supported launch and BARO intervals')
 checks=[]
 for u,l,label in p['projection_records']:
  r=by[u];g=poly(r['copper'][l]).difference(holes);line=LineString([r['start'],r['end']]);checks.append({'label':label,'uuid':u,'layer':l,'source_unsupported_centerline_mm':line.difference(sourceplanes['In4.Cu']).length,'candidate_unsupported_centerline_mm':line.difference(planes['In4.Cu']).length,'newly_lost_centerline_mm':line.intersection(loss['In4.Cu']).length,'candidate_unsupported_WKB_hex':line.difference(planes['In4.Cu']).wkb_hex,'newly_lost_projection_mm2':g.intersection(loss['In4.Cu']).area,'actual_source_record_sha256':digest(r)})
 R['projection_checks']=checks
 before=read(p['inputs']['old_SPI_witness']['path']);oldpaths=[]
 for flank in before['flanks']:
  for row in flank['candidates']:
   if row['via_uuid']in p['old_witness_via_UUIDs']and row['finite_straight_path']:
    line=shapely.from_wkb(bytes.fromhex(row['anchor_to_actual_In4_annulus']['WKB_hex']));oldpaths.append({'via_uuid':row['via_uuid'],'source_unsupported_mm':line.difference(sourceplanes['In4.Cu']).length,'candidate_unsupported_mm':line.difference(planes['In4.Cu']).length,'newly_lost_mm':line.intersection(loss['In4.Cu']).length})
 R['old_SPI_witness_recheck']=oldpaths
 sensitive=[]
 for row in read(p['inputs']['critical_manifest']['path'])['rows']:
  if row['net']in p['sensitive_supply_nets'] and row['uuid']in by:
   r=by[row['uuid']];g=poly(r['copper'][row['layer']]);sensitive.append((row,g,g.buffer(row['margin_mm'],quad_segs=32)))
 selected={u:{'xy':by[u]['xy'],'annuli':{l:g.wkb_hex for l,g in a.items()}}for u,a in annuli.items()};save('actual-geometry-input.json.gz',{'source':p['source'],'candidate':p['candidate'],'source_GND_planes_WKB_hex':{l:g.wkb_hex for l,g in sourceplanes.items()},'candidate_GND_planes_WKB_hex':{l:g.wkb_hex for l,g in planes.items()},'candidate_zone_fill_WKB_hex':{l:g.wkb_hex for l,g in zoneplanes.items()},'selected_GND_vias':selected,'definition':'Native filled GND zones plus unchanged native GND lands/tracks, less all actual drills; zone-fill contact is also checked separately. No buffer repairs or snapping.'})
 del n,by,source,hashes,delta
 tick('six fixed finite-width return witnesses')
 radius=p['witness_width_mm']/2;erosion=(radius+.00011)/math.cos(math.pi/128);window=box(*p['local_window_mm']);domains={l:g.buffer(-erosion,quad_segs=32).intersection(window)for l,g in planes.items()};route=core(p['inputs']['generic_route_core']['path']);results=[]
 for task in p['paths']:
  tick(task['name']);l=task['layer'];domain=domains[l];bset=annuli[task['to_via']][l].buffer(-.00001).intersection(domain);a=Point(task['from_xy'])if 'from_xy'in task else None;aset=None if a is not None else annuli[task['from_via']][l].buffer(-.00001).intersection(domain)
  comp=next((g for g in parts(domain)if (g.covers(a)if a is not None else g.intersects(aset))and g.intersects(bset)),None);row=dict(task,requested_width_mm=p['witness_width_mm'],same_finite_component=comp is not None)
  if comp is None:row['status']='NO_PATH_IN_FIXED_WIDTH_WINDOW';results.append(row);continue
  if a is None:a,b=nearest_points(aset.intersection(comp),bset.intersection(comp))
  else:_,b=nearest_points(a,bset.intersection(comp))
  points=route(comp,list(a.coords[0]),list(b.coords[0]),DEADLINE)
  if points is None:row['status']='NO_CONSTRUCTOR_PATH_WITHIN_BOUND';results.append(row);continue
  points=[[round(float(v),6)for v in xy]for xy in points];line=LineString(points);gap=line.distance(planes[l].boundary);contact_a=True if 'from_xy'in task else annuli[task['from_via']][l].covers(Point(points[0]));contact_b=annuli[task['to_via']][l].covers(Point(points[-1]));valid=planes[l].covers(line)and gap>=radius and comp.covers(line)and contact_a and contact_b;row.update(status='FINITE_PATH'if valid else'ROUNDED_PATH_RECHECK_FAILED',xy=points,length_mm=line.length,actual_min_boundary_distance_mm=gap,observed_continuous_disk_path_width_mm=2*gap,candidate_outside_mm=line.difference(planes[l]).length,source_outside_mm=line.difference(sourceplanes[l]).length,from_point_on_annulus=None if 'from_xy'in task else annuli[task['from_via']][l].covers(Point(points[0])),to_point_on_annulus=annuli[task['to_via']][l].covers(Point(points[-1])))
  signal_line=LineString(task['signal_comparison_xy']);samples=[line.interpolate(i/100,normalized=True)for i in range(101)];row['geometric_return_context']={'signal_layer':task['signal_layer'],'return_layer':l,'dielectric_or_layer_surface_distance_mm':task['signal_to_return_surface_distance_mm'],'minimum_planar_signal_distance_mm':line.distance(signal_line),'sampled_max_planar_signal_distance_mm':max(q.distance(signal_line)for q in samples),'sampling_note':'101 equally spaced path stations; not an AC current distribution or exact maximum bound','distance_from_end_to_near_signal_transition_mm':min(Point(points[-1]).distance(Point(q))for q in task['signal_transition_xy']),'straight_endpoint_distance_mm':math.dist(points[0],points[-1]),'path_excess_over_straight_mm':line.length-math.dist(points[0],points[-1]),'globally_shortest_path_proven':False}
  row['sensitive_supply_projection_intersections']=[{'uuid':r['uuid'],'net':r['net'],'signal_layer':r['layer'],'source_reference_layer':r['reference'],'literal_intersection_mm':line.intersection(g).length,'review_band_intersection_mm':line.intersection(band).length,'lateral_distance_to_literal_mm':line.distance(g)}for r,g,band in sensitive if r['reference']==l and line.intersects(band)]
  results.append(row);R['paths']=results;save('result.json',R)
 R['paths']=results;R['status']='FINITE_WITNESSES_COMPLETE'if all(q['status']=='FINITE_PATH'for q in results)else'SCOPED_RETURN_WITNESS_NEGATIVE';R['electrical_limits']=['Finite metal paths do not quantify loop inductance, AC current division, reflections or EMC.','The 0.127mm witness is an engineering screen, not a native plane-neck rule or a new user requirement.','All new and original signal copper and holes remain unchanged.','No automatic width reduction, ROI widening or extra path search.']
 for name,group in p['return_groups'].items():
  pathnames=group['paths']
  selected=[q for q in results if q['name']in pathnames];R.setdefault('complete_return_groups',{})[name]={'paths':pathnames,'all_finite':len(selected)==len(pathnames)and all(q['status']=='FINITE_PATH'for q in selected),'planar_length_mm':sum(q.get('length_mm',0)for q in selected),'two_In4_to_In1_transition_surface_distance_mm':1.4664,'not_nearest_reference_equivalence':True,'signal_flank_direct_distance_mm':math.dist(*group['signal_flank_xy']),'planar_return_excess_over_signal_flank_distance_mm':sum(q.get('length_mm',0)for q in selected)-math.dist(*group['signal_flank_xy']),'sum_is_partial_when_not_all_finite':True}
 save('finite-domains.json.gz',{'erosion_mm':erosion,'window_mm':p['local_window_mm'],'domains_WKB_hex':{l:g.wkb_hex for l,g in domains.items()}})
def main():
 global shapely,Polygon,Point,LineString,box,unary_union,nearest_points
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--seal-sha256');a=ap.parse_args()
 if not a.execute:print('Inert actual-return review; explicit execution approval and sealed inputs required.');return
 assert sha(H/'REVIEW-SEAL.json')==a.seal_sha256;s=read(H/'REVIEW-SEAL.json');assert sha(__file__)==s['script_sha256'];p=read(H/'proposal.json');assert sha(H/'proposal.json')==s['proposal_sha256']
 for k,v in p['inputs'].items():assert sha(v['path'])==v['sha256'],('Input changed',k)
 assert not O.exists();fd=os.open(p['shared_lock'],os.O_RDWR);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,)*2);resource.setrlimit(resource.RLIMIT_CPU,(115,119));resource.setrlimit(resource.RLIMIT_CORE,(0,0));sys.path.insert(0,p['python_dependencies'])
 import shapely
 from shapely.geometry import Polygon,Point,LineString,box
 from shapely import unary_union
 from shapely.ops import nearest_points
 start=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('115 second wall limit')));signal.alarm(115)
 try:perform(p)
 except Exception as e:R.update(status='FAILED',error=repr(e),traceback=traceback.format_exc())
 finally:
  signal.alarm(0);R['elapsed_seconds']=time.monotonic()-start;R['peak_RSS_KiB']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;R['source_inputs_unchanged']=all(sha(v['path'])==v['sha256']for v in p['inputs'].values());save('result.json',R);fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)
 print(json.dumps({k:R.get(k)for k in ['status','elapsed_seconds','peak_RSS_KiB','error']}))
if __name__=='__main__':main()
