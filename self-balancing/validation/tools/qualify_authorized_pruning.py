#!/usr/bin/python3
"""Bind the six explicitly approved redundant vias and their terminal trees.

This proof permits only the named source objects. It does not grant permission
to remove another via or a functional current path. All surviving terminals,
actual copper joins, complete native DRC and independent pad gates remain required.
"""
import argparse,collections,hashlib,json,os
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
from audit_single_terminal_copper import inventory
FROZEN='fafa9c3f0efc570ab70c69d45ffb7bfc7e548dae520a391ed167540ffccf6c6a'
NAMED={
 '9c197846-e3b5-4a56-9a25-a11e9b673ef5':'+5V_STACK',
 '0339b82d-3353-4627-9f03-57d192f6ea21':'FDCAN1_RX',
 '5a501fc3-ea58-40d5-9413-78ad9c4f02b6':'IMU_CS',
 'cc569dba-8c17-4a1b-a17d-55d48ca98df2':'IMU_CS',
 '24ff4382-6c48-4794-abe9-9a57776d555d':'UART3_TX',
 'b1deabfa-acc0-4236-bcdc-9327e2653b94':'USB_SOURCE_DISABLE'}
SAMPLE='060b047c-d688-49da-9f40-03b3572d6506'
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();uid=lambda t:t.m_Uuid.AsString()
def via_rec(t):
 return {'uuid':uid(t),'type':t.GetClass(),'net':t.GetNetname(),'start_nm':[t.GetStart().x,t.GetStart().y],'end_nm':[t.GetEnd().x,t.GetEnd().y],'width_nm':t.GetWidth(p.F_Cu),'drill_nm':t.GetDrillValue(),'layers':[t.TopLayer(),t.BottomLayer()],'via_type':int(t.GetViaType()),'tented_front':t.IsTented(p.F_Cu),'tented_back':t.IsTented(p.B_Cu)}
