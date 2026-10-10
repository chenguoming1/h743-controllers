"""Read-only exact topology, saved-return classification and conditional RC sensitivity."""
import pathlib,json,hashlib,sys,math,heapq,collections
from shapely.geometry import Point,Polygon,mapping,shape
from shapely.ops import unary_union
H=pathlib.Path(__file__).resolve().parent;R=H.parents[2];D=H/'candidate01';S=H.parent/'servo48/candidate04';O=D/'conditional-signal-review';O.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'repo/f722-heli/layout-revision/signal-review/native'))
from check_signal_geometry import poly,copper_entries,pieces,centerline
from check_critical_reference import ground_geometry,ground_ties,REFERENCE
read=lambda p:json.loads(pathlib.Path(p).read_text());sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();write=lambda p,x:pathlib.Path(p).write_text(json.dumps(x,indent=2)+'\n')
n=read(D/'f722-heli.native.json');old=read(S/'f722-heli.native.json');h=sha(D/'f722-heli.kicad_pcb');assert h==n['board_sha256'];prov=read(D/'construction-provenance.json');raw=read(D/'new-route-reference-review.json');added={o['uuid']for o in prov['added_records']}
binding=dict(board_sha256=h,source_board_sha256=old['board_sha256'],native_sha256=sha(D/'f722-heli.native.json'),source_native_sha256=sha(S/'f722-heli.native.json'))
objects={o['uuid']:o for o in n['objects']};pads={o['key']:o for o in n['objects']if o['kind']=='pad'}
nets=['RPM_EXT','RPM_HV','RPM_LV','RPM_MCU'];obs=[o for o in n['objects']if o['net']in nets];g=collections.defaultdict(list)
def node(l,xy):return(l,*xy)
def edge(a,b,w,u):g[a].append((b,w,u));g[b].append((a,w,u))
for t in obs:
 if t['kind']=='track':edge(node(next(iter(t['copper'])),t['start']),node(next(iter(t['copper'])),t['end']),math.dist(t['start'],t['end']),t['uuid'])
for v in obs:
 if v['kind']=='via':
  for l in v['barrel_layers']:edge(('via',v['uuid']),node(l,v['xy']),0,v['uuid'])
for p in obs:
 if p['kind']=='pad':
  for l,ps in p['copper'].items():
   pg=poly(ps)
   for v in list(g):
    if len(v)==3 and v[0]==l and pg.covers(Point(v[1:])):edge(('pad',p['key']),v,0,p['uuid'])
paths={}
for a,b in [('J7.3','R25.1'),('R25.2','U16.1'),('U16.1','Q1.3'),('Q1.2','R39.1'),('R36.2','R39.1'),('R39.2','U13.6'),('U13.6','U1.16')]:
 start=('pad',a);target=('pad',b);q=[(0,start)];dist={start:0};prev={}
 while q:
  cost,x=heapq.heappop(q)
  if cost!=dist[x]:continue
  if x==target:break
  for y,w,u in g[x]:
   c=cost+w
   if c<dist.get(y,math.inf):dist[y]=c;prev[y]=(x,u);heapq.heappush(q,(c,y))
 assert target in dist,(a,b)
 x=target;ids=[]
 while x!=start:x,u=prev[x];ids.append(u)
 ids=list(dict.fromkeys(reversed(ids)));ts=[objects[u]for u in ids if objects[u]['kind']=='track'];vs=[objects[u]for u in ids if objects[u]['kind']=='via'];layers=collections.defaultdict(float)
 for t in ts:layers[next(iter(t['copper']))]+=math.dist(t['start'],t['end'])
 paths[a+'__'+b]=dict(planar_track_length_mm=dist[target],by_layer_mm=dict(layers),via_count=len(vs),via_xy_mm=[v['xy']for v in vs],track_uuids=[t['uuid']for t in ts])
inventory={}
for net in nets:
 ts=[o for o in obs if o['net']==net and o['kind']=='track'];vs=[o for o in obs if o['net']==net and o['kind']=='via'];layers=collections.defaultdict(float)
 for t in ts:layers[next(iter(t['copper']))]+=math.dist(t['start'],t['end'])
 inventory[net]=dict(track_count=len(ts),total_track_length_mm=sum(layers.values()),by_layer_mm=dict(layers),via_count=len(vs))
