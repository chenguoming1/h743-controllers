from pathlib import Path
import pcbnew as k,sys,json,hashlib,importlib.util
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'r56-remaining-via-inventory';S=R/'routing-continuation/r53-cc2-bend';C=R/'routing-continuation/r56-offpad-ground';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(C/'hardware/nexus-style-fc.kicad_pcb')=='64eb0addce9b1ef9c14f29714224834a09e44b96ecd66a967d2f667f9530900f';spec=importlib.util.spec_from_file_location('validator',R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V);review=Path('/workspace/shared/nexus-pasted-via-review/per-via-review.json');j=json.loads(review.read_text());assert sha(S/'hardware/nexus-style-fc.kicad_pcb')==j['source_sha256'];trees=[V.parse_sexpr((p/'hardware/nexus-style-fc.kicad_pcb').read_text()) for p in [S,C]];assert V.keyed_nodes(V.children(trees[0],'footprint'))==V.keyed_nodes(V.children(trees[1],'footprint'));maps=[]
for t in trees:
 d={}
 for tag in ['segment','via','arc']:d.update(V.keyed_nodes(V.children(t,tag)))
 maps.append(d)
b=k.LoadBoard(str(C/'hardware/nexus-style-fc.kicad_pcb'));contacts=V.drill_paste_contacts(b);ids={p['via_uuid'] for p in contacts};removed={'3cfc0b66-fb89-4bcd-8fd4-b8f8542b90a3','7f89653b-c07a-4bb7-8d55-49a1f1873aa3'};assert {p['via']['uuid'] for p in j['vias']}-ids==removed;assert len(ids)==16 and len(contacts)==17
rows=[]
for z in j['vias']:
 u=z['via']['uuid']
 if u not in ids:continue
 for item in [z['via']]+z['all_direct_same_net_copper_donors']:
  q=item['uuid']
  if item['kind']!='pad':assert maps[0][q]==maps[1][q],('Remaining via/donor drift',q)
 row={key:z[key] for key in ['via','classification','function','pasted_pad_contacts','all_direct_same_net_copper_donors','smallest_further_investigation']};row['source_pad_and_direct_donor_definitions_unchanged']=True;row['current_native_drill_paste_contacts']=[p for p in contacts if p['via_uuid']==u];rows.append(row)
out={'status':'Verified exact remaining inventory on sealed r56: 16 ordinary vias contact 17 pasted pads; assembly/process remedies remain unqualified','candidate_board_sha256':sha(C/'hardware/nexus-style-fc.kicad_pcb'),'candidate_seal_sha256':sha(C/'evidence-manifest.json'),'classification_source_sha256':sha(review),'native_summary':V.contact_summary(contacts),'removed_locations':sorted(removed),'remaining':rows,'scope':'Classification and function labels carried from exact source review only after whole-footprint and every remaining via/direct donor definition equality; current native drill/pasted-pad geometry recomputed. Old fill-membership and untested candidate calculations intentionally omitted. No claim that remaining assembly risks are resolved.'};(O/'remaining-vias.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
