from pathlib import Path
import json,re,hashlib,sys,shutil
sys.path.insert(0,'/workspace/shared/nexus-recovery-evidence');from apply_en_cut import children,field
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');S=R/'routing-continuation/r42-crx';O=R/'routing-continuation/r43-swclk';assert not O.exists();P=S/'hardware/nexus-style-fc.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();expected='07bd34fd91df1d7ea2a21fbe4b4282b0fe9deffa8f19c1ae25d3db27dc093d5c';assert sha(P)==expected;F=Path('/workspace/shared/nexus-recovery-evidence/swclk-corridor/fresh-coordinated-proposal.json');j=json.loads(F.read_text());text=P.read_text();nodes={}
for i,z in children(text):
 b=text[i:z]
 if b.startswith('(segment\n') or b.startswith('(via\n'):nodes[field(b,'uuid').strip('"')]=(i,z,b)
patches=[];old_items=[x for g in j['original_donor_groups'] for x in g['original_items']];removed=[];moves=j['operation']['move_vias']
for old in old_items:
 u=old['uuid'];i,z,b=nodes[u];assert field(b,'net').strip('"')==old['net']
 if old['kind']=='segment':
  assert field(b,'layer').strip('"')==old['layers'][0] and float(field(b,'width'))==old['w']
  for f,key in [('start','a'),('end','b')]:assert [round(float(x)*1e6) for x in field(b,f).split()]==[round(x*1e6) for x in old[key]]
  patches.append((i,z,''));removed.append(old)
 else:
  mv=next(x for x in moves if x['uuid']==u);assert list(map(float,field(b,'at').split()))==mv['from'];assert float(field(b,'size'))==mv['size_mm'] and float(field(b,'drill'))==mv['drill_mm'];change=re.sub(r'\(at\s+[^()]+\)',f'(at {mv["to"][0]} {mv["to"][1]})',b,count=1);patches.append((i,z,change))
assert {x['uuid'] for x in removed}==set(j['operation']['remove_segments'])
added=[]
for t in j['operation']['add_segments']:
 assert t['uuid'] not in nodes;a,b=t['a'],t['b'];added.append(f'\t(segment\n\t\t(start {a[0]} {a[1]})\n\t\t(end {b[0]} {b[1]})\n\t\t(width {t["w"]})\n\t\t(layer "{t["layers"][0]}")\n\t\t(net "{t["net"]}")\n\t\t(uuid "{t["uuid"]}")\n\t)\n')
routes=[]
for ri,r in enumerate(j['replacement_route_summary']):
 group=next(g for g in j['original_donor_groups'] if g['net']==r['net']);layer=r['layer'];old=[t['uuid'] for t in group['original_items'] if t['kind']=='segment' and t['layers']==[layer]];new=[t for t in j['operation']['add_segments'] if t['net']==r['net'] and t['layers']==[layer]];assert len(new)==len(r['points'])-1
 for i,t in enumerate(new):assert t['a']==r['points'][i] and t['b']==r['points'][i+1]
 ports={c['retained_item']['uuid'] for c in group['external_physical_contacts'] if layer in c['retained_item']['layers']}
 if r['net']=='SWCLK':ports|={moves[0]['uuid']}
 routes.append({'name':r['net']+'/'+layer,'net':r['net'],'layer':layer,'width_mm':r['width_mm'],'points':r['points'],'removed_uuids':old,'new_uuids':[t['uuid'] for t in new],'expected_external_ports':sorted(ports)})
for i,z,v in sorted(patches,reverse=True):text=text[:i]+v+text[z:]
end=text.rfind(')');text=text[:end]+''.join(added)+text[end:];shutil.copytree(S/'hardware',O/'hardware');out=O/'hardware/nexus-style-fc.kicad_pcb';out.write_text(text);shutil.copy2(F,O/'source-proposal.json');tr={'status':'Fresh source-bound SWCLK/SDA/5V coordinated transaction; native checks pending','source_directory':str(S),'source_board_sha256':expected,'source_schematic_sha256':sha(S/'hardware/nexus-style-fc.kicad_sch'),'candidate_pre_refill_sha256':sha(out),'source_proposal_sha256':sha(F),'routes':routes,'removed_tracks':removed,'moved_vias':moves,'width_layer_policy':'SWCLK and SDA remain .127 mm on inherited layers. Complete .350 mm 5V donor stays F.Cu; no power necking, layer/cross-section change or dangling partial donor.'};(O/'transaction.json').write_text(json.dumps(tr,indent=2)+'\n');assert sha(P)==expected;print(json.dumps({'candidate':str(out),'pre_refill_sha256':sha(out),'removed':len(removed),'added':len(added),'routes':routes},indent=2))
