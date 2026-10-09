exec(open('ordinary-routing/servo2-local-review/check_final.py').read().split('for label,g,layer in ')[0])
from shapely.affinity import translate
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
paths=['ordinary-routing/candidate32/f722-heli.kicad_pcb','ordinary-routing/candidate32/f722-heli.native.json','ordinary-routing/candidate32/f722-heli.logical-route-map.json','ordinary-routing/candidate31/f722-heli.kicad_pcb','ordinary-routing/model-candidate31-ready/model.json','ordinary-routing/model-candidate31-ready/fixed-explicit-native-ids.json','ordinary-routing/model-candidate31-ready/filtered05.successes/count2/snapshot.after.json','ordinary-routing/model-candidate31-ready/filtered05.successes/count2/snapshot.ses','ordinary-routing/model-candidate31-ready/filtered05.successes/count3/snapshot.after.json','ordinary-routing/model-candidate31-ready/filtered05.successes/count3/snapshot.ses','ordinary-routing/servo2-local-review/review_local.py','ordinary-routing/servo2-local-review/check_final.py']
def finite_entry(points):
 a,b=points[-1],points[-2];d=math.dist(a,b);normal=[-(b[1]-a[1])/d,(b[0]-a[0])/d];allowed=translate(cut,-normal[0]*.0635,-normal[1]*.0635).intersection(translate(cut,normal[0]*.0635,normal[1]*.0635));return dict(endpoint=a,endpoint_depth_mm=Point(a).distance(cut.boundary),full_width_transverse_entry_length_mm=LineString([a,b]).intersection(allowed).length)
