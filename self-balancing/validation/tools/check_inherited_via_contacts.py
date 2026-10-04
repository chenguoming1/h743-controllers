#!/usr/bin/python3
import os,json,collections,hashlib
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
D=Path(__file__).resolve().parent;SRC=Path('/workspace/shared/storm32-redesign/controller-r3s-p6/controller.kicad_pcb');H='64ac0d810d013d8a85491d8bd9672040b351f12e4e31b628105cdb2adbca5e90';sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();assert sha(SRC)==H;b=p.LoadBoard(str(SRC));uid=lambda t:t.m_Uuid.AsString();allobjects=list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()];layers=list(b.GetEnabledLayers().CuStack());report=json.loads((D/'via-attachments-64ac0d81.json').read_text());out=[]
for row in report['inherited_or_improved_shallow_groups']:
 net=row['net'];via=row['via_uuid'];contact_ids={q['uuid'] for q in row['candidate']['tracks']};objects={uid(t):t for t in allobjects if t.GetNetname()==net};adj={u:[] for u in objects};pairs=[]
 for i,(u,t) in enumerate(objects.items()):
  for v,o in list(objects.items())[:i]:
   for l in layers:
    if not(t.IsOnLayer(l) and o.IsOnLayer(l)):continue
    if t.GetEffectiveShape(l).GetClearance(o.GetEffectiveShape(l))>0:continue
    if (u==via and v in contact_ids or v==via and u in contact_ids) and b.GetLayerName(l)==row['layer']:continue
    adj[u].append(v);adj[v].append(u);break
 seen={via};parents={};todo=[via]
 while todo:
  u=todo.pop()
  for v in adj[u]:
   if v not in seen:seen.add(v);parents[v]=u;todo.append(v)
 reachable=contact_ids&seen;path=[]
 if reachable:
  cur=next(iter(reachable));path=[cur]
  while cur!=via:cur=parents[cur];path.append(cur)
 def label(u):
  q=objects[u];r={'uuid':u,'kind':q.GetClass()}
  if isinstance(q,p.PAD):r.update(reference=q.GetParentFootprint().GetReference(),pin=q.GetNumber())
  return r
 otherterminals=[]
 if not reachable:
  branch=set(contact_ids);todo=list(contact_ids)
  while todo:
   u=todo.pop()
   for v in adj[u]:
    if v not in branch:branch.add(v);todo.append(v)
  otherterminals=[label(u) for u in branch if isinstance(objects[u],(p.PAD,p.PCB_VIA))]
 out.append({'net':net,'layer':row['layer'],'via_uuid':via,'xy_mm':row['xy_mm'],'contact_group':row['candidate'],'has_alternate_copper_path_without_shallow_via_edges':bool(reachable),'alternate_path_objects':[label(u) for u in path],'isolated_branch_terminals_without_shallow_edges':otherterminals,'disposition':'INCIDENTAL COPPER GRAZE; ALTERNATE PATH EXISTS' if reachable else 'FUNCTIONAL SHALLOW ATTACHMENT; REPAIR REQUIRED'})
assert sha(SRC)==H;(D/'inherited-via-contact-dispositions-64ac0d81.json').write_text(json.dumps({'source_sha256':H,'results':out,'limits':'Alternate paths use exact native contacts; join-throat quality of those alternate paths is a separate global screen.'},indent=2)+'\n');print(json.dumps(out,indent=2))
