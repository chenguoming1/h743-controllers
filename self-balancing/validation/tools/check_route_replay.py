#!/usr/bin/python3
"""Independent exact operation replay and current-path width proof.

Every removed record must equal the current native inventory, then the full
sequence must reproduce the final track inventory. Rail replacements preserve
the maximum width of each removed run; ordinary low-current traces stay at or
above .130mm. Protected exceptions are additionally checked by the native
geometry gate. No native source is saved.
"""
import argparse,collections,hashlib,json,os
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
from approved_cleanup_common import load_cleanup,component_records
BASELINE='6e2031b040ce8f3a534c2f73abb0091e25b3e6adcab982463264ad8898d65cf8'
RAILS={'GND','3V3_CORE','VLOGIC_IN','+5V_STACK','VDDA','IMU_3V3','USB_VBUS','/power/USB_VBUS_SLEW','/power/BUCK_SW','/power/BUCK_VIN','/power/BUCK_OUT'}
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
def inventory(path):
 b=p.LoadBoard(str(path));return {t.m_Uuid.AsString():{'id':t.m_Uuid.AsString(),'net':t.GetNetname(),'layer':t.GetLayerName(),'start':[round(p.ToMM(t.GetStart().x),6),round(p.ToMM(t.GetStart().y),6)],'end':[round(p.ToMM(t.GetEnd().x),6),round(p.ToMM(t.GetEnd().y),6)],'width_mm':round(p.ToMM(t.GetWidth()),6)} for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)}
def record(q):return {k:q[k] for k in ['id','net','layer','start','end','width_mm']}
def duplicate_covered(q,cur):
 return any(v['net']==q['net'] and v['layer']==q['layer'] and v['width_mm']>=q['width_mm'] and (v['start']==q['start'] and v['end']==q['end'] or v['start']==q['end'] and v['end']==q['start']) for v in cur.values())
