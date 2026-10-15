from pathlib import Path
import pcbnew as k,json,hashlib,shutil,sys,re
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');L=R/'mechanical-integration';S=L/'r61-replay/native-baseline';T=L/'r61-replay/project';O=L/'main-right-vias-02';assert not O.exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();sys.path.insert(0,'/workspace/shared/nexus-recovery-evidence');from apply_en_cut import children,field
sys.path.insert(0,str(R/'latest-main/nexus-style-fc/tools'));import validate_nexus_reroute as V
proposal=L/'top-header-via-study/complete-proposal.json';assert sha(proposal)=='167a5cb494018c6ad5974a376ed09aee21981dfd6e94bce61140e34a2d186674';p=json.loads(proposal.read_text());assert sha(S/'hardware/nexus-style-fc.kicad_pcb')==p['source_board_sha256'];P=T/'hardware/nexus-style-fc.kicad_pcb';assert sha(P)=='c03e93ad9006456f0094c058f15e53e550c9a521d59308bba12c82020113e4be';raw=P.read_text();nodes={field(raw[i:j],'uuid').strip(chr(34)):raw[i:j] for i,j in children(raw) if raw[i:j].startswith(('(segment','(via'))};routes=[];moves=[];sourceblocks={}
for route in p['routes']:
 r=dict(route);r['name']=r['net']+'_'+r['layer'];r['new_uuids']=[z['uuid'] for z in r['replacement_segments']];u=r['removed_uuids'][0];assert V.canonical(V.parse_sexpr(nodes[u]))==V.canonical(V.parse_sexpr(r['source_record']));sourceblocks[u]=nodes[u];new=[]
 for z in r['replacement_segments']:new.append(f'(segment (start {z["start"][0]} {z["start"][1]}) (end {z["end"][0]} {z["end"][1]}) (width {z["width_mm"]}) (layer "{z["layer"]}") (net "{z["net"]}") (uuid "{z["uuid"]}"))')
 raw=raw.replace(nodes[u],'\n\t'.join(new));routes.append(r)
for m in p['moved_vias']+[{ 'uuid':'3bc1d32f-634e-4d77-9c5d-f6bdd353e76c','net':'GND','from':[119.975,104.225],'to':[120.825,105.05],'diameter_mm':.45,'drill_mm':.20}]:
 u=m['uuid'];block=nodes[u];assert field(block,'net').strip(chr(34))==m['net'];assert list(map(float,field(block,'at').split()))==m['from'];
 if 'source_record' in m:assert V.canonical(V.parse_sexpr(block))==V.canonical(V.parse_sexpr(m['source_record']))
 sourceblocks[u]=block;raw=raw.replace(block,re.sub(r'\(at [^)]+\)',f'(at {m["to"][0]} {m["to"][1]})',block,count=1));m={**m,'size_mm':m['diameter_mm']};moves.append(m)
# Copper source identities use the exact pre-native mechanical replay. Loading the uncorrected source reassigns one overlapping via, so restore that original identity in memory for contact enumeration.
b=k.LoadBoard(str(P));ts={q.m_Uuid.AsString():q for q in b.GetTracks()};ps={q.m_Uuid.AsString():q for f in b.GetFootprints() for q in f.Pads()};ground=next(q.GetNetCode() for q in ps.values() if q.GetNetname()=='GND');ts['3bc1d32f-634e-4d77-9c5d-f6bdd353e76c'].SetNetCode(ground)
def hit(a,b):
 z=k.SHAPE.Collide(a,b,0);return z[0] if isinstance(z,tuple) else bool(z)
for r in routes:
 ports=set();l=b.GetLayerID(r['layer'])
 for u in r['removed_uuids']:
  t=ts[u]
  for w,q in {**ts,**ps}.items():
   if w not in r['removed_uuids'] and q.GetNetname()==r['net'] and q.IsOnLayer(l) and hit(t.GetEffectiveShape(l),q.GetEffectiveShape(l)):ports.add(w)
 r['expected_original_external_ports']=r['expected_external_ports']=sorted(ports)
shutil.copytree(S/'hardware',O/'hardware');(O/'hardware/nexus-style-fc.kicad_pcb').write_text(raw);shutil.copy2(proposal,O/'source-proposal.json');tr={'status':'UNACCEPTED mechanical correction trial','source_directory':str(S),'source_board_sha256':sha(S/'hardware/nexus-style-fc.kicad_pcb'),'intended_source_directory':str(T),'intended_source_board_sha256':sha(P),'source_schematic_sha256':sha(S/'hardware/nexus-style-fc.kicad_sch'),'accepted_r61_source_sha256':'5a51610cc1569958442f97407e11533b646b1e0d8997d86356b8968dce50487e','routes':routes,'moved_vias':moves,'source_blocks':sourceblocks,'recovered_original_net':{'uuid':'3bc1d32f-634e-4d77-9c5d-f6bdd353e76c','original_net':'GND','incorrect_native_baseline_net':'S1','mechanism':'KiCad load automatically reassigns the via overlapping the moved S1 pad. Candidate is patched from original guarded text before loading, keeping GND and relocating the ordinary plane via off the pad.'},'stopping_bound':'One complete right ESC/DSM donor transaction plus original-net GND via recovery; no new/worse native findings, no net changes versus original approved replay, and finite post-refill GND/USB/LDO/shield returns required.'};(O/'transaction.json').write_text(json.dumps(tr,indent=2)+'\n');print(sha(O/'hardware/nexus-style-fc.kicad_pcb'))
