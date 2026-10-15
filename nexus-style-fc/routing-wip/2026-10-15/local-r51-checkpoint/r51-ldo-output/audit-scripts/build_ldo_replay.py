from pathlib import Path
import json,hashlib,sys,shutil,uuid,importlib.util,copy
sys.path.insert(0,'/workspace/shared/nexus-recovery-evidence');from apply_en_cut import children,field
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');S=R/'routing-continuation/r50-cc1-spoke-preserved';O=R/'routing-continuation/r51-ldo-output';assert not O.exists();P=S/'hardware/nexus-style-fc.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();expected='dcc05684e414cb291761e02b97c2e27fa118dae4cf9363598499972c7e5b3d2a';assert sha(P)==expected
F=Path('/workspace/shared/nexus-recovery-evidence/ldo-transaction/ldo-transaction-proposal.json');assert sha(F)=='950857c491b7ab3ca029df535ffe9a8ca88c22c932ec67455f0f5c6a79e3ce73';j=json.loads(F.read_text());oldP=Path(j['source']['path']);assert sha(oldP)==j['source']['sha256']
spec=importlib.util.spec_from_file_location('validator',R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
texts=[oldP.read_text(),P.read_text()];trees=[V.parse_sexpr(s) for s in texts];native_nodes=[{**V.keyed_nodes(V.children(t,'segment')),**V.keyed_nodes(V.children(t,'via'))} for t in trees]
removed=j['remove']['output_items']+j['remove']['input_items'];rm={x['uuid'] for x in removed};assert len(rm)==10
historical,current=[copy.deepcopy(V.keyed_nodes(V.children(t,'footprint'))) for t in trees]
c19='bf4b5d3b-ec00-467e-acdf-84522df41d82'
allowed={'Value':('2.2uF','10uF'),'LCSC':('C23630','C19702'),'Description':('LDO out, >=2 uF effective','LDO output; Samsung CL10A106KP8NNNC; 10 uF, 10 V, X5R, +/-10%; JLC/LCSC C19702')}
for name,(old,new) in allowed.items():
 a=next(n for n in V.children(historical[c19],'property') if n[1]==['string',name]);b=next(n for n in V.children(current[c19],'property') if n[1]==['string',name])
 assert a[2]==['string',old] and b[2]==['string',new],(name,a[2],b[2]);b[2]=['string',old]
assert historical==current,'Historical applicability changed outside exact approved C19 metadata'
assert sha(S/'hardware/nexus-style-fc.kicad_sch')=='49f9e0571424d0610e294bdcd6b120a42d04db284ecda9e660428fc587e62699' 
for u in rm|{x['uuid'] for x in j['retained']['critical_items'] if x['kind']!='pad'}:assert native_nodes[0][u]==native_nodes[1][u],('Source applicability changed',u)
text=texts[1];nodes={field(text[i:z],'uuid').strip('"'):(i,z,text[i:z]) for i,z in children(text) if text[i:z].startswith(('(segment\n','(via\n'))};patches=[]
for u in rm:i,z,_=nodes[u];patches.append((i,z,''))
add=[];mapping={};new_items=[]
for q in j['add']:
 t=dict(q);u=str(uuid.uuid5(uuid.NAMESPACE_URL,'nexus/r51-ldo/'+q['uuid']));assert u not in nodes;mapping[q['uuid']]=u;t['uuid']=u;new_items.append(t)
 if t['kind']=='segment':
  a,b=t['start'],t['end'];add.append(f'\t(segment\n\t\t(start {a[0]} {a[1]})\n\t\t(end {b[0]} {b[1]})\n\t\t(width {t["width_mm"]})\n\t\t(layer "{t["layers"][0]}")\n\t\t(net "{t["net"]}")\n\t\t(uuid "{u}")\n\t)\n')
 else:
  assert t['kind']=='via';p=t['at'];add.append(f'\t(via\n\t\t(at {p[0]} {p[1]})\n\t\t(size {t["diameter_mm"]})\n\t\t(drill {t["drill_mm"]})\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(tenting front back)\n\t\t(net "{t["net"]}")\n\t\t(uuid "{u}")\n\t)\n')
for i,z,v in sorted(patches,reverse=True):text=text[:i]+v+text[z:]
end=text.rfind(')');text=text[:end]+''.join(add)+text[end:];shutil.copytree(S/'hardware',O/'hardware');out=O/'hardware/nexus-style-fc.kicad_pcb';out.write_text(text);shutil.copy2(F,O/'source-proposal.json')
tr={'status':'Fresh U10 output-loop improvement replay; native and actual-return acceptance pending','source_directory':str(S),'source_board_sha256':expected,'source_schematic_sha256':sha(S/'hardware/nexus-style-fc.kicad_sch'),'candidate_pre_refill_sha256':sha(out),'source_proposal_sha256':sha(F),'historical_applicability_exception':'Only the three exact approved C19 property values were normalized to the old proposal; all other footprints and donor copper match exactly.','stopping_bound':'One exact atomic replay of the source-bound U10 proposal. Reject any donor mismatch, new/worsened native error, lost full-width port, changed C18/C19 GND primitive path, EN contact, or forbidden net/part/width/stack/paste change. No broader reroute in this transaction.','removed_items':removed,'new_items':new_items,'proposal_to_native_uuid':mapping,'expected_external_ports':[p['geometry']['uuid'] for p in j['external_contacts']['unique_external_ports']],'width_layer_policy':'All replacement power tracks 0.250 mm. Output moves from 15.2 um In3 to 35 um F.Cu; input moves from 35 um F.Cu to 35 um B.Cu. No trace-width or copper-cross-section reduction. Ordinary .45/.20 tented via outside pasted pads.','qualification':'Output-loop restoration under source-based TPS709 input-capacitor tradeoff decision with +0.389325 mm input planar and +1.4134 mm modeled input barrels. Actual input and output ground topology and capacitor/stability qualification remain separate gates.'};(O/'transaction.json').write_text(json.dumps(tr,indent=2)+'\n');shutil.copy2(R/'current-main-binding-09.json',O/'current-main-binding.json');assert sha(P)==expected;print(json.dumps({'candidate':str(out),'pre_refill_sha256':sha(out),'removed':len(rm),'added':len(add),'mapping':mapping},indent=2))
