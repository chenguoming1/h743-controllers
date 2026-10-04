#!/usr/bin/python3
"""Read-only dangling-tree screen with vias treated as junctions, not loads.

Actual same-layer trace components form graph nodes joined to native pads/vias.
Pads and legitimate filled-zone contacts are protected anchors; all GND vias
remain protected because their return/stitch function is separately reviewed.
Iteratively peel non-anchor leaves. No loop or genuine two-anchor path is deleted
or classified by this screen. Native source remains unchanged.
"""
import argparse,collections,hashlib,json,os
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
from audit_single_terminal_copper import inventory
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();uid=lambda q:q.m_Uuid.AsString()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert sha(a.candidate)==a.sha256;I=inventory(a.candidate);b=p.LoadBoard(str(a.candidate));lands=[q for q in b.GetTracks() if isinstance(q,p.PCB_VIA)]+[q for f in b.GetFootprints() for q in f.Pads()];tracks={uid(q):q for q in b.GetTracks() if not isinstance(q,p.PCB_VIA)};layers=list(b.GetEnabledLayers().CuStack());adj=collections.defaultdict(set);nodes={};anchors=set();zones=collections.defaultdict(list)
 def edge(x,y):adj[x].add(y);adj[y].add(x)
 for q in lands:
  n=uid(q);nodes[n]={'kind':'via' if isinstance(q,p.PCB_VIA) else 'pad','net':q.GetNetname(),'uuid':n,'xy_mm':[q.GetPosition().x/1e6,q.GetPosition().y/1e6]};adj[n]
  if isinstance(q,p.PAD):nodes[n]['reference']=q.GetParentFootprint().GetReference()+'.'+q.GetNumber();anchors.add(n)
  elif q.GetNetname()=='GND':anchors.add(n)
 for z in b.Zones():
  if z.GetIsRuleArea():continue
  for l in layers:
   if z.IsOnLayer(l) and z.HasFilledPolysForLayer(l):
    ps=z.GetFilledPolysList(l)
    for i in range(ps.OutlineCount()):
     zp=p.SHAPE_POLY_SET(ps.COutline(i))
     for j in range(ps.HoleCount(i)):zp.AddHole(ps.CHole(i,j),0)
     n='zone:'+uid(z)+':'+str(l)+':'+str(i);nodes[n]={'kind':'zone','net':z.GetNetname(),'layer':b.GetLayerName(l)};anchors.add(n);zones[z.GetNetname(),l].append((n,zp))
 for i,row in enumerate(I['all_component_terminal_inventory']):
  n='component:'+str(i);nodes[n]={'kind':'trace_component',**row};adj[n]
  for t in row['terminals']:edge(n,t['uuid'])
  l=b.GetLayerID(row['layer'])
  for z,zp in zones[row['net'],l]:
   if any(tracks[u].GetEffectiveShape(l).GetClearance(zp)<=0 for u in row['track_uuids']):edge(n,z)
 for i,t in enumerate(lands):
  for u in lands[:i]:
   if t.GetNetname()!=u.GetNetname():continue
   if any(t.IsOnLayer(l) and u.IsOnLayer(l) and t.GetEffectiveShape(l).GetClearance(u.GetEffectiveShape(l))<=0 for l in layers):edge(uid(t),uid(u))
  for l in layers:
   if t.IsOnLayer(l):
    for z,zp in zones[t.GetNetname(),l]:
     if t.GetEffectiveShape(l).GetClearance(zp)<=0:edge(uid(t),z)
 degree={n:len(adj[n]) for n in nodes};todo=collections.deque(n for n in nodes if n not in anchors and degree[n]<=1);peeled=set()
 while todo:
  n=todo.popleft()
  if n in peeled:continue
  peeled.add(n)
  for u in adj[n]:
   if u in peeled:continue
   degree[u]-=1
   if u not in anchors and degree[u]<=1:todo.append(u)
 candidates={frozenset(q['uuid'] for q in c['tracks']):c for c in I['candidates']};groups=[];unseen=set(peeled)
 while unseen:
  first=min(unseen);group={first};queue=[first];unseen.remove(first)
  while queue:
   n=queue.pop()
   for u in adj[n]&unseen:unseen.remove(u);group.add(u);queue.append(u)
  boundary=sorted(set().union(*(adj[n]-group for n in group)));vs=[nodes[n] for n in sorted(group) if nodes[n]['kind']=='via'];cs=[nodes[n] for n in sorted(group) if nodes[n]['kind']=='trace_component'];contained=not vs and all(candidates.get(frozenset(q['track_uuids']),{}).get('classification')=='TERMINAL-CONTAINED COPPER' for q in cs);groups.append({'net':nodes[first]['net'],'classification':'BENIGN LAND-CONTAINED COPPER' if contained else 'DANGLING COPPER TREE; REVIEW','peeled_vias':vs,'peeled_trace_components':cs,'remaining_attachment_nodes':[nodes[n] for n in boundary],'remaining_attachment_count':len(boundary)})
 out={'status':'REVIEW REQUIRED' if any(q['classification'].endswith('REVIEW') for q in groups) else 'PASS NO EXPOSED PAD-ANCHORED DANGLING TREES','candidate_sha256':a.sha256,'source':str(a.candidate),'audit_script_sha256':sha(Path(__file__)),'component_census_script_sha256':sha(Path(__file__).with_name('audit_single_terminal_copper.py')),'routed_nets':I['routed_nets'],'graph_nodes':len(nodes),'peeled_node_count':len(peeled),'peeled_via_count':sum(len(q['peeled_vias']) for q in groups),'trees':groups,'review_trees':[q for q in groups if q['classification'].endswith('REVIEW')],'method':__doc__};assert sha(a.candidate)==a.sha256;a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'peeled_via_count':out['peeled_via_count'],'review_trees':[{'net':q['net'],'vias':q['peeled_vias'],'track_count':sum(len(c['track_uuids']) for c in q['peeled_trace_components']),'boundary':q['remaining_attachment_nodes']} for q in out['review_trees']]},indent=2))
if __name__=='__main__':main()
