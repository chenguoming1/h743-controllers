"""Check scoped source retention and every support terminal after native reconstruction."""
import argparse, hashlib, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; R=HERE.parents[1]
sys.path.insert(0,str(R/'native-tools'))
from check_protection_paths import make_graph, geometry
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);a=ap.parse_args()
bp=a.source/'f722-heli.kicad_pcb';apath=a.candidate/'f722-heli.kicad_pcb'
before=json.loads(bp.with_suffix('.native.json').read_text());after=json.loads(apath.with_suffix('.native.json').read_text());receipt=json.loads((a.candidate/'power-construction.json').read_text());base=json.loads((a.source/'power-audit.json').read_text())
assert sha(bp)==before['board_sha256']==receipt['source_board_sha256']==base['board_sha256']
assert sha(apath)==after['board_sha256']==receipt['board_sha256']
old={o['uuid']:o for o in before['objects']};now={o['uuid']:o for o in after['objects']};removed={o['uuid']:o for o in receipt['removed_objects']};added={o['uuid']:o for o in receipt['added_objects']}
assert all(old.get(u)==o and u not in now for u,o in removed.items())
assert all(now.get(u)==o and u not in old for u,o in added.items())
assert set(now)==(set(old)-set(removed))|set(added)
assert all(now[u]==o for u,o in old.items()if u not in removed)
assert before['footprints']==after['footprints'] and before['edge_cuts']==after['edge_cuts']
def objects(n,net):
 return [o for o in n['objects']if o['net']==net]+[{'uuid':z['uuid'],'kind':'zone','net':net,'copper':z['filled'],'drill':None,'plated':False}for z in n['zones']if not z['rule']and z['net']==net]
def groups(n,net):
 out=[]
 for g in make_graph(objects(n,net)):
  pads={v['object']['uuid']:v['object']['key']for v in g if v['object']['kind']=='pad'}
  if pads:out.append({'pads':sorted(pads.values()),'pad_uuids':sorted(pads)})
 return sorted(out,key=lambda q:q['pad_uuids'])
rows={}
for net in base['nets']:
 g=groups(after,net);oldg=groups(before,net)
 assert len(g)==1 and g==oldg,(net,g,oldg)
 rows[net]={'pad_group_count':1,'groups':g}
assert len(rows)==28
usb=groups(after,'USB_VBUS_RAW');assert usb==groups(before,'USB_VBUS_RAW')and len(usb)==1
planes=[]
for z in after['zones']:
 prev=next(x for x in before['zones']if x['uuid']==z['uuid'])
 strip=lambda o:{k:v for k,v in o.items()if k not in {'filled','fill_representation'}}
 assert strip(z)==strip(prev)
 if z['rule']:assert z==prev;continue
 assert z['net']=='GND' and set(z['layers'])<={'In1.Cu','In4.Cu'}
 for layer,ps in z['filled'].items():
  g=geometry(ps);p=geometry(prev['filled'][layer]);assert not g.is_empty and g.is_valid
  planes.append(dict(layer=layer,added_area_mm2=g.difference(p).area,removed_area_mm2=p.difference(g).area,source_outline_count=len(prev['filled'][layer]),result_outline_count=len(ps),source_hole_count=sum(len(q['holes'])for q in prev['filled'][layer]),result_hole_count=sum(len(q['holes'])for q in ps)))
r=dict(passed=True,status='all_28_support_nets_and_USB_RAW_connected_after_scoped_power_reconstruction',board_sha256=sha(apath),source_board_sha256=sha(bp),native_sha256=sha(apath.with_suffix('.native.json')),source_native_sha256=sha(bp.with_suffix('.native.json')),construction_sha256=sha(a.candidate/'power-construction.json'),audit_source_sha256=sha(__file__),source_objects_retained_exact=len(old)-len(removed),removed_copper_count=len(removed),added_copper_count=len(added),all_source_pads_and_footprints_exact=True,all_support_pad_groups_exactly_preserved=True,all_ground_pad_groups_exactly_preserved=True,usb_vbus_raw_pad_groups=usb,nets=rows,planes=planes,limitations='Connectivity and scoped identity only; native DRC/process/reference, endpoint, loaded power and bypass-placement review remain separate gates.')
(a.candidate/'power-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in {'nets','planes','usb_vbus_raw_pad_groups'}}))
