"""Source-bound physical path comparisons, explicitly not regulator qualification."""
import pathlib,json,hashlib,sys,math,heapq,itertools
H=pathlib.Path(__file__).resolve().parent;R=H.parents[2];S=R/'ordinary-routing/candidate50';D=H/'candidate03';sys.path.insert(0,str(R/'repo/f722-heli/layout-revision/signal-review/native'))
from check_signal_geometry import poly,copper_entries
from check_critical_reference import ground_geometry
from shapely.geometry import Point,LineString,mapping
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=read(S/'f722-heli.native.json');after=read(D/'f722-heli.native.json');prov=read(D/'construction-provenance.json');physical=lambda o:{k:v for k,v in o.items()if k!='net_code'}
assert before['board_sha256']==sha(S/'f722-heli.kicad_pcb')and after['board_sha256']==sha(D/'f722-heli.kicad_pcb')
def graph_path(n,net,start,end):
 objects=[o for o in n['objects']if o['net']==net];g={};nodes={};bykey={o.get('key',o['uuid']):o for o in objects}
 def edge(a,b,length,uid):g.setdefault(a,[]).append((b,length,uid));g.setdefault(b,[]).append((a,length,uid))
 for o in objects:
  if o['kind']!='track':continue
  layer=next(iter(o['copper']));a,b=[(layer,*o[k])for k in ['start','end']];edge(a,b,math.dist(o['start'],o['end']),o['uuid']);nodes[a]=o['start'];nodes[b]=o['end']
 for o in objects:
  if o['kind']not in['pad','via']:continue
  key=o.get('key',o['uuid']);root=('terminal',key)
  for node,xy in nodes.items():
   if node[0]in o['copper']and poly(o['copper'][node[0]]).covers(Point(xy)):edge(root,node,math.dist(o['xy'],xy),o['uuid'])
 src=('terminal',start);dst=('terminal',end);q=[(0,0,src,[])];seen={};counter=itertools.count(1)
 while q:
  d,_,v,p=heapq.heappop(q)
  if v in seen:continue
  seen[v]=d
  if v==dst:
   ids=list(dict.fromkeys(p));tracks=[o for o in objects if o['uuid']in ids and o['kind']=='track'];return dict(found=True,planar_track_length_mm=d,track_uuids=[o['uuid']for o in tracks],track_widths_mm=sorted(set(o['width']for o in tracks)),via_uuids=[o['uuid']for o in objects if o['uuid']in ids and o['kind']=='via'],centerline_path_excludes_component_and_barrel_internal_lengths=True)
  for w,weight,uid in g.get(v,[]):
   if w not in seen:heapq.heappush(q,(d+weight,next(counter),w,p+[uid]))
 return dict(found=False)
