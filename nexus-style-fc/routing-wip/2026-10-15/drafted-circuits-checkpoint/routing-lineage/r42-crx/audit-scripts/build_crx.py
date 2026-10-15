from pathlib import Path
import json,re,hashlib,sys,shutil,uuid
sys.path.insert(0,'/workspace/shared/nexus-recovery-evidence');from apply_en_cut import children,field
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');S=R/'pcb-lane/experimental-en';O=R/'routing-continuation/r42-crx';assert not O.exists();P=S/'hardware/nexus-style-fc.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();expected='dffa517af49995e3d29a5e6cf7bea1e7cfab7c7449ec1d0e8030fb253a12c2e8';assert sha(P)==expected;j=json.loads(Path('/workspace/shared/nexus-recovery-evidence/recovered-crx-5v-proposal-not-accepted-transaction.json').read_text());text=P.read_text();nodes={}
for i,z in children(text):
 b=text[i:z]
 if b.startswith('(segment ' ) or b.startswith('(segment\n'):nodes[field(b,'uuid').strip('"')]=(i,z,b)
patches=[];routes=[];removed=[];added=[]
for ci,c in enumerate(j['cases']):
 for old in c['old_tracks']:
  i,z,b=nodes[old['id']];assert field(b,'net').strip('"')==old['net'] and field(b,'layer').strip('"')==old['layer'][0] and float(field(b,'width'))==old['width'][0]
  for f in ['start','end']:assert [round(float(x)*1e6) for x in field(b,f).split()]==[round(x*1e6) for x in old[f]]
  patches.append((i,z,''));removed.append(old)
 route={'name':c['net'],'net':c['net'],'layer':c['layer'],'width_mm':c['width_mm'],'removed_uuids':c['remove'],'points':c['points'],'new_uuids':[],'expected_external_ports':[x['id'] for x in c['external_ports']]}
 for si,(a,b) in enumerate(zip(c['points'],c['points'][1:])):
  u=str(uuid.uuid5(uuid.NAMESPACE_URL,'nexus-fresh-crx/'+expected+'/'+str(ci)+'/'+str(si)));route['new_uuids'].append(u);added.append(f'\t(segment\n\t\t(start {a[0]} {a[1]})\n\t\t(end {b[0]} {b[1]})\n\t\t(width {c["width_mm"]})\n\t\t(layer "{c["layer"]}")\n\t\t(net "{c["net"]}")\n\t\t(uuid "{u}")\n\t)\n')
 routes.append(route)
for i,z,v in sorted(patches,reverse=True):text=text[:i]+v+text[z:]
end=text.rfind(')');text=text[:end]+''.join(added)+text[end:];shutil.copytree(S/'hardware',O/'hardware');out=O/'hardware/nexus-style-fc.kicad_pcb';out.write_text(text);tr={'status':'fresh bounded transaction; not historical replay; native checks pending','source_directory':str(S),'source_board_sha256':expected,'candidate_pre_refill_sha256':sha(out),'source_schematic_sha256':sha(S/'hardware/nexus-style-fc.kicad_sch'),'routes':routes,'removed_tracks':removed,'width_layer_policy':'Every donor stays on F.Cu at its exact inherited width: C_RX .127 mm, 5V .250 mm. No via/pad/net/footprint/rule/outline changes.','historical_proposal':'recovered-crx-5v-proposal-not-accepted-transaction.json'};(O/'transaction.json').write_text(json.dumps(tr,indent=2)+'\n');assert sha(P)==expected;print(json.dumps({'candidate':str(out),'pre_refill_sha256':sha(out),'removed':len(removed),'added':len(added)},indent=2))
