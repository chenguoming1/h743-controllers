from pathlib import Path
import pcbnew as k,json,hashlib,shutil,sys,re,subprocess,collections,datetime,uuid,copy,importlib
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');L=R/'mechanical-integration';S=L/'main-terminal-cleanup-07';O=L/'main-signal-slot-08';Q=Path(sys.argv[1]);QH=sys.argv[2];M=R/'header-assembly-fit-review-readonly/slot101x220-source-guarded-spec.json';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert not O.exists();assert sha(Q)==QH;assert sha(M)=='5d0864b9465a0cde7d148bda654c9adaeff6ccd9e0dd5fb01155699cba5d552a';m=json.loads(M.read_text());j=json.loads(Q.read_text());assert sha(S/'hardware/nexus-style-fc.kicad_pcb')=='1d40a35cf373bef251f8032001766016f09500b007f22ff27ccb6578b0c4e263'
assert j['source_board_sha256']==sha(S/'hardware/nexus-style-fc.kicad_pcb') and j['mechanical_spec_sha256']==sha(M)
for rel,h in m['source_sha256'].items():assert sha(S/rel)==h,rel
sys.path.insert(0,'/workspace/shared/nexus-recovery-evidence');from apply_en_cut import children,field
sys.path.insert(0,str(R/'latest-main/nexus-style-fc/tools'));import validate_nexus_reroute as V
raw=(S/'hardware/nexus-style-fc.kicad_pcb').read_text();nodes={field(raw[i:z],'uuid').strip('"'):raw[i:z] for i,z in children(raw) if raw[i:z].startswith(('(segment','(via','(arc'))};removed=[];added=[];records={};routes=copy.deepcopy(j['routes']);ns=uuid.UUID('9160f3ce-d847-5be9-8869-b3a131da1980')
for r in routes:
 r['removed_uuids']=r.get('removed',r.get('removed_uuids'));r['new_uuids']=[]
 for i,s in enumerate(r['source_records']):
  u=s['uuid'];assert u in r['removed_uuids'];old=nodes[u];assert V.canonical(V.parse_sexpr(old))==V.canonical(V.parse_sexpr(s['canonical_sexpr'])),('source donor conflict',u);records[u]=old;removed.append(u);new=[]
  if i==0:
   for z,q in enumerate(r['replacement_segments']):
    q['uuid']=q.get('uuid',str(uuid.uuid5(ns,r['name']+'/'+str(z))));q['width_mm']=q.get('width_mm',.127);assert q['width_mm']==.127 and q['net'] in ['RPM','DSM_DATA','SBUS'] and q['layer']=='In2.Cu';r['new_uuids'].append(q['uuid']);new.append(f'(segment (start {q["start"][0]} {q["start"][1]}) (end {q["end"][0]} {q["end"][1]}) (width {q["width_mm"]}) (layer "{q["layer"]}") (net "{q["net"]}") (uuid "{q["uuid"]}"))');added.append({'kind':'segment','uuid':q['uuid'],'net':q['net'],'layer':q['layer'],'width':q['width_mm'],'start':q['start'],'end':q['end'],'proposal_id':r['name']+'/'+str(z)})
  assert raw.count(old)==1;raw=raw.replace(old,'\n'.join(new))
assert len(removed)==len(set(removed))
# Incremental approved geometry only; never rerun historical r54 mechanical replay.
t=V.parse_sexpr(raw)
def replace_canonical(raw,old,new,root_tag=None):
 oldc=V.canonical(V.parse_sexpr(old));target=V.source_uuid(V.parse_sexpr(old));assert raw.count(chr(34)+target+chr(34))==1
 # Locate raw node by parentheses, using uuid as a unique inner anchor.
 pos=raw.index('"'+target+'"');starts=[i for i,c in enumerate(raw[:pos]) if c=='('];chosen=None
 for start in reversed(starts):
  level=0;quote=False;esc=False
  for end in range(start,len(raw)):
   c=raw[end]
   if quote:
    if esc:esc=False
    elif c=='\\':esc=True
    elif c=='"':quote=False
   elif c=='"':quote=True
   elif c=='(':level+=1
   elif c==')':
    level-=1
    if level==0:
     if end>=pos:
      candidate=raw[start:end+1]
      try:good=V.canonical(V.parse_sexpr(candidate))==oldc
      except Exception:good=False
      if good:chosen=(start,end+1)
     break
  if chosen:break
 assert chosen,target;return raw[:chosen[0]]+new+raw[chosen[1]:]
for q in m['edge_changes']+m['keepout_changes']:raw=replace_canonical(raw,q['old_native_record'],q['new_native_record'])
# Description is scoped to J1's complete footprint node.
for i,z in children(raw):
 n=raw[i:z]
 if n.startswith('(footprint') and '(property "Reference" "J1"' in n:
  assert n.count('10.0 x 2.1')==1;raw=raw[:i]+n.replace('10.0 x 2.1','10.1 x 2.2')+raw[z:];break
