import json,pathlib,hashlib,math,collections,sys
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
H=pathlib.Path(__file__).resolve().parent;D=H/'candidate03';R=H.parents[2]
read=lambda p:json.loads(pathlib.Path(p).read_text());sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def geom(ps):return unary_union([Polygon(p['outer'],p.get('holes',[]))for p in ps])
g=read(D/'f722-heli.native.json');prov=read(D/'construction-provenance.json');ref=read(D/'tail-reference/reference-review.json');ob=g['objects'];by={o['uuid']:o for o in ob};h=sha(D/'f722-heli.kicad_pcb');assert h==g['board_sha256']==ref['board_sha256']
mask=[(o,l,geom(ps))for o in ob if o.get('smd')for l,v in o.get('mask',{}).items() for ps in [v['polygons']]]
drills=[(o,geom(o['drill']['outside']))for o in ob if o.get('drill')]
copper=[(o,l,geom(ps))for o in ob for l,ps in o.get('copper',{}).items()]
outline=geom(g['outline_with_npth']['polygons']);newvias=[by[o['uuid']]for o in prov['added_records']if o['kind']=='via'];margins=[]
for v in newvias:
 drill=geom(v['drill']['outside']);vc={l:geom(ps)for l,ps in v['copper'].items()}
 gm,mo,ml=min((drill.distance(s),o['key'],l)for o,l,s in mask)
 gd,du=min((drill.distance(s),o['uuid'])for o,s in drills if o['uuid']!=v['uuid'])
 gc,cu,cl,cn=min((vc[l].distance(s),o['uuid'],l,o['net'])for o,l,s in copper if o['net']!=v['net']and l in vc)
 ge=drill.distance(outline.boundary)
 row=dict(uuid=v['uuid'],net=v['net'],xy_mm=v['xy'],drill_to_SMT_mask_mm=gm,limiting_mask=mo,mask_layer=ml,drill_to_drill_mm=gd,other_drill_uuid=du,copper_clearance_mm=gc,other_copper_uuid=cu,other_copper_net=cn,copper_layer=cl,drill_to_edge_or_NPTH_mm=ge,drill_inside_outline=outline.covers(drill),excess_over_rules_mm=dict(mask=gm-.2,drill=gd-.25,copper=gc-.127,edge_NPTH=ge-.254),tented=v['tented'])
 assert all(x>=-1e-8 for x in row['excess_over_rules_mm'].values())and row['drill_inside_outline'];margins.append(row)
residual=[]
for t in ref['tracks']:
 if t['net']!='TAIL_MCU':continue
 for f in t['trace_width_missing_by_class']['saved_void_or_edge_outside_own_window']:
  holes=[ref['saved_holes'][t['reference_layer']][i]for i in f['saved_hole_indices']]
  containing_pads=[{'key':o['key'],'net':o['net'],'xy_mm':o['xy']}for o in ob if o['kind']=='pad'and any(box['bounds_mm'][0]<=o['xy'][0]<=box['bounds_mm'][2]and box['bounds_mm'][1]<=o['xy'][1]<=box['bounds_mm'][3]for box in holes)]
  residual.append({'track_uuid':t['track_uuid'],'signal_layer':t['signal_layer'],'reference_layer':t['reference_layer'],'fragment':f,'saved_holes':holes,'pads_within_hole_bounds':containing_pads,'classification':'Other connector pad antipad'if t['track_uuid']=='177bef1f-34aa-51f8-b484-47f9cba8be84'else'Other-net merged via void'if t['track_uuid']=='8eb1d2be-c127-560a-920c-7e19331e990e'else'Own TAIL via plus BARO_SCL merged antipad; this fragment remains outside own window'})
length=read(H/'signal-review/tail-path-comparison.json')['candidate03']['paths']['U1.55__U12.6']['planar_track_length_mm'];delay=[{'assumed_uniform_effective_epsilon':e,'one_way_ns':length*math.sqrt(e)/299.792458,'round_trip_ns':2*length*math.sqrt(e)/299.792458}for e in[2.8,4.1,4.4]]
out={'schema':'f722-TAIL-margin-reference-details/v1','board_sha256':h,'native_sha256':sha(D/'f722-heli.native.json'),'via_process_margins':margins,'TAIL_reference_totals':ref['nets']['TAIL_MCU'],'TAIL_outside_window_width_fragments':residual,'TAIL_transitions':[t for t in ref['transitions']if t['net']=='TAIL_MCU'],'GND_native_pad_groups_exactly_preserved':read(D/'power-audit.json')['ground_native_pad_groups_exactly_preserved'],'GND_ties_verified_against_both_saved_planes':len(ref['GND_ties']['accepted']),'propagation_sensitivity':delay,'propagation_model_limits':'Uniform effective permittivity scenarios, not field-solved impedance or dielectric tolerance guarantees; track lengths include land entries but omit package and vertical-barrel delay. Four through-vias retain their unused barrel stubs. No transmission-line waveform or external cable model is simulated.','geometry_method':'Actual saved native polygons and drill envelopes. No snapping, normalization, polygon repair or suppression of small residuals. Own windows are labels and not electrical waivers.'}
(D/'signal-geometry-details.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'board':h,'vias':margins,'residual_area_mm2':sum(r['fragment']['area_mm2']for r in residual),'delay':delay}))
