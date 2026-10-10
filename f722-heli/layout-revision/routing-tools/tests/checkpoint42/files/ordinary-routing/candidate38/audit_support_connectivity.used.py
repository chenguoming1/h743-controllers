#!/usr/bin/env python3
"""Source-bound native support connectivity and reference refill audit."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native-tools'))
from check_protection_paths import make_graph,geometry
ap=argparse.ArgumentParser();ap.add_argument('--source-native',type=Path,required=True);ap.add_argument('--native',type=Path,required=True);ap.add_argument('--board',type=Path,required=True);ap.add_argument('--source-audit',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=json.loads(a.source_native.read_text());after=json.loads(a.native.read_text());base=json.loads(a.source_audit.read_text());assert after['board_sha256']==sha(a.board);assert base['board_sha256']==before['board_sha256'];old={o['uuid']:o for o in before['objects']};now={o['uuid']:o for o in after['objects']};assert all(now.get(uid)==o for uid,o in old.items()),'Existing pad/copper changed';assert before['footprints']==after['footprints'] and before['edge_cuts']==after['edge_cuts'] and before['copper_layers']==after['copper_layers']
def objects(n,net):
 return [o for o in n['objects']if o['net']==net]+[{'uuid':z['uuid'],'kind':'zone','net':net,'copper':z['filled'],'drill':None,'plated':False}for z in n['zones']if not z['rule']and z['net']==net]
def groups(n,net):
 out=[]
 for group in make_graph(objects(n,net)):
  pads={v['object']['uuid']:v['object']['key']for v in group if v['object']['kind']=='pad'}
  if pads:out.append({'pads':sorted(pads.values()),'pad_uuids':sorted(pads)})
 return sorted(out,key=lambda q:q['pad_uuids'])
rows={}
for net in base['nets']:
 g=groups(after,net);assert len(g)==1,(net,len(g));rows[net]={'pad_group_count':len(g),'groups':g}
assert len(rows)==28
old_ground=groups(before,'GND');assert old_ground==rows['GND']['groups'];vias=[o for o in after['objects']if o['uuid']not in old and o['kind']=='via'];planes=[]
for z in after['zones']:
 prev=next(x for x in before['zones']if x['uuid']==z['uuid']);regen=not z['rule']and z['net']=='GND'and set(z['layers'])<={'In1.Cu','In4.Cu'};strip=lambda q:{k:v for k,v in q.items()if not(regen and k in {'filled','fill_representation'})};assert strip(z)==strip(prev)
 if not regen:continue
 for layer,ps in z['filled'].items():
  g=geometry(ps);p=geometry(prev['filled'][layer]);gaps=[{'via':v['uuid'],'net':v['net'],'gap_mm':g.distance(geometry(v['copper'][layer]))}for v in vias];assert all(x['gap_mm']>=.127 for x in gaps);planes.append({'layer':layer,'source_holes':sum(len(q['holes'])for q in prev['filled'][layer]),'result_holes':sum(len(q['holes'])for q in ps),'source_outlines':len(prev['filled'][layer]),'result_outlines':len(ps),'new_via_gaps':gaps,'added_fill_area_mm2':g.difference(p).area,'removed_fill_area_mm2':p.difference(g).area})
r={'passed':True,'status':'all_28_support_nets_connected','board_sha256':after['board_sha256'],'source_board_sha256':before['board_sha256'],'native_sha256':sha(a.native),'source_native_sha256':sha(a.source_native),'source_audit_sha256':sha(a.source_audit),'audit_source_sha256':sha(Path(__file__)),'method':'Fresh native copper/barrel/saved-fill pad graph; connectivity only, not loaded electrical qualification.','all_source_pad_and_copper_objects_exact':len(old),'ground_native_pad_groups_exactly_preserved':True,'nets':rows,'planes':planes};a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in {'nets','planes'}}))