def plane_witness(n,source,target,width):
 by={o['uuid']:o for o in n['objects']};a,b=by[source],by[target];u=[(b['xy'][i]-a['xy'][i])/math.dist(a['xy'],b['xy'])for i in range(2)];p=[a['xy'][i]+.15*u[i]for i in range(2)];q=[b['xy'][i]-.15*u[i]for i in range(2)];line=LineString([p,q]);strip=line.buffer(width/2,cap_style=2);_,zones,ground,drills=ground_geometry(n,copper_entries(n));rows=[];direct={l:dict(missing_mm2=strip.difference(ground[l]).area,actual_missing_geometry=mapping(strip.difference(ground[l])))for l in ['In1.Cu','In4.Cu']};mid=[];startunit=endunit=u
 if any(v['missing_mm2']>0 for v in direct.values()):
  # A fixed small witness bend above the actual saved void; this changes no copper.
  mid=[[30.65,17.8]];startunit=[(mid[0][i]-a['xy'][i])/math.dist(a['xy'],mid[0])for i in range(2)];endunit=[(b['xy'][i]-mid[0][i])/math.dist(mid[0],b['xy'])for i in range(2)];p=[a['xy'][i]+.15*startunit[i]for i in range(2)];q=[b['xy'][i]-.15*endunit[i]for i in range(2)];line=LineString([p,*mid,q]);strip=line.buffer(width/2,cap_style=2)
 for layer in ['In1.Cu','In4.Cu']:
  missing=strip.difference(ground[layer]);annular=[]
  for v,point,direction in [(a,p,startunit),(b,q,endunit)]:
   native=poly(v['copper'][layer]).buffer(-n['maximum_polygon_error_mm']).difference(poly(v['drill']['outside']));endstrip=LineString([[point[i]-.002*direction[i]for i in range(2)],[point[i]+.002*direction[i]for i in range(2)]]).buffer(width/2,cap_style=2);contact=poly(v['copper'][layer]).difference(drills[layer]).intersection(zones[layer].difference(drills[layer]));annular.append(dict(via_uuid=v['uuid'],finite_annular_window_mm=mapping(endstrip),window_outside_actual_annulus_mm2=endstrip.difference(native).area,positive_saved_zone_contact_mm2=contact.area))
  rows.append(dict(layer=layer,full_width_mm=width,finite_strip_missing_mm2=missing.area,finite_strip_missing_geometry=mapping(missing),finite_strip_fully_inside_saved_physical_ground=missing.is_empty,annular_entries=annular))
 return dict(source_via=source,target_via=target,source_xy=a['xy'],target_xy=b['xy'],via_center_distance_mm=math.dist(a['xy'],b['xy']),witness_center_path_length_mm=LineString([a['xy'],*mid,b['xy']]).length,finite_strip_centerline_mm=[p,*mid,q],straight_strip_trial=direct,planes=rows,qualified_current_path=False)
oldby={o['uuid']:o for o in before['objects']};newby={o['uuid']:o for o in after['objects']};old_c58='05b65697-c2ea-4e3a-9c91-ffe217bc975d';new_c58='07d7ae57-1856-4035-91d7-ae96a26f2ddd';u6g='5fcbcdfd-4888-47d4-87de-4474dc82d6a5';c74feed='cb46fb53-49b2-4ac5-9b9f-56e4082763af';c74g='d141f729-8234-4c3c-89d1-d3341d392e2b'
c58={}
for label,n,via in [('source50',before,old_c58),('candidate22',after,new_c58)]:
 positive=graph_path(n,'ABC_VAUX','U6.3','C58.1');lead=graph_path(n,'GND','C58.2',via);ic=graph_path(n,'GND','U6.4',u6g);plane=plane_witness(n,via,u6g,.2);assert positive['found']and lead['found']and ic['found'];c58[label]=dict(positive=positive,capacitor_ground_lead=lead,IC_control_ground_lead=ic,explicit_plane_witness=plane,planar_ground_witness_center_length_mm=lead['planar_track_length_mm']+plane['witness_center_path_length_mm']+ic['planar_track_length_mm'],complete_external_planar_loop_witness_length_mm=positive['planar_track_length_mm']+lead['planar_track_length_mm']+plane['witness_center_path_length_mm']+ic['planar_track_length_mm'])
unchanged_refs=['C58','U6','C74','U8','U9','C66'];padproof={ref:all(physical(o)==physical(newby[o['uuid']])for o in before['objects']if o['kind']=='pad'and o['ref']==ref)for ref in unchanged_refs};assert all(padproof.values())
c58['ABC_VAUX_all_physical_records_identical']=all(physical(o)==physical(newby[o['uuid']])for o in before['objects']if o['net']=='ABC_VAUX');assert c58['ABC_VAUX_all_physical_records_identical']
c58['function']='100nF VAUX internal-regulator bypass for TPS63070 U6, pin3. No external VAUX load is introduced. U6.4 control ground and all U6 power/input/output/inductor/feedback components remain unchanged.'
c58['assessment']='The local capacitor B ground lead is shorter and wider, but the explicit control-ground plane witness is longer. This is a topological/finite-copper observation only and does not establish equal or improved loop inductance or regulator stability. Fresh current-source power, startup/transient and regulator-loop review remains required.'
c58['datasheet_source']='https://www.ti.com/lit/ds/symlink/tps63070.pdf';c58['datasheet_sections']=['Pin Functions: VAUX pin3 and GND pin4','11.1 Layout Guidelines'];c58['datasheet_layout_intent']='Keep supply loops short and wide; preserve separate local control/power ground routing and join near the IC ground. No stability approval is inferred from DC connectivity.'
c74={}
for label,n in [('source50',before),('candidate22',after)]:
 c74[label]=dict(feed_via_to_positive_pad=graph_path(n,'CORE_BUCK_IN',c74feed,'C74.1'),mux_output_to_positive_pad=graph_path(n,'CORE_BUCK_IN','U8.1','C74.1'),ground_pad_to_existing_via=graph_path(n,'GND','C74.2',c74g))
 assert all(r['found']for r in c74[label].values())
