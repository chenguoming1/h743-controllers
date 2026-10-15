from pathlib import Path
import pcbnew as k,sys,json,hashlib
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();uid=lambda o:o.m_Uuid.AsString();area=lambda p:abs(p.Area())/1e12;r4=json.loads((O/'source-review/r4-proposal.json').read_text());r18=json.loads((O/'source-review/r18-proposal.json').read_text());ret=json.loads((O/'usb-reference-return-verification.json').read_text());result=[]
for state,D in [('source',S),('candidate',O)]:
 b=k.LoadBoard(str(D/'hardware/nexus-style-fc.kicad_pcb'));tracks={uid(t):t for t in b.GetTracks()};groups={'R4_LED_branch':r4['removed_uuids'] if state=='source' else [x['uuid'] for x in r4['new_tracks']],'R18_divider_5V_branch':r18['removed_uuids']['5V'] if state=='source' else [x['uuid'] for x in r18['new_tracks'] if x['net']=='5V'],'R18_5V_SENSE':r18['removed_uuids']['5V_SENSE'] if state=='source' else [x['uuid'] for x in r18['new_tracks'] if x['net']=='5V_SENSE']}
 for name,ids in groups.items():
  for layer,refs in [('F.Cu',['In1.Cu']),('In3.Cu',['In2.Cu','In4.Cu'])]:
   l=b.GetLayerID(layer);ts=[tracks[u] for u in ids if tracks[u].GetLayer()==l];poly=k.SHAPE_POLY_SET()
   if not ts:continue
   for t in ts:p=k.SHAPE_POLY_SET();t.TransformShapeToPolygon(p,l,0,1,k.ERROR_INSIDE);poly.BooleanAdd(p)
   for ref in refs:
    rl=b.GetLayerID(ref);g=k.SHAPE_POLY_SET()
    for z in b.Zones():
     if z.GetNetname()=='GND' and not z.GetIsRuleArea() and z.IsOnLayer(rl):g.BooleanAdd(z.GetFilledPolysList(rl))
    miss=k.SHAPE_POLY_SET(poly);miss.BooleanSubtract(g);components=[]
    for i in range(g.OutlineCount()):
     q=k.SHAPE_POLY_SET(poly);q.BooleanIntersection(g.UnitSet(i));ar=area(q)
     if ar>1e-10:
      key=f'{ref}:{i}';d=next(x for x in ret['measurements'][state]['filled_components'] if x['id']==key);assert d['finite_via_connected_to_main_ground'];components.append({'id':key,'overlap_area_mm2':ar,'finite_connected_to_main_ground':True})
    result.append({'state':state,'branch':name,'layer':layer,'reference_layer':ref,'track_uuids':[uid(t) for t in ts],'length_mm':sum(t.GetLength()/1e6 for t in ts),'full_width_union_area_mm2':area(poly),'uncovered_area_mm2':area(miss),'ground_coverage_fraction':1-area(miss)/area(poly),'actual_ground_components':components})
# Since all USB primitives remain exact, direct source/candidate projection comparison isolates refill/reference changes.
a=ret['measurements']['source']['full_width_usb_projection'];b=ret['measurements']['candidate']['full_width_usb_projection'];key=lambda x:(x['net'],x['routing_layer'],x['reference_layer']);old={key(x):x for x in a};deltas=[]
for x in b:
 q=old[key(x)];deltas.append({'net_layer_reference':list(key(x)),'before_uncovered_mm2':q['uncovered_area_mm2'],'after_uncovered_mm2':x['uncovered_area_mm2'],'added_uncovered_mm2':x['uncovered_area_mm2']-q['uncovered_area_mm2']});assert abs(x['uncovered_area_mm2']-q['uncovered_area_mm2'])<1e-9
out={'status':'PASS source-bound branch projection measured; every touched actual GND component finitely connected, USB projection unchanged','source_board_sha256':sha(S/'hardware/nexus-style-fc.kicad_pcb'),'candidate_board_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'branch_full_width_projection':result,'unchanged_USB_reference_measurements':deltas,'R4_loading':r4['electrical_width_exception'],'R18_loading_cross_section':r18['cross_section_loading_assessment'],'qualification':'Projection establishes geometric reference presence and finite ground connectivity only. R18 In3 copper has lower cross-section at the same width; measured nominal divider loading is explicitly isolated from shared 5V feeds. R4 current bound assumes nominal 5V and intact 1k resistor. No current/thermal/transient/SI qualification.'};(O/'branch-reference-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