parts={f['ref']:{k:f[k]for k in ['uuid','ref','value','fpid','xy','angle','side']}for f in n['footprints']if f['ref']in ['J7','R25','Q1','R36','R39','U13','U16','U1']}
keys=['J7.3','R25.1','R25.2','U16.1','U16.3','Q1.1','Q1.2','Q1.3','R36.1','R36.2','R39.1','R39.2','U13.6','U13.2','U13.5','U1.16']
midcontacts=[]
for t in obs:
 if t['kind']!='track'or t['uuid']not in added:continue
 layer=next(iter(t['copper']))
 for v in obs:
  if v['kind']!='via'or v['net']!=t['net']or v['xy']in[t['start'],t['end']]:continue
  overlap=poly(t['copper'][layer]).intersection(poly(v['copper'][layer])).area
  if overlap>0:midcontacts.append(dict(track_uuid=t['uuid'],via_uuid=v['uuid'],via_xy=v['xy'],layer=layer,actual_land_overlap_mm2=overlap,centerline_distance_to_via_center_mm=centerline(t).distance(Point(v['xy']))))
top=dict(schema='f722-RPM-source-bound-signal-path/v1',**binding,paths=paths,net_inventory=inventory,parts=parts,pads={k:{x:pads[k][x]for x in ['uuid','net','xy','size']}for k in keys},new_tracks=len([u for u in added if objects[u]['kind']=='track']),new_vias=5,new_planar_length_mm=sum(math.dist(objects[u]['start'],objects[u]['end'])for u in added if objects[u]['kind']=='track'),additional_same_net_midsegment_via_land_contacts=midcontacts,physical_shortest_path_claimed=False,method='Exact saved track endpoint graph; actual pad interiors and plated via centers join at zero planar distance. Counts whole track centerlines including land entries. Excludes component internals, pad-internal travel and via barrel propagation. All branch inventory retained separately. Midsegment same-net via land contacts are reported separately: the endpoint walk is not a unique or shortest physical copper path.')
write(O/'RPM-path-topology.json',top)
_,zones,physical,cuts=ground_geometry(n,copper_entries(n));_,oldzones,oldphysical,oldcuts=ground_geometry(old,copper_entries(old));ties,rejected=ground_ties(n,zones,cuts);vias=[o for o in obs if o['kind']=='via'and o['net']=='RPM_MCU'];windows=unary_union([Point(v['xy']).buffer(v['width']/2+.127+.01,quad_segs=96)for v in vias]);res=[]
for r in raw['tracks']:
 if r['outside_width_empty']and r['outside_centerline_empty']:continue
 t=objects[r['uuid']];ref=r['reference_layer'];p=poly(t['copper'][r['layer']]);gap=p.difference(physical[ref]).difference(windows);assert gap.area==r['width_outside_own_via_windows_mm2'];holes=[Polygon(h)for pp in pieces(zones[ref],'Polygon')for h in pp.interiors];matches=[]
 for hole in holes:
  if hole.intersection(gap).area<=0:continue
  members=[{k:v[k]for k in ['uuid','net','xy']}for v in n['objects']if v['kind']=='via'and hole.covers(Point(v['xy']))]
  matches.append(dict(bounds_mm=list(hole.bounds),area_mm2=hole.area,contained_vias=members))
 res.append(dict(uuid=t['uuid'],start=t['start'],end=t['end'],layer=r['layer'],reference_layer=ref,actual_outside_own_window_geometry=mapping(gap),area_mm2=gap.area,bounds_mm=list(gap.bounds),component_count=len(pieces(gap,'Polygon')),centerline_outside_own_window_mm=centerline(t).difference(physical[ref]).difference(windows).length,intersection_with_any_drill_mm2=gap.intersection(cuts[ref]).area,area_already_missing_in_source_plane_mm2=gap.difference(oldphysical[ref]).area,area_newly_lost_from_source_plane_mm2=gap.intersection(oldphysical[ref]).area,containing_saved_holes=matches,minimum_distance_to_centerline_mm=gap.distance(centerline(t))))
returns=[]
for v in vias:
 nearest=sorted(ties,key=lambda t:math.dist(t['xy_mm'],v['xy']))[:3];layers=sorted({next(iter(o['copper']))for o in obs if o['kind']=='track'and v['xy']in[o['start'],o['end']]});refs=sorted({REFERENCE[l]for l in layers})
 returns.append(dict(via_uuid=v['uuid'],xy_mm=v['xy'],signal_layers_used=layers,adjacent_reference_planes=refs,requires_interplane_reference_transfer=len(refs)>1,nearest_three_both_plane_bonded_GND_ties=[dict(**t,center_distance_mm=math.dist(t['xy_mm'],v['xy']))for t in nearest]))
