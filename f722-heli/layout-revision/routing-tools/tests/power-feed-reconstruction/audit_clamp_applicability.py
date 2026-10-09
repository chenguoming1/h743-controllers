"""Bind four clamp bridges and prove candidate19 power/reference inputs unchanged."""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[1]
sys.path.insert(0,str(R/'native-tools'))
from check_protection_paths import make_graph
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
A=R/'candidate19';B=R/'candidate20';before=json.loads((A/'f722-heli.native.json').read_text());after=json.loads((B/'f722-heli.native.json').read_text());proposal=json.loads((HERE/'clamp-bridges-prepared/proposal.json').read_text());logical=json.loads((B/'f722-heli.logical-route-map.json').read_text());power=json.loads((A/'power-audit.json').read_text())
assert before['board_sha256']==sha(A/'f722-heli.kicad_pcb')==proposal['source_board_sha256']==power['board_sha256'];assert after['board_sha256']==sha(B/'f722-heli.kicad_pcb')==logical['board_sha256']
old={o['uuid']:o for o in before['objects']};now={o['uuid']:o for o in after['objects']};assert all(now.get(u)==o for u,o in old.items());new=[o for u,o in now.items()if u not in old]
assert len(new)==4 and all(o['kind']=='track'and list(o['copper'])==['F.Cu']and o['width']==.127 for o in new)
assert before['zones']==after['zones'] and before['edge_cuts']==after['edge_cuts'] and before['footprints']==after['footprints'] and before['copper_layers']==after['copper_layers']
group=lambda n,net:sorted([sorted({v['object']['key']for v in g if v['object']['kind']=='pad'})for g in make_graph([o for o in n['objects']if o['net']==net])if any(v['object']['kind']=='pad'for v in g)])
rows=[]
for q in proposal['branches']:
 matches=[o for o in new if o['net']==q['net']];assert len(matches)==1;t=matches[0]
 assert [t['start'],t['end']]==q['points'] and logical['logical_route_map'][t['uuid']]==q['logical_net']
 g0=group(before,q['net']);g1=group(after,q['net']);assert len(g1)==len(g0)-1
 assert sorted(q['terminals'])in g1
 rows.append(dict(net=q['net'],logical_net=q['logical_net'],track_uuid=t['uuid'],terminals=q['terminals'],source_groups=g0,result_groups=g1,endpoints=q['endpoints'],min_foreign_or_other_branch_gap_mm=q['min_foreign_or_other_branch_gap_mm']))
domains={}
for net in power['nets']:
 x=[o for o in before['objects']if o['net']==net];y=[o for o in after['objects']if o['net']==net];assert x==y
 zones=[z for z in before['zones']if z['net']==net];digest=hashlib.sha256(json.dumps(dict(objects=x,zones=zones),sort_keys=True,separators=(',',':')).encode()).hexdigest();domains[net]=dict(object_count=len(x),zone_count=len(zones),identical_native_domain_sha256=digest)
holes0=[o for o in before['objects']if o.get('drill')];holes1=[o for o in after['objects']if o.get('drill')];assert holes0==holes1
paired={}
for p in sorted(A.rglob('*')):
 if not p.is_file()or not(p.suffix in ['.kicad_sch','.kicad_pro','.kicad_dru','.kicad_mod','.kicad_sym']or p.name in ['parts.json','fp-lib-table','sym-lib-table']):continue
 q=B/p.relative_to(A);assert q.is_file()and sha(p)==sha(q);paired[str(p.relative_to(A))]=sha(p)
r=dict(passed=True,source_board_sha256=before['board_sha256'],board_sha256=after['board_sha256'],source_native_sha256=sha(A/'f722-heli.native.json'),native_sha256=sha(B/'f722-heli.native.json'),audit_source_sha256=sha(Path(__file__)),all1653_source_objects_exact=True,all_footprints_and_poses_exact=True,all_saved_zones_and_reference_fills_exact=True,all_drill_objects_exact=True,new_tracks=4,new_vias=0,all_28_power_domains_exact=domains,paired_project_schematic_library_hashes=paired,logical_branch_results=rows,power_applicability='Candidate20 changes only four ordinary F.Cu clamp bridges; all candidate19 conductive power/ground objects, pads, drills, saved fills, component poses and paired circuits are exact. A candidate19 numerical receipt can be conditionally applied to these unchanged DC model inputs after the owner validates the complete job/contact/material binding. No new solve or numerical pass is claimed here.')
(B/'unchanged-power-reference.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,board_sha256=r['board_sha256'],source_board_sha256=r['source_board_sha256'],branch_reductions=4,power_domains=len(domains),paired_files=len(paired))))
