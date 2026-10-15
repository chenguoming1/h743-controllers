"""Read-only complete same-net In2 copper components and all their via/pad ports. No board writes or route generation."""
import sys
sys.path.insert(0,'/workspace/shared/nexus-usb-stack-review/r57-inner-pair')
from static_clearance import *
R=D/'reference';report=json.loads((R/'reference-analysis.json').read_text())
interest={t['source']['uuid'] for t in report['non_ground_in2_tracks'] if t['projected_0200_zone_clearance_overlap_mm']>0}
components=[]
for net in sorted({t['net'] for t in tracks if t['uuid'] in interest}):
 ts=[t for t in tracks if t['net']==net and t['layer']=='In2.Cu'];adj={i:[] for i in range(len(ts))}
 for i in range(len(ts)):
  for j in range(i):
   if seg_seg(ts[i]['start'],ts[i]['end'],ts[j]['start'],ts[j]['end'])<=(ts[i]['width']+ts[j]['width'])/2+1e-9:adj[i].append(j);adj[j].append(i)
 seen=set()
 for seed in range(len(ts)):
  if seed in seen:continue
  cc=set();todo=[seed]
  while todo:
   q=todo.pop()
   if q in cc:continue
   cc.add(q);todo.extend(adj[q])
  seen|=cc;ct=[ts[i] for i in sorted(cc)]
  if not any(t['uuid'] in interest for t in ct):continue
  ports=[]
  for v in vias:
   if v['net']!=net:continue
   touches=[t['uuid'] for t in ct if point_seg(v['at'],t['start'],t['end'])[0]<=(v['diameter']+t['width'])/2+1e-9]
   if touches:ports.append(dict(source=v,touching_in2_segments=touches,other_layer_incident_tracks=[t for t in tracks if t['net']==net and t['layer']!='In2.Cu' and point_seg(v['at'],t['start'],t['end'])[0]<=(v['diameter']+t['width'])/2+1e-9]))
  padports=[]
  for p in pads:
   if p['net']!=net or ('*.Cu' not in p['layers'] and 'In2.Cu' not in p['layers']):continue
   touches=[t['uuid'] for t in ct if seg_pad(t['start'],t['end'],p)<=t['width']/2+1e-9]
   if touches:padports.append(dict(source=p,touching_in2_segments=touches))
  endpoints=collections.Counter(tuple(p) for t in ct for p in [t['start'],t['end']]);loose=[]
  for p,count in endpoints.items():
   if count!=1:continue
   touch_via=[v['source']['uuid'] for v in ports if math.dist(p,v['source']['at'])<=v['source']['diameter']/2+max(t['width']/2 for t in ct)+1e-9]
   # Find copper overlap within own component even when center endpoints do not coincide.
   overlap=[t['uuid'] for t in ct if p not in (tuple(t['start']),tuple(t['end'])) and point_seg(p,t['start'],t['end'])[0]<=t['width']/2+max(q['width']/2 for q in ct if p in (tuple(q['start']),tuple(q['end'])))+1e-9]
   loose.append(dict(at=p,via_ports=touch_via,overlapping_same_net_segment_uuids=overlap))
  components.append(dict(net=net,segment_count=len(ct),total_source_length_mm=sum(t['length_mm'] for t in ct),segments=ct,via_ports=ports,through_pad_ports=padports,source_centerline_leaf_points=loose,overlapping_interest_segments=[t['uuid'] for t in ct if t['uuid'] in interest]))
# Source through-via edge-clearance obstructions: full source incident routes are listed, not silently removed.
edge_vias=[]
for o in report['non_ground_through_vias']:
 if not o['projected_0200_zone_clearance_overlap_mm']:continue
 v=o['source'];inc=[t for t in tracks if t['net']==v['net'] and point_seg(v['at'],t['start'],t['end'])[0]<=(t['width']+v['diameter'])/2+1e-9]
 edge_vias.append(dict(**o,source_incident_tracks=inc))
obj=dict(source_sha256=H,complete_same_net_in2_components=components,additional_retained_via_clearance_obstructions=edge_vias,limits=['Components based on exact planar capsule contact, not native net connectivity or a routed candidate.','Every source segment and all physically touched through-via ports in each listed component are included. Branches can be separately rerouted only with every incident junction preserved.','No candidate replacement was drawn, solved, or tested. A full component transaction is a conditional scope, not clearance-certified feasibility.'])
(R/'complete-donor-ports.json').write_text(json.dumps(obj,indent=2)+'\n')
print('COMPONENTS')
for c in components:
 print(c['net'],c['segment_count'],round(c['total_source_length_mm'],5),'ports',[(p['source']['at'],p['source']['uuid']) for p in c['via_ports']])
print('EDGE VIA PORTS')
for v in edge_vias:print(v['source'],v['source_incident_tracks'])
assert hashlib.sha256(S.read_bytes()).hexdigest()==H