else:raise AssertionError('J1 not found')
# Clear cached fills only, preserving all copper-zone definitions.
for i,z in reversed(list(children(raw))):
 node=raw[i:z]
 if not node.startswith('(zone'):continue
 for a,c in reversed(list(children(node))):
  if node[a:c].startswith(('(filled_polygon','(fill_segments')):node=node[:a]+node[c:]
 raw=raw[:i]+node+raw[z:]
shutil.copytree(S/'hardware',O/'hardware');shutil.copytree(S/'tools',O/'tools',ignore=shutil.ignore_patterns('__pycache__'))
for rel,replacements in m['source_text_replacements'].items():
 p=O/rel;s=p.read_text();counts={q['old_text']:q['expected_count'] for q in m['source_replacement_counts'][rel]}
 for old,new in replacements:assert s.count(old)==counts[old],(rel,old,s.count(old));s=s.replace(old,new)
 compile(s,str(p),'exec');p.write_text(s)
# Generate only the one joint footprint in memory. Validate non-edge text nodes before writing it.
sys.path.insert(0,str(O/'tools'));import make_footprints as mf;ll=[];mf.fp_joint(ll);newlib='\n'.join(ll)+'\n';lib=O/'hardware/library/NexusFC.pretty/HeaderBoard_Joint.kicad_mod';oldlib=lib.read_text();oldtree,newtree=[V.parse_sexpr(x) for x in [oldlib,newlib]]
def nonedges(t):
 q=copy.deepcopy(t);q[:]=[x for x in q if not(isinstance(x,list) and any(V.atom(y[1])=='Edge.Cuts' for y in V.children(x,'layer')))];return q
ln=nonedges(newtree)
for q in V.children(ln,'descr'):q[1]=('string',V.atom(q[1]).replace('10.1 x 2.2','10.0 x 2.1'))
assert V.canonical(nonedges(oldtree))==V.canonical(ln),'non-edge library drift';lib.write_text(newlib)
(O/'hardware/nexus-style-fc.kicad_pcb').write_text(raw)
for n in ['manufacturing-project.kicad_pro','current-main-binding.json','child-model-binding.json']:shutil.copy2(S/n,O/n)
shutil.copy2(Q,O/'source-signal-proposal.json');shutil.copy2(M,O/'source-mechanical-proposal.json');tr={'status':'UNACCEPTED integrated source-bound signal and slot trial','source_directory':str(S),'source_board_sha256':sha(S/'hardware/nexus-style-fc.kicad_pcb'),'removed_uuids':removed,'added_primitives':added,'moved_vias':[],'footprint_changes':[],'routes':routes,'source_records':records,'mechanical_edge_changes':m['edge_changes'],'mechanical_keepout_changes':m['keepout_changes'],'mechanical_description_change':['10.0 x 2.1','10.1 x 2.2'],'source_signal_proposal_sha256':sha(Q),'source_mechanical_proposal_sha256':sha(M),'source_schematic_sha256':sha(S/'hardware/nexus-style-fc.kicad_sch'),'approved_scope':'Only complete .127 mm RPM/DSM/SBUS tracks, RPM inter-via span restored In4 to In2, sixteen J1 slot Edge.Cuts records and description, two keepout Y extents and matching project-local joint library/generator/checker. Fixed switch node, all vias, parts/pads/nets/stack/rules/body/child/model unchanged.'};(O/'transaction.json').write_text(json.dumps(tr,indent=2)+'\n')
b=k.LoadBoard(str(O/'hardware/nexus-style-fc.kicad_pcb'));mp={q.m_Uuid.AsString():q.GetNetname() for q in b.GetTracks()};mp.update({q.m_Uuid.AsString():q.GetNetname() for f in b.GetFootprints() for q in f.Pads()});tree=V.parse_sexpr(raw);pm={}
for tag in ['segment','via','arc']:
 for q in V.children(tree,tag):pm[V.source_uuid(q)]=V.atom(V.children(q,'net')[0][1])
for f in V.children(tree,'footprint'):
 for q in V.children(f,'pad'):
  nn=V.children(q,'net');pm[V.source_uuid(q)]=V.atom(nn[0][1]) if nn else ''
assert all(mp[u]==net for u,net in pm.items());(O/'pre-native-net-proof.json').write_text(json.dumps({'status':'PASS','parsed_native_net_identity_count':len(pm),'pre_refill_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb')},indent=2)+'\n')
cmd=[str(R/'runtime/kicad-cli'),'pcb','drc','--all-track-errors','--schematic-parity','--refill-zones','--save-board','--severity-all','--format','json','--exit-code-violations','-o',str(O/'native-drc.json'),str(O/'hardware/nexus-style-fc.kicad_pcb')];start=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (O/'native-drc.log').open('w') as f:p=subprocess.run(['timeout','--signal=INT','--kill-after=5s','150s']+cmd,stdout=f,stderr=subprocess.STDOUT)
assert p.returncode==5;d=json.loads((O/'native-drc.json').read_text());out={'command':cmd,'started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':p.returncode,'board_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'counts':dict(collections.Counter(q['type']+':'+q['severity'] for q in d['violations'])),'opens':len(d['unconnected_items']),'parity':len(d['schematic_parity'])};(O/'native-receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
