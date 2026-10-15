"""Prove proposed copper path crosses preserved external bridges; read-only geometry."""
import sys,json,collections
from pathlib import Path
sys.path.insert(0,'/workspace/shared/nexus-usb-stack-review/r57-inner-pair')
import static_clearance as c
D=Path('/workspace/shared/nexus-usb-stack-review/r57-inner-pair/ports');proposal=json.loads((D/'compact-port-proposal.json').read_text())
objects=proposal['segments']+proposal['vias']+[dict(p,id=f"{p['ref']}.{p['pin']}") for p in c.pads if p['net'] in ['USB_DP','USB_DM','VBUS_C']]+[dict(t,id=t['uuid']) for t in c.tracks if t['net']=='VBUS_C' and t['uuid'] not in proposal['replace_foreign_track_uuids']]+[dict(v,id=v['uuid']) for v in c.vias if v['net']=='VBUS_C' and v['uuid'] not in proposal['replace_foreign_via_uuids']]
def layers(a):return {a['layer']} if a['kind']=='segment' else set(c.ls) if a['kind']=='via' else set(a['layers'])
def touch(a,b):
 if a['net']!=b['net'] or not layers(a)&layers(b):return False
 if a['kind']=='pad' and b['kind']=='pad':return False
 if b['kind']=='pad':a,b=b,a
 if a['kind']=='pad':
  if b['kind']=='segment':return c.seg_pad(b['start'],b['end'],a)<=b['width']/2+1e-9
  return c.seg_pad(b['at'],b['at'],a)<=b['diameter']/2+1e-9
 if a['kind']=='via' and b['kind']=='segment':a,b=b,a
 if a['kind']=='segment' and b['kind']=='segment':return c.seg_seg(a['start'],a['end'],b['start'],b['end'])<=(a['width']+b['width'])/2+1e-9
 if a['kind']=='segment':return c.point_seg(b['at'],a['start'],a['end'])[0]<=(a['width']+b['diameter'])/2+1e-9
 return c.math.dist(a['at'],b['at'])<=(a['diameter']+b['diameter'])/2+1e-9
def reachable(src,dst,exclude):
 ob=[a for a in objects if not any(a['id'].startswith(x) for x in exclude)];adj=collections.defaultdict(set)
 for i,a in enumerate(ob):
  for b in ob[i+1:]:
   if touch(a,b):adj[a['id']].add(b['id']);adj[b['id']].add(a['id'])
 seen={src};todo=[src]
 while todo:
  u=todo.pop()
  for v in adj[u]-seen:seen.add(v);todo.append(v)
 return dst in seen
results=[]
for net,sources,dest,cut in [('DP',['J6.A6','J6.B6'],'dp_trunk_fanout_2','dp_bridge_preserve'),('DM',['J6.A7','J6.B7'],'dm_trunk_fanout_4','dm_bridge_preserve')]:
 for source in sources:results.append(dict(net=net,source=source,destination=dest,connected=reachable(source,dest,[]),connected_after_external_bridge_cut=reachable(source,dest,[cut])))
(D/'compact-protection-cut-screen.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))

vbus=[dict(source=src,destination='F1.1',connected=reachable(src,'F1.1',[])) for src in ['J6.A4','J6.A9','J6.B4','J6.B9']]
(D/'compact-vbus-closure-screen.json').write_text(json.dumps(vbus,indent=2)+'\n');print(json.dumps(vbus,indent=2))