def plane(b,l):
 out=p.SHAPE_POLY_SET()
 for z in b.Zones():
  if z.GetNetname()=='GND' and not z.GetIsRuleArea() and z.IsOnLayer(l) and z.HasFilledPolysForLayer(l):out.BooleanAdd(z.GetFilledPolysList(l))
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--dead-tree-report',type=Path,required=True);ap.add_argument('--retirement-patch',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert sha(a.source)==FROZEN and sha(a.candidate)==a.sha256;errors=[]
 def check(ok,msg):
  if not ok:errors.append(msg)
 old=p.LoadBoard(str(a.source));new=p.LoadBoard(str(a.candidate));av={uid(q):q for q in old.GetTracks() if isinstance(q,p.PCB_VIA)};bv={uid(q):q for q in new.GetTracks() if isinstance(q,p.PCB_VIA)};oldvia={u:via_rec(q) for u,q in av.items()};newvia={u:via_rec(q) for u,q in bv.items()};check(set(av)-set(bv)==set(NAMED) and not(set(bv)-set(av)),'Via inventory differs beyond exact six approved deletions');check(all(newvia[u]==r for u,r in oldvia.items() if u not in NAMED),'Surviving via record changed');check(len(bv)==406 and sum(q.GetNetname()=='GND' for q in bv.values())==97,'Expected406 total/97 GND vias');check(all(av[u].GetNetname()==n for u,n in NAMED.items()),'Named via net differs')
 census=inventory(a.source);retired_components=[];current_ids={uid(q) for q in new.GetTracks()};allowed={*NAMED,'de4a9077-676b-415b-8ad2-3e996940fd62'}
 for q in census['candidates']:
  if len(q['terminals'])!=1 or q['terminals'][0]['uuid'] not in allowed:continue
  check(not q['filled_zone_contacts'],'Removed one-terminal branch contacted filled zone');check(all(t['uuid'] not in current_ids for t in q['tracks']),'Approved redundant branch still present');retired_components.append(q)
 check(len(retired_components)==6 and sum(q['track_count'] for q in retired_components)==14,'Expected exact six single-terminal components/fourteen tracks')
 trees=json.loads(a.dead_tree_report.read_text());check(trees['candidate_sha256']==FROZEN and trees['audit_script_sha256']==sha(Path(__file__).with_name('audit_pad_anchored_dead_trees.py')),'Dead-tree source or method differs');tree_vias={q['uuid'] for t in trees['review_trees'] for q in t['peeled_vias']};check(tree_vias<=set(NAMED) and 'cc569dba-8c17-4a1b-a17d-55d48ca98df2' in tree_vias,'Dead-tree via set exceeds authorization');oldtracks={uid(q):q for q in old.GetTracks() if not isinstance(q,p.PCB_VIA)};seen={frozenset(t['uuid'] for t in q['tracks']) for q in retired_components}
 for tree in trees['review_trees']:
  check(tree['remaining_attachment_count']==1,'Pruned tree has more than one live anchor')
  for comp in tree['peeled_trace_components']:
   ids=frozenset(comp['track_uuids'])
   if ids in seen:continue
   seen.add(ids);tracks=[]
   for u in sorted(ids):
    q=oldtracks[u];tracks.append({'uuid':u,'start_mm':[q.GetStart().x/1e6,q.GetStart().y/1e6],'end_mm':[q.GetEnd().x/1e6,q.GetEnd().y/1e6],'width_mm':q.GetWidth()/1e6});check(u not in current_ids,'Retired dangling-tree track remains')
   retired_components.append({'net':comp['net'],'layer':comp['layer'],'track_count':len(tracks),'tracks':tracks,'classification':'PAD-ANCHORED DANGLING TREE COMPONENT','sole_remaining_anchor':tree['remaining_attachment_nodes'][0]})
 check(len(retired_components)==9 and sum(q['track_count'] for q in retired_components)==31,'Expected exact nine retired components/thirty-one tracks')
 packet=json.loads(a.retirement_patch.read_text());stage_path=Path(packet['source']);check(sha(stage_path)==packet['source_sha256'],'Retirement source stage hash differs');stage=p.LoadBoard(str(stage_path));stage_tracks={uid(q):q for q in stage.GetTracks() if not isinstance(q,p.PCB_VIA)};final_tracks={uid(q):q for q in new.GetTracks() if not isinstance(q,p.PCB_VIA)}
 def trec(q):return {'id':uid(q),'net':q.GetNetname(),'layer':q.GetLayerName(),'start':[q.GetStart().x/1e6,q.GetStart().y/1e6],'end':[q.GetEnd().x/1e6,q.GetEnd().y/1e6],'width_mm':q.GetWidth()/1e6}
 arm=packet['changes'][0];arm_ids={'600fdad2-5338-4463-b801-5d2be184dc45','baf1a6c6-4f28-4d59-9d7d-0d3a1c802805','af2715c3-64ab-45dc-b5ea-caf225d7d34e','3d896c3a-8947-4ee0-8d18-f4ddb280b19e','efeb1491-4037-4cb4-bf79-23468fc0eadd'};check({q['id'] for q in arm['removed']}==arm_ids and not arm['added'],'Rail dead-arm record set differs');arm_native=[stage_tracks[u] for u in arm_ids];contacts=[]
 for q in list(stage.GetTracks())+[pd for f in stage.GetFootprints() for pd in f.Pads()]:
  if uid(q) in arm_ids or uid(q) in NAMED or q.GetNetname()!='+5V_STACK' or not q.IsOnLayer(p.B_Cu):continue
  if any(q.GetEffectiveShape(p.B_Cu).GetClearance(t.GetEffectiveShape(p.B_Cu))<=0 for t in arm_native):contacts.append(q)
 expected_contacts={'7cadd0ad-2bc5-488d-9a2b-18e8e241963b','8335836a-57d1-4bbf-87aa-1a65b6884959','8fb33d82-cbfe-41e1-b291-8e14e9688a95'};check({uid(q) for q in contacts}==expected_contacts,'Rail dead arm touches an additional terminal/path');junction=p.VECTOR2I(27650000,9300000)
 check(all(not isinstance(q,(p.PAD,p.PCB_VIA)) and (q.GetStart()==junction or q.GetEnd()==junction) and q.GetWidth()==450000 and uid(q) in final_tracks and trec(final_tracks[uid(q)])==trec(q) for q in contacts),'Genuine full-width rail junction changed')
 retired_components.append({'net':'+5V_STACK','layer':'B.Cu','track_count':5,'tracks':[{'uuid':r['id'],'start_mm':r['start'],'end_mm':r['end'],'width_mm':r['width_mm']} for r in arm['removed']],'classification':'DEAD ARM TO ONE UNCHANGED FULL-WIDTH JUNCTION','sole_remaining_junction_mm':[27.65,9.3],'retained_junction_tracks':[trec(q) for q in contacts]})
 pruned_ids={q['uuid'] for c in retired_components for q in c['tracks']};bridge_proofs=[];retirement_ids=[]
 for i,ch in enumerate(packet['changes']):
  for r in ch['removed']:check(r['id'] in stage_tracks and trec(stage_tracks[r['id']])==r,'Retirement removed record differs from native source')
  for r in ch['added']:check(r['id'] in final_tracks and trec(final_tracks[r['id']])==r,'Retirement added record differs from final native')
  retirement_ids.extend(q['id'] for q in ch['removed_vias'])
  if not ch['added']:check({r['id'] for r in ch['removed']}<=pruned_ids,'Unproved pure deletion in retirement operation')
  for layer in {r['layer'] for r in ch['added']}:
   l=new.GetLayerID(layer);source_copper=p.SHAPE_POLY_SET();added_copper=p.SHAPE_POLY_SET()
   for q in stage.GetTracks():
    if q.GetNetname()==ch['net'] and q.IsOnLayer(l):poly=p.SHAPE_POLY_SET();q.TransformShapeToPolygon(poly,l,0,50,p.ERROR_OUTSIDE);source_copper.BooleanAdd(poly)
   for r in ch['added']:
    if r['layer']==layer:q=final_tracks[r['id']];poly=p.SHAPE_POLY_SET();q.TransformShapeToPolygon(poly,l,0,50,p.ERROR_OUTSIDE);added_copper.BooleanAdd(poly);check(q.GetWidth()>=130000,'Retirement planar bridge below signal floor')
   outside=p.SHAPE_POLY_SET(added_copper);outside.BooleanSubtract(source_copper);expanded=p.SHAPE_POLY_SET(source_copper);expanded.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);outside_rounding=p.SHAPE_POLY_SET(added_copper);outside_rounding.BooleanSubtract(expanded);check(outside_rounding.Area()==0,'Planar replacement exceeds prior native copper beyond2nm rounding');bridge_proofs.append({'operation_index':i,'net':ch['net'],'layer':layer,'added_outside_source_copper_mm2':outside.Area()/1e12,'added_outside_source_copper_plus_2nm_mm2':outside_rounding.Area()/1e12})
 check(len(retirement_ids)==6 and set(retirement_ids)==set(NAMED),'Retirement patch changes other vias')
 # Require each retired via to have exactly one real layer before retirement.
 role=[]
 for u,n in NAMED.items():
  comps=[r for r in census['all_component_terminal_inventory'] if len(r['terminals'])>1 and any(t['uuid']==u for t in r['terminals'])];layers={r['layer'] for r in comps};check(len(layers)==1 or u in tree_vias,'Retired via had multiple functional routing layers outside a pad-anchored dead tree: '+u);role.append({'via':oldvia[u],'functional_layer':next(iter(layers)) if len(layers)==1 else None,'pad_anchored_dead_tree':u in tree_vias,'former_functional_components':comps})
 # Gains in reference planes may only close these exact own-via antipads.
 # Never use the whole of a merged hole as an allowance.
 planes=[];drilledpads=[q for f in old.GetFootprints() for q in f.Pads() if q.HasHole()]
 oracle=p.LoadBoard(str(a.source))
 for q in list(oracle.GetTracks()):
  if uid(q) in NAMED:oracle.Remove(q)
 oracle.BuildConnectivity();filler=p.ZONE_FILLER(oracle);check(filler.Fill(oracle.Zones()),'Independent six-via-only refill failed')
 for l in [p.In1_Cu,p.In3_Cu,p.In4_Cu]:
  A=plane(old,l);B=plane(new,l);loss=p.SHAPE_POLY_SET(A);loss.BooleanSubtract(B);gain=p.SHAPE_POLY_SET(B);gain.BooleanSubtract(A);sample=av[SAMPLE];templates=[]
  for oi in range(A.OutlineCount()):
   for hi in range(A.HoleCount(oi)):
    h=p.SHAPE_POLY_SET(A.CHole(oi,hi))
    if not h.Contains(sample.GetPosition()):continue
    residents=[uid(v) for v in av.values() if v.IsOnLayer(l) and h.Contains(v.GetPosition())];padres=[uid(v) for v in drilledpads if h.Contains(v.GetPosition())];check(residents==[SAMPLE] and not padres,'Reference template is not an isolated single-via hole');templates.append(h)
  check(len(templates)==1,'Isolated antipad template missing')
  allowance=p.SHAPE_POLY_SET();template=templates[0] if templates else p.SHAPE_POLY_SET()
  for u in NAMED:
   v=av[u];check((v.GetWidth(l),v.GetDrillValue(),v.GetOwnClearance(l),str(v.GetNetClassName()))==(sample.GetWidth(l),sample.GetDrillValue(),sample.GetOwnClearance(l),str(sample.GetNetClassName())),'Removed via differs from exact antipad template');x=p.SHAPE_POLY_SET(template);x.Move(v.GetPosition()-sample.GetPosition());allowance.BooleanAdd(x)
  allowance.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);expanded_old=p.SHAPE_POLY_SET(A);expanded_old.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);expanded_new=p.SHAPE_POLY_SET(B);expanded_new.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);outside_loss=p.SHAPE_POLY_SET(A);outside_loss.BooleanSubtract(expanded_new);outside=p.SHAPE_POLY_SET(gain);outside.BooleanSubtract(expanded_old);outside.BooleanSubtract(allowance)
  predicted=plane(oracle,l);predicted_expanded=p.SHAPE_POLY_SET(predicted);predicted_expanded.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);oracle_loss=p.SHAPE_POLY_SET(predicted);oracle_loss.BooleanSubtract(B);oracle_gain=p.SHAPE_POLY_SET(B);oracle_gain.BooleanSubtract(predicted);oracle_loss_residual=p.SHAPE_POLY_SET(predicted);oracle_loss_residual.BooleanSubtract(expanded_new);oracle_gain_residual=p.SHAPE_POLY_SET(B);oracle_gain_residual.BooleanSubtract(predicted_expanded)
  check(outside_loss.Area()==0 and oracle_loss_residual.Area()==oracle_gain_residual.Area()==0,'Reference plane differs from exact six-via-only refill beyond2nm rounding');planes.append({'layer':new.GetLayerName(l),'loss_mm2':loss.Area()/1e12,'gain_mm2':gain.Area()/1e12,'loss_beyond_2nm_boundary_mm2':outside_loss.Area()/1e12,'gain_outside_translated_isolated_templates_mm2':outside.Area()/1e12,'exact_six_via_only_refill_loss_mm2':oracle_loss.Area()/1e12,'exact_six_via_only_refill_gain_mm2':oracle_gain.Area()/1e12,'exact_six_via_only_refill_loss_beyond_2nm_mm2':oracle_loss_residual.Area()/1e12,'exact_six_via_only_refill_gain_beyond_2nm_mm2':oracle_gain_residual.Area()/1e12,'rounding_envelope_nm':2,'template_uuid':SAMPLE,'template_area_mm2':template.Area()/1e12,'merged_hole_disposition':'Exact native source board refilled after deleting only the six named vias; every other source object and zone definition retained. This captures local native merged-hole fillets without allowing arbitrary merged-hole area.'})
 out={'status':'PASS EXACT REDUNDANT VIA/STUB PRUNING' if not errors else 'NOT PASSED','source':str(a.source),'source_sha256':FROZEN,'candidate':str(a.candidate),'candidate_sha256':a.sha256,'errors':errors,'audit_script_sha256':sha(Path(__file__)),'removed_via_records':[oldvia[u] for u in sorted(NAMED)],'retired_terminal_components':retired_components,'former_via_functional_roles':role,'reference_plane_delta':planes,'remaining_via_count':len(bv),'ground_via_count':sum(q.GetNetname()=='GND' for q in bv.values()),'all_other_via_records_unchanged':all(newvia.get(u)==r for u,r in oldvia.items() if u not in NAMED),'retirement_patch':{'path':str(a.retirement_patch),'sha256':sha(a.retirement_patch),'source':str(stage_path),'source_sha256':packet['source_sha256']},'exact_retirement_operations':packet['changes'],'planar_bridge_proofs':bridge_proofs,'limits':__doc__};assert sha(a.source)==FROZEN and sha(a.candidate)==a.sha256;a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k in ['status','errors','remaining_via_count','ground_via_count','reference_plane_delta']},indent=2));return bool(errors)
if __name__=='__main__':raise SystemExit(main())