ret=dict(schema='f722-RPM-exact-return-context/v1',**binding,raw_reference_review_sha256=sha(D/'new-route-reference-review.json'),raw_summary=raw['summary'],outside_window_width_residuals=res,via_return_context=returns,both_plane_bonded_GND_ties=len(ties),unbonded_or_rejected_ties=len(rejected),normalization_or_tolerance_waiver_used=False,AC_return_qualified=False,limits=['All exact nonempty polygons are retained. Width residues are genuine saved geometry and are not zeroed by an area tolerance.','Ground tie distances are Euclidean context, not plane-path length, inductance, impedance or an AC current-flow proof.','Two transitions change reference plane: B-to-In2 at the clamp and In2-to-In3 at the bridge. The other three transitions share In4 but still have own antipad and barrel discontinuities.'])
write(O/'RPM-return-context.json',ret)
actual=read(D/'protection-actual-io.json');prior=read(S/'protection-actual-io.json');now={r['id']:r for r in actual['checks']};passed=[r['id']for r in prior['checks']if r['complete_clamp_first_path_passes']];assert all(now[k]['complete_clamp_first_path_passes']for k in passed);rpm=next(r for r in actual['checks']if r['net']=='RPM_MCU');assert rpm['complete_clamp_first_path_passes']
write(D/'actual-protection-superset.json',dict(schema='f722-RPM-actual-protection-superset/v1',**binding,passed=True,source_report_sha256=sha(S/'protection-actual-io.json'),candidate_report_sha256=sha(D/'protection-actual-io.json'),source_passing_ids=passed,source_passing_cases=len(passed),candidate_passing_cases=actual['passed'],all_source_passes_preserved=True,new_complete_contract=rpm))
depth={'F.Cu':.0175,'In1.Cu':.142,'In2.Cu':.4072,'In3.Cu':.6252,'In4.Cu':.8904,'B.Cu':1.0149};vertical=[]
for row in returns:
 ds=[depth[l]for l in row['signal_layers_used']];vertical.append(dict(xy_mm=row['xy_mm'],layers=row['signal_layers_used'],used_copper_center_span_mm=max(ds)-min(ds)))
Rpull=4700*1.01;Rseries=220*1.01;Rc=Rpull+Rseries;length=top['new_planar_length_mm'];tl=[]
for eps in [2.8,4.1,4.4]:
 delay=length/299.792458*math.sqrt(eps)
 for z in [40,60,100]:tl.append(dict(assumed_effective_permittivity=eps,assumed_Z0_ohm=z,new_planar_one_way_delay_ns=delay,implied_new_trace_capacitance_pF=1000*delay/z))
rc=[dict(assumed_total_LV_plus_MCU_load_pF=c,pullup_plus_series_ohm=Rc,tau_us=Rc*c*1e-6,rise10_90_us=math.log(9)*Rc*c*1e-6,rise_to_70percent_us=-math.log(.3)*Rc*c*1e-6,one_pole_3dB_kHz=1/(2*math.pi*Rc*c*1e-9))for c in [25,50,100,200]]
loading=dict(schema='f722-RPM-conditional-loading/v1',**binding,assumption_only=True,not_field_or_waveform_extracted=True,stackup=dict(board_thickness_mm=n['board_thickness_mm'],copper_center_depth_mm=depth,used_via_spans=vertical,total_used_copper_center_vertical_span_mm=sum(v['used_copper_center_span_mm']for v in vertical),five_full_board_depths_mm=5*n['board_thickness_mm']),added_via_capacitance_allocations=[dict(assumed_pF_per_via=c,total_five_vias_pF=5*c)for c in [.15,.3,.6]],new_trace_lossless_sensitivity=tl,rise_load_sensitivity=rc,RC_method='For a released transistor and a lumped total LV+MCU capacitance C, conservative first-order envelope places all C behind R36(max)+R39(max)=4969.2 ohm; ignores nonlinear Q1 turn-off/two-node dynamics and internal pull configuration. Not a guaranteed waveform.',capacitance_limits='MCU 5pF typical only; U13 I/O-GND 3typ/4maxpF only at1.65V; Q1 bias-dependent values at25V do not bound this translator. Added trace and via estimates are assumed sensitivities, not maximum extracted load.',unknowns=['ESC output topology, impedance, output low level and edge rate','external cable length/capacitance, noise and harness ground','Q1 nonlinear capacitance and actual gate/source/drain trajectories','all LV/MCU pad and coupling load, assembly variation and probe loading','minimum pulse high/low time, pulse encoding, mechanical/electrical ratio and firmware filter settings'],electrical_status='NOT_QUALIFIED')
write(O/'RPM-loading-sensitivity.json',loading)
print(json.dumps(dict(board=h,paths={k:v['planar_track_length_mm']for k,v in paths.items()},residuals=[{k:r[k]for k in ['uuid','area_mm2','bounds_mm','area_already_missing_in_source_plane_mm2','area_newly_lost_from_source_plane_mm2','minimum_distance_to_centerline_mm']}for r in res],nearest_GND_distances_mm=[dict(xy=v['xy_mm'],distance=v['nearest_three_both_plane_bonded_GND_ties'][0]['center_distance_mm'])for v in returns],rise=rc)))
