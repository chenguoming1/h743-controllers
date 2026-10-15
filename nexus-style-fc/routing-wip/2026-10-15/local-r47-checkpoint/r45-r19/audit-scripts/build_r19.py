from pathlib import Path
import json,re,hashlib,sys,shutil,uuid
sys.path.insert(0,'/workspace/shared/nexus-recovery-evidence');from apply_en_cut import children,field
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');S=R/'c19-integration/experimental-r43';O=R/'routing-continuation/r45-r19';assert not O.exists();P=S/'hardware/nexus-style-fc.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();expected='10c4da72046f311a0ad61ac150091573966c8d9fae70fa93a57402a568d059c5';assert sha(P)==expected;F=Path('/workspace/shared/nexus-recovery-evidence/r19-coordinated-proposal-recovered.json');assert sha(F)=='a3498b92a53593e2d6da1e7e9e3f9d6db0752219fc1dc5e4a44b2063dcc7c877';j=json.loads(F.read_text());text=P.read_text();nodes={field(text[i:z],'uuid').strip('"'):(i,z,text[i:z]) for i,z in children(text) if text[i:z].startswith(('(segment\n','(via\n'))};patches=[]
for old in j['removed_tracks']:
 u=old['uuid'];i,z,t=nodes[u];assert field(t,'net').strip('"')==old['net'] and field(t,'layer').strip('"')==old['layer'] and float(field(t,'width'))==old['width_mm']
 for f in ['start','end']:assert list(map(float,field(t,f).split()))==old[f]
 patches.append((i,z,''))
m=j['via_move'];old=m['original'];u=old['uuid'];i,z,t=nodes[u];assert field(t,'net').strip('"')==old['net'] and list(map(float,field(t,'at').split()))==old['position'] and float(field(t,'size'))==old['size_mm'] and float(field(t,'drill'))==old['drill_mm'];to=m['new_position'];patches.append((i,z,re.sub(r'\(at\s+[^()]+\)',f'(at {to[0]} {to[1]})',t,count=1)));moves=[{'uuid':u,'from':old['position'],'to':to,'size_mm':old['size_mm'],'drill_mm':old['drill_mm']}]
routes=[];added=[]
for r in j['routes']:
 r=dict(r);r['new_uuids']=[];r['expected_external_ports']=[p['original']['uuid'] for p in j['external_physical_ports'] if any(c.startswith(r['name']+':') for c in p['new_contacts'])]
 if r['net']=='IMU_CS':r['expected_external_ports'].append(u)
 for idx,(a,b) in enumerate(zip(r['points'],r['points'][1:])):
  nu=str(uuid.uuid5(uuid.NAMESPACE_URL,f'nexus/r45-r19/{r["name"]}/{idx}'));assert nu not in nodes;r['new_uuids'].append(nu);added.append(f'\t(segment\n\t\t(start {a[0]} {a[1]})\n\t\t(end {b[0]} {b[1]})\n\t\t(width {r["width_mm"]})\n\t\t(layer "{r["layer"]}")\n\t\t(net "{r["net"]}")\n\t\t(uuid "{nu}")\n\t)\n')
 routes.append(r)
for i,z,v in sorted(patches,reverse=True):text=text[:i]+v+text[z:]
end=text.rfind(')');text=text[:end]+''.join(added)+text[end:];shutil.copytree(S/'hardware',O/'hardware');out=O/'hardware/nexus-style-fc.kicad_pcb';out.write_text(text);shutil.copy2(F,O/'source-proposal.json');tr={'status':'Fresh R19/IMU_CS/IMU_INT/GND/power complete donor transaction; native checks pending','source_directory':str(S),'source_board_sha256':expected,'source_schematic_sha256':sha(S/'hardware/nexus-style-fc.kicad_sch'),'source_main_commit_reported_by_owner':'80a3f763d5031198b4622402bb73a532676b9be9','candidate_pre_refill_sha256':sha(out),'source_proposal_sha256':sha(F),'routes':routes,'removed_tracks':j['removed_tracks'],'moved_vias':moves,'width_layer_policy':'Every donor retains inherited .127 mm width and copper layer. Existing .45/.20 IMU_CS via relocated only; no added vias, footprint/pad/part/net/stack/outline changes.'};(O/'transaction.json').write_text(json.dumps(tr,indent=2)+'\n');assert sha(P)==expected;print(json.dumps({'candidate':str(out),'pre_refill_sha256':sha(out),'removed':len(j['removed_tracks']),'added':len(added)},indent=2))