def copper_union_delta(before,after):
 b=p.BOARD();results=[];keep=[]
 for error in [100,10]:
  def poly(rows):
   union=p.SHAPE_POLY_SET()
   for r in rows:
    t=p.PCB_TRACK(b);l=b.GetLayerID(r['layer']);t.SetLayer(l);t.SetWidth(round(r['width_mm']*1e6));t.SetStart(p.VECTOR2I(*[round(v*1e6) for v in r['start']]));t.SetEnd(p.VECTOR2I(*[round(v*1e6) for v in r['end']]));keep.append(t);q=p.SHAPE_POLY_SET();t.TransformShapeToPolygon(q,l,0,error,p.ERROR_OUTSIDE);union.BooleanAdd(q)
   return union
  A=poly(before);B=poly(after);loss=p.SHAPE_POLY_SET(A);loss.BooleanSubtract(B);gain=p.SHAPE_POLY_SET(B);gain.BooleanSubtract(A);results.append({'polygon_error_nm':error,'loss_mm2':loss.Area()/1e12,'gain_mm2':gain.Area()/1e12})
 return results
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--patch',type=Path,action='append',default=[]);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--pruning-proof',type=Path);ap.add_argument('--approved-pruning',type=Path);ap.add_argument('--exceptions',type=Path);ap.add_argument('--selfcheck',action='store_true');a=ap.parse_args();assert sha(a.baseline)==BASELINE and sha(a.candidate)==a.sha256
 cleanup=load_cleanup(json.loads(a.exceptions.read_text()),a.sha256) if a.exceptions else None
 approved_stubs=[component_records(q) for q in cleanup['retired_terminal_components']] if cleanup else []
 A=inventory(a.baseline);B=inventory(a.candidate);cur=dict(A);errors=[];checks=[];patches=[];pruning=None
 if a.approved_pruning:
  pruning=json.loads(a.approved_pruning.read_text());assert a.pruning_proof,'Approved pruning requires independent exact local proof'
  proof=json.loads(a.pruning_proof.read_text())
  assert pruning['source_sha256']==proof['source_sha256'] and sha(Path(proof['source_path']))==proof['source_sha256'] and proof['proposal_sha256']==sha(a.approved_pruning) and not proof['errors']
  assert pruning['pad_id']==proof['pad_uuid']=='f033bae3-30e5-46a0-9885-a09cf30a9873' and len(pruning['delta']['removed'])==proof['deleted_tracks'] and not pruning['delta']['added']
  for q in pruning['retained_original_contact_edges']:
   if B.get(q['id'])!=record(q):errors.append('Approved J162 feed record changed: '+q['id'])
 for path in a.patch:
  data=json.loads(path.read_text());patches.append({'path':str(path),'sha256':sha(path),'claimed_source_sha256':data.get('source_sha256'),'claimed_candidate_sha256':data.get('candidate_sha256')})
  for i,ch in enumerate(data['changes']):
   label=path.name+':'+str(i);removed=[record(q) for q in ch['removed']];added=[record(q) for q in ch['added']];match=all(cur.get(q['id'])==q for q in removed)
   if not match:errors.append('Removed record differs from independent replay: '+label)
   nets={q['net'] for q in removed+added};layers={q['layer'] for q in removed+added}
   approved_retirement=bool(cleanup and ch in cleanup['exact_retirement_operations'])
   if len(nets)!=1 or len(layers)!=1 and not approved_retirement:errors.append('Operation crosses nets/layers without exact retirement proof: '+label)
   for q in removed:cur.pop(q['id'],None)
   for q in added:
    if q['id'] in cur:errors.append('Added UUID already exists: '+label)
    cur[q['id']]=q
   source_widths=sorted({q['width_mm'] for q in removed});new_widths=sorted({q['width_mm'] for q in added});israil=bool(nets&RAILS);preserved=min(new_widths)>=max(source_widths) if new_widths and source_widths else False;duplicate=False;approved_pruned=False;union_check=[];approved_stub=not added and {q['id']:q for q in removed} in approved_stubs
   if israil:
    if not removed and added:preserved=all(q['width_mm']>=.13 for q in added)
    if not added:
     duplicate=all(duplicate_covered(q,cur) for q in removed)
     approved_pruned=bool(pruning and {q['id']:q for q in removed}=={q['id']:record(q) for q in pruning['delta']['removed']})
     preserved=duplicate or approved_pruned or approved_stub
     if approved_pruned:
      for q in pruning['retained_original_contact_edges']:
       if cur.get(q['id'])!=record(q):errors.append('Rebased J162 feed differs at exact replay stage: '+q['id'])
    if not preserved and added:
     union_check=copper_union_delta(removed,added);preserved=all(r['loss_mm2']==r['gain_mm2']==0 for r in union_check)
    if not preserved:errors.append('Rail path width reduced or deleted without exact duplicate coverage: '+label+' '+str(nets))
   elif any(q['width_mm']<.13 for q in added):errors.append('Ordinary added track narrower than .130mm: '+label)
   checks.append({'patch':str(path),'index':i,'operation':ch.get('operation'),'net':next(iter(nets)) if nets else None,'layer':next(iter(layers)) if layers else None,'removed_count':len(removed),'added_count':len(added),'source_records_verified':match,'source_widths_mm':source_widths,'new_widths_mm':new_widths,'rail':israil,'rail_width_preserved':preserved if israil else None,'source_copper_unchanged_additive_operation':not removed and bool(added),'exact_duplicate_coverage':duplicate,'approved_J162_pad_redundancy':approved_pruned,'approved_exact_single_terminal_component':approved_stub,'exact_copper_union_checks':union_check,'ordinary_width_floor':all(q['width_mm']>=.13 for q in added)})
 difference={u:{'replayed':cur.get(u),'native':B.get(u)} for u in sorted(set(cur)|set(B)) if cur.get(u)!=B.get(u)}
 if difference:errors.append('Exact operation replay differs from final native tracks')
 if not a.selfcheck and (not a.patch or not checks):errors.append('No explicit operation packet for P6')
 assert sha(a.baseline)==BASELINE and sha(a.candidate)==a.sha256
 report={'status':('BASELINE REPLAY SELF-CHECK; NOT ACCEPTANCE' if a.selfcheck else 'PASS EXACT OPERATION REPLAY AND CURRENT-PATH WIDTHS') if not errors else 'NOT PASSED','baseline_sha256':BASELINE,'candidate_sha256':a.sha256,'errors':errors,'patches':patches,'approved_pruning_packet':{'path':str(a.approved_pruning),'sha256':sha(a.approved_pruning),'independent_proof':str(a.pruning_proof),'independent_proof_sha256':sha(a.pruning_proof)} if a.approved_pruning else None,'rail_names':sorted(RAILS),'operation_count':len(checks),'rail_operation_count':sum(r['rail'] for r in checks),'replay_differences':difference,'changes':checks,'method':__doc__,'scope':'This gate verifies correspondence and widths; geometry, clearances, topology, local return-path review, and all-route visual review are separate required gates.'}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['changes','replay_differences']},indent=2));return bool(errors)
if __name__=='__main__':raise SystemExit(main())
