from pathlib import Path
import pcbnew as k,json,hashlib,shutil,sys,uuid
sys.path.insert(0,'/workspace/shared/nexus-recovery-evidence');from apply_en_cut import children,field
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');L=R/'mechanical-integration';S=L/'r58-replay/native-baseline';O=L/'main-signal-01';assert not O.exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();P=S/'hardware/nexus-style-fc.kicad_pcb';assert sha(P)=='9818f3a8b18b84a300d7455b7251c18e46fde6d764a67829d0a49a98e19c99da';b=k.LoadBoard(str(P));uid=lambda o:o.m_Uuid.AsString();ts={uid(t):t for t in b.GetTracks()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};s=P.read_text();nodes={field(s[i:z],'uuid').strip(chr(34)):s[i:z] for i,z in children(s) if s[i:z].startswith('(segment')};routes=[{'name':'S3_B','net':'S3','layer':'B.Cu','width_mm':.127,'removed_uuids':['62aa1890-1d51-5a51-a2ab-0a3e85e99c83','035ce5d7-6f5f-420c-b9ac-0499106933ba'],'points':[[117.714551,104.880883],[116.7,104.9],[115.951333,104.225]]},{'name':'TAIL_B','net':'TAIL','layer':'B.Cu','width_mm':.127,'removed_uuids':['3c6b6b07-bc47-44c3-933e-dec9987cb0a7'],'points':[[106.973,104.225],[107.7,104.9],[108.7,105.3],[109.260798,105.901932]],'required_reconnected_pad':'7bcd86aa-3187-4a58-b9ec-aa84540e65c7'}]
ns=uuid.UUID('8cbfb12d-2c7d-4a3e-adff-537db29704fe');sourceblocks={}
def hit(a,b):
 z=k.SHAPE.Collide(a,b,0);return z[0] if isinstance(z,tuple) else bool(z)
for r in routes:
 l=b.GetLayerID(r['layer']);ports=set()
 for u in r['removed_uuids']:
  t=ts[u];assert t.GetNetname()==r['net'] and t.GetWidth()==127000 and t.GetLayer()==l;sourceblocks[u]=nodes[u]
  for w,o in {**ts,**ps}.items():
   if w not in r['removed_uuids'] and o.GetNetname()==r['net'] and o.IsOnLayer(l) and hit(t.GetEffectiveShape(l),o.GetEffectiveShape(l)):ports.add(w)
 r['expected_original_external_ports']=sorted(ports)
 if 'required_reconnected_pad' in r:
  p=ps[r['required_reconnected_pad']];assert p.GetParentFootprint().GetReference()=='J1' and p.GetNumber()=='6' and p.GetNetname()=='TAIL';ports.add(uid(p))
 r['expected_external_ports']=sorted(ports);r['new_uuids']=[];new=[]
 for i,(a,z) in enumerate(zip(r['points'],r['points'][1:])):
  u=str(uuid.uuid5(ns,r['name']+'-'+str(i)));r['new_uuids'].append(u);new.append(f'(segment (start {a[0]} {a[1]}) (end {z[0]} {z[1]}) (width {r["width_mm"]}) (layer "{r["layer"]}") (net "{r["net"]}") (uuid "{u}"))')
 for i,u in enumerate(r['removed_uuids']):assert s.count(nodes[u])==1;s=s.replace(nodes[u],'\n\t'.join(new) if i==0 else '')
shutil.copytree(S/'hardware',O/'hardware');(O/'hardware/nexus-style-fc.kicad_pcb').write_text(s);tr={'status':'UNFINISHED mechanical copper integration, bounded S3 and TAIL transaction','source_directory':str(S),'source_board_sha256':sha(P),'source_schematic_sha256':sha(S/'hardware/nexus-style-fc.kicad_sch'),'accepted_r58_source_sha256':'85c5cede5407d2022df36e0323527704a84c55687fc9dcc426565073aa9c4f8e','mechanical_replay_directory':str(L/'r58-replay/transaction'),'routes':routes,'moved_vias':[],'source_blocks':sourceblocks,'scope':'Only three B.Cu signal segments replaced by five same-width segments. Reconnect moved J1.6 TAIL and retain J1.7 S3 plus their original external donor ports. Diagnostic project has inherited ignored checks visible; unchanged source manufacturing rules. Mechanical board remains unaccepted while other shorts/edge conflicts remain.','stopping_bound':'One exact two-net route transaction; reject new/worsened native violations or missing same-net ports. No power, USB, parts, pad, via, outline or rule edits.'};(O/'transaction.json').write_text(json.dumps(tr,indent=2)+'\n');print(json.dumps({'candidate_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'routes':routes},indent=2))
