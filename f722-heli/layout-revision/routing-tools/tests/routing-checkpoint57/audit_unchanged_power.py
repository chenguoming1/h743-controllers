"""Prove exact numerical-domain applicability after add-only outer signal tracks.

This verifies geometry/circuit identity only. The baseline numerical result and
its complete contact, material and load envelope must be bound separately.
"""
import argparse,hashlib,json
from pathlib import Path
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ap=argparse.ArgumentParser(description=__doc__)
for name in ['source','candidate','power-baseline','out']:ap.add_argument('--'+name,type=Path,required=True)
a=ap.parse_args();A=a.source;B=a.candidate;P=a.power_baseline
read=lambda d:json.loads((d/'f722-heli.native.json').read_text())
before,after,base=map(read,[A,B,P]);power=json.loads((P/'power-audit.json').read_text())
for d,n in [(A,before),(B,after),(P,base)]:assert sha(d/'f722-heli.kicad_pcb')==n['board_sha256']
assert base['board_sha256']==power['board_sha256']
old={o['uuid']:o for o in before['objects']};now={o['uuid']:o for o in after['objects']};assert all(now.get(uid)==o for uid,o in old.items())
added=[o for uid,o in now.items()if uid not in old];assert added
assert all(o['kind']=='track' and set(o['copper'])<={'F.Cu','B.Cu'} and len(o['copper'])==1 and o['width']==.127 and o['net']not in power['nets'] for o in added)
assert all(before[k]==after[k]==base[k]for k in ['zones','edge_cuts','footprints','copper_layers'])
assert [o for o in base['objects']if o.get('drill')]==[o for o in after['objects']if o.get('drill')]
domains={}
for net in power['nets']:
 x=[o for o in base['objects']if o['net']==net];y=[o for o in after['objects']if o['net']==net];assert x==y
 zones=[z for z in base['zones']if z['net']==net]
 domains[net]=dict(object_count=len(x),zone_count=len(zones),identical_native_domain_sha256=hashlib.sha256(json.dumps(dict(objects=x,zones=zones),sort_keys=True,separators=(',',':')).encode()).hexdigest())
paired={}
for p in sorted(P.rglob('*')):
 if not p.is_file()or not(p.suffix in ['.kicad_sch','.kicad_pro','.kicad_dru','.kicad_mod','.kicad_sym']or p.name in ['parts.json','fp-lib-table','sym-lib-table']):continue
 dest=B/p.relative_to(P);assert dest.is_file()and sha(dest)==sha(p);paired[str(p.relative_to(P))]=sha(p)
r=dict(passed=True,source_board_sha256=before['board_sha256'],board_sha256=after['board_sha256'],power_baseline_board_sha256=base['board_sha256'],source_native_sha256=sha(A/'f722-heli.native.json'),native_sha256=sha(B/'f722-heli.native.json'),power_baseline_native_sha256=sha(P/'f722-heli.native.json'),audit_source_sha256=sha(__file__),source_objects_retained_exact=len(old),new_tracks=len(added),new_vias=0,all_footprints_poses_saved_zones_drills_and_power_domains_exact=True,power_domains=domains,paired_circuit_hashes=paired,power_applicability='Exact baseline conductive domains, pads, drills, saved fills, component poses and paired circuits retained. Complete job/contact/material binding and numerical result remain separate; no new solve or unconditional power pass is claimed.')
a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in ['power_domains','paired_circuit_hashes']}))
