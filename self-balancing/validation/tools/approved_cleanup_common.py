"""Shared binding of the explicitly reviewed six-via retirement proof."""
import hashlib,json
from pathlib import Path
from qualify_authorized_pruning import NAMED,FROZEN
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
def load_cleanup(exceptions,candidate_sha):
 spec=exceptions.get('redundant_cleanup_proof')
 if not spec:return None
 path=Path(spec['path']);assert sha(path)==spec['sha256'];q=json.loads(path.read_text());assert q['candidate_sha256']==candidate_sha and q['source_sha256']==FROZEN and sha(Path(q['source']))==FROZEN
 assert q['status']=='PASS EXACT REDUNDANT VIA/STUB PRUNING' and not q['errors'];assert q['audit_script_sha256']==sha(Path(__file__).with_name('qualify_authorized_pruning.py'))
 assert {r['uuid']:r['net'] for r in q['removed_via_records']}==NAMED
 assert q['remaining_via_count']==406 and q['ground_via_count']==97 and q['all_other_via_records_unchanged']
 assert len(q['reference_plane_delta'])==3 and all(r['loss_beyond_2nm_boundary_mm2']==r['exact_six_via_only_refill_loss_beyond_2nm_mm2']==r['exact_six_via_only_refill_gain_beyond_2nm_mm2']==0 for r in q['reference_plane_delta'])
 assert sha(Path(q['retirement_patch']['path']))==q['retirement_patch']['sha256'] and sha(Path(q['retirement_patch']['source']))==q['retirement_patch']['source_sha256']
 return q
def component_records(component):
 return {t['uuid']:{'id':t['uuid'],'net':component['net'],'layer':component['layer'],'start':t['start_mm'],'end':t['end_mm'],'width_mm':t['width_mm']} for t in component['tracks']}
