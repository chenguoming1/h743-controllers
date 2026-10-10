#!/usr/bin/env python3
"""Read-only exact connected pad groups before/after the BEC reconstruction."""
import sys,pathlib,json,hashlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'dsm-mcu-candidate43'))
import native43_geometry as G
from shapely.geometry import LineString
HERE=pathlib.Path(__file__).resolve().parent
p=json.loads((HERE/'joint-escape-proof.json').read_text())
rem=set(p['removed_track_uuids'])
old=[(o,c) for o,c,m,d in G.OBJECTS if o['net']=='+5V_BEC']
new=[(o,c) for o,c in old if o['uuid'] not in rem]
line=LineString(p['proposal']['bec_reconstruction']['points'])
new.append((dict(uuid='replacement-BEC-two-track-reconstruction',kind='track',net='+5V_BEC'),{'In3.Cu':line.buffer(.3,quad_segs=256)}))
def groups(items):
 pa=list(range(len(items)))
 def find(i):
  while pa[i]!=i:pa[i]=pa[pa[i]];i=pa[i]
  return i
 contacts=[]
 for i,(a,ac) in enumerate(items):
  for k in range(i):
   b,bc=items[k]
   if any(ac[l].distance(bc[l])<1e-9 for l in ac.keys()&bc.keys()):
    pa[find(i)]=find(k);contacts.append([a.get('key',a['uuid']),b.get('key',b['uuid'])])
 comp={}
 for i,(o,c) in enumerate(items):
  root=find(i);comp.setdefault(root,dict(objects=[],pads=[]))
  comp[root]['objects'].append(o.get('key',o['uuid']))
  if o['kind']=='pad':comp[root]['pads'].append(o['key'])
 return dict(object_count=len(items),component_count=len(comp),pad_groups=sorted([sorted(g['pads']) for g in comp.values() if g['pads']]),padless_components=[sorted(g['objects']) for g in comp.values() if not g['pads']],replacement_contacts=[x for x in contacts if 'replacement-BEC-two-track-reconstruction' in x])
a=groups(old);b=groups(new)
r=dict(schema='f722-read-only-BEC-pad-group-preservation/v1',board_sha256=G.EXPECTED,native_sha256=hashlib.sha256(G.SOURCE.read_bytes()).hexdigest(),geometry='native polygon touch/intersection; epsilon1e-9 mm. Replacement circular endcaps approximated within 0.000002 mm for connectivity, with exact shared centerline endpoints.',before=a,after=b,actual_connected_pad_groups_preserved=a['pad_groups']==b['pad_groups'],component_count_preserved=a['component_count']==b['component_count'])
(HERE/'bec-connected-pad-groups.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