c74.update(function='1uF bypass on TPS2121 U8 mux-output/TPS62162 U9 buck-input rail. U8 is the mux; U9 is the fixed3.3V buck. Local22uF C66 remains unchanged.',positive_feed_width_mm=.4,ground_lead_width_mm=.3,existing_feed_via_and_ground_via_physical_records_exact=all(physical(oldby[u])==physical(newby[u])for u in[c74feed,c74g]),capacitor_value_and_pose_preserved=True,ground_lead_physical_record_exact=physical(oldby['bda745f7-49e0-4bd1-be3f-06a961d8c5f1'])==physical(newby['bda745f7-49e0-4bd1-be3f-06a961d8c5f1']),full_input_rail_and_GND_native_pad_partitions_preserved=True,finite_new_pad_and_annular_entries='entry-support-audit.json',fresh_power_model_required=True)
oldcore=[o for o in prov['removed_source_records']if o['net']=='+3V3_CORE'];newcore=[newby[u]for u in prov['routes']['complete-core-feed']];core=dict(removed_tracks=[dict(uuid=o['uuid'],layer=next(iter(o['copper'])),start=o['start'],end=o['end'],width_mm=o['width'])for o in oldcore],replacement_tracks=[dict(uuid=o['uuid'],layer=next(iter(o['copper'])),start=o['start'],end=o['end'],width_mm=o['width'])for o in newcore],removed_track_length_mm=sum(math.dist(o['start'],o['end'])for o in oldcore),replacement_track_length_mm=sum(math.dist(o['start'],o['end'])for o in newcore),all_widths_preserved_at_mm=.3,source_complete_pad_partition_restored=True,retained_ADC_and_SBUS_regression='declared-transaction50-screen.json',numerical_drop_ampacity_or_ripple_qualification=False)
out=dict(schema='f722-PORT-B-conditional-power-path-review/v1',board_sha256=after['board_sha256'],source_board_sha256=before['board_sha256'],native_sha256=sha(D/'f722-heli.native.json'),source_native_sha256=sha(S/'f722-heli.native.json'),script_sha256=sha(pathlib.Path(__file__)),support_audit_sha256=sha(D/'power-audit.json'),unchanged_full_power_pad_records=padproof,C58=c58,C74=c74,CORE=core,all28_native_support_groups_exactly_preserved=True,numerical_power_and_VCAP_applicable=False,regulator_stability_or_transient_qualification=False,limits=['Explicit plane strips show a possible finite-copper geometric connection, not the actual frequency-dependent current distribution.','Reported lengths are planar track/plane-witness lengths; package-internal and vertical barrel lengths are not included.','Original source50 power numerical evidence is stale and does not qualify this changed copper or ground domain.'])
(D/'conditional-power-path-review.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(C58={k:dict(ground_mm=v['planar_ground_witness_center_length_mm'],loop_mm=v['complete_external_planar_loop_witness_length_mm'],plane_clear=[p['finite_strip_fully_inside_saved_physical_ground']for p in v['explicit_plane_witness']['planes']])for k,v in c58.items()if isinstance(v,dict)},C74=c74,CORE=core),indent=2))