vp=Point(10.7,10.7).buffer(.225,resolution=256);vd=Point(10.7,10.7).buffer(.1,resolution=256)
def minimum(q,rows):return sorted([brief(o,l,q.distance(p)) for o,l,p in rows],key=lambda a:a['gap'])[0]
old_f_ids=[o['uuid'] for o in n['objects'] if lm.get(o['uuid'])=='SERVO2_MCU::P0' and o['kind']=='track' and 'F.Cu' in o['copper'] and max(o['start'][1],o['end'][1])>10]
old_tail='7ef93c2f-799a-4117-b124-c76999e6093b';old_via='2b07387c-0e51-4096-a791-30766feb86b6'
out={
 'schema':'f722-servo2-bounded-entry-review/v1',
 'status':'local_geometry_proposal_only_not_route_acceptance',
 'source_hashes':{p:sha(p) for p in paths if Path(p).exists()},
 'scope':{'geometry_bounds_mm':[9.5,8.5,16.5,15.5],'method':'Bounding-box-selected native polygons; a few hand-chosen path/via queries, nominal round buffers, exact source32 U12.3 inside polygon for pad cut. No solver, JVM, native DRC or board mutation.','candidate32_board_sha256':n['board_sha256'],'source31_mutable_route_objects':len(mutable),'source31_explicit_fixed_ordinary_objects':len(explicit)},
 'recommended_minimal_group':{'logical_nets':['SERVO2_MCU::P0','SERVO2_MCU::P1'],'neighboring_ordinary_nets_to_reroute':[],'fixed_ordinary_segments_actually_limiting':False,'reason':'No source31 explicit fixed ordinary object restricts these local routes. Coordinated P0 replacement opens two independent full-width tracks to the shared clamp pad; P1 gets exclusive use of the former P0 via. Local critical and power copper can stay geometrically unchanged.'},
 'proposal':{
  'track_width_mm':.127,'clearance_mm':.127,'new_via':{'logical_net':'SERVO2_MCU::P0','xy':[10.7,10.7],'diameter_mm':.45,'drill_mm':.2,'tented':['F.Mask','B.Mask']},
  'P0_F_Cu_points_mm':p0points,'P1_F_Cu_points_mm':p1points,'P0_In3_replacement_tail_points_mm':p0in3,
  'P0_retain':'Source32 R21.2 approach, via(11.77,5.49), In3 route through(11.77,8.42774) down to(10.16087,10.03687).',
  'P1_continue':'Use count2 P1 In2 corridor from old via(10.16087,11.17593) through(11.10242,11.17593),(12.88099,12.9545),(15.9801,12.9545),(16.73903,13.71343) to via(21.51385,13.71343), then its B.Cu tail to U1.57. This full continuation still needs source32 screening.',
  'remove_before_inserting':{'P0_F_Cu_track_uuids':old_f_ids,'P0_In3_tail_track_uuid':old_tail,'old_via_uuid':old_via,'old_via_disposition':'Remove/recreate as P1 exclusively, or explicitly relabel with removal/ownership validation. No P0 copper may remain connected to it outside U12.3.'},
  'electrical_topology':'R21.2 → dedicated P0 → actual U12.3 pad → dedicated P1 → U1.57. P0/P1 meet only inside the real clamp pad.'},
 'local_screen_measurements_mm':{
  'P0_P1_F_Cu_outside_actual_pad_gap':g0.difference(cut).distance(g1.difference(cut)),
  'P0_nearest_foreign_F_Cu':minimum(g0,[(o,l,p) for o,l,p in local if l=='F.Cu' and o['net']!='SERVO2_MCU']),
  'P1_nearest_foreign_F_Cu':minimum(g1,[(o,l,p) for o,l,p in local if l=='F.Cu' and o['net']!='SERVO2_MCU']),
  'P0_In3_tail_nearest_foreign':minimum(g3,[(o,l,p) for o,l,p in local if l=='In3.Cu' and o['net']!='SERVO2_MCU']),
  'P0_In3_tail_to_P1_old_via_gap':g3.distance(Point(10.16087,11.17593).buffer(.225,resolution=256)),
  'new_via_nearest_foreign_copper':minimum(vp,[(o,l,p) for o,l,p in local if l not in ['In1.Cu','In4.Cu'] and o['net']!='SERVO2_MCU']),
  'new_via_drill_to_nearest_SMT_mask_both_faces':minimum(vd,masks),
  'new_via_drill_to_nearest_drill':minimum(vd,[(o,'drill',p) for o,p in drills]),
  'new_via_to_reused_P1_via_copper_gap':vp.distance(Point(10.16087,11.17593).buffer(.225,resolution=256)),
  'new_via_to_count2_P1_In2_first_segment_gap':vp.distance(LineString([[10.16087,11.17593],[11.10242,11.17593]]).buffer(.0635,resolution=256)),
  'P0_pad_entry':finite_entry(p0points),'P1_pad_entry':finite_entry(p1points),
  'new_via_intersected_via_keepouts':[z['uuid'] for z in n['zones'] if z.get('rule') and z.get('forbid',{}).get('vias') and vp.intersects(geom(z['outline']))]},
 'rejected_alternatives':[
  {'proposal':'North U12.3→(13.45,10.75) and immediate via','local_trace_clear':True,'blockers':['B.Cu R9.1 HSE_OUT pad203f6260-eda5-4649-ad70-6ace4fd2c9c7; its B.Mask overlaps drill.','B.Cu HSE_OUT track7e13fb09-b2e8-41ee-b2c7-ed26adf964c7.']},
  {'proposal':'North then west at y10.75','blockers':['F.Cu GND tracks4bdbc594-f503-4ac4-887a-602087e810a5 and651dd4bb-367c-4146-91ab-c7b2cafdcd9c. Raising to y10.47 still conflicts GND via7aa57d39-de74-4e59-ae7e-b321426a2b13.']},
  {'proposal':'Immediate south vias around(13.45,12.95) and(13.7,12.95)','blockers':['B.Cu Y1.3 HSE_XTAL_OUT copper/mask, HSE_OUT trace, GND stitching vias and +3V3_ANALOG.']},
  {'proposal':'Northeast track to x14.03 then y8.5','blockers':['F.Cu +3V3_CORE segment0692c3f1-6488-4fcf-8901-212399ef3c1d at y8.6. Adjacent via pockets additionally restricted by HSE/analog copper.']},
  {'proposal':'P0 new In3 tail via x10.7 from y9.49774 directly to10.7','blockers':['GND through-viafdbceb98-66ac-414b-90c2-14e8474996af at(10.874,9.9139). Use the explicit replacement tail instead.']}],
 'validation_still_required':['Validate removal and logical ownership of every affected source32 object.','Screen entire count2 P1 In2/B.Cu continuation against all source32 geometry and the replacement P0.','Native full-width finite actual-pad and annular entries, actual U12.3 cut/outside-gap on all layers, native DRC/open count, full process/drill-to-both-masks and all-drill gaps, tenting, GND-only In1/In4 policy, unchanged critical/power/process/placement gates.','No manufacturing-margin, numerical-power or transient-protection qualification claim is made.']}
path=ROOT/'servo2-local-review/review.json';path.write_text(json.dumps(out,indent=2)+'\n');print(str(path));print(json.dumps({'proposal_file_sha256':sha(path),'source_board_sha256':n['board_sha256'],'files_hashed':len(out['source_hashes']),'removed_tracks':len(old_f_ids)+1,'outside_pad_gap':out['local_screen_measurements_mm']['P0_P1_F_Cu_outside_actual_pad_gap'],'entries':[out['local_screen_measurements_mm']['P0_pad_entry'],out['local_screen_measurements_mm']['P1_pad_entry']]}))
