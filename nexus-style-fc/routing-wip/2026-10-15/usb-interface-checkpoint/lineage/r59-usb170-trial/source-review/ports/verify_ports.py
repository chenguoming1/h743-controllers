"""Read-only, bounded analytic port proposal. Does not load native KiCad or modify source."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,'/workspace/shared/nexus-usb-stack-review/r57-inner-pair')
import static_clearance as c
D=Path('/workspace/shared/nexus-usb-stack-review/r57-inner-pair/ports')
segs=[];vs=[]
def poly(name,net,layer,pts,w=.15):
 for i,(a,b) in enumerate(zip(pts,pts[1:])):segs.append(dict(kind='segment',id=f'{name}_{i+1}',net=net,layer=layer,start=a,end=b,width=w))
def via(name,net,at):vs.append(dict(kind='via',id=name,net=net,at=at,diameter=.45,drill=.2,layers=['F.Cu','B.Cu']))
poly('dp_A6','USB_DP','F.Cu',[(108.15,128.95),(108.15,127.45),(108.075,127.375)])
poly('dp_B6','USB_DP','F.Cu',[(108.65,130.65),(108.65,131.754)])
poly('dp_join_ingress','USB_DP','In3.Cu',[(108.65,131.754),(108.152,131.237),(108.152,127.452),(108.075,127.375),(108.075,123.826),(108.152,123.749)])
poly('dp_pin3_ingress','USB_DP','B.Cu',[(108.152,123.749),(108.091,123.749),(107.847,123.993),(107.847,124.35),(108.55,124.35)])
poly('dm_connector_join','USB_DM','F.Cu',[(108.15,130.65),(108.15,129.88),(108.65,129.38),(108.65,128.95),(108.65,127.846)])
poly('dm_pin1_ingress','USB_DM','B.Cu',[(108.65,127.846),(108.65,126.9),(108.55,126.8),(108.55,126.25)])
poly('dp_bridge_preserve','USB_DP','B.Cu',[(108.55,124.35),(110.85,124.35)])
poly('dm_bridge_preserve','USB_DM','B.Cu',[(108.55,126.25),(109.253,126.25),(110.147,126.25),(110.85,126.25)])
poly('dp_pin4_egress','USB_DP','B.Cu',[(110.85,124.35),(110.85,124.725),(109.575,124.725)])
poly('dm_pin6_egress','USB_DM','B.Cu',[(110.85,126.25),(110.85,125.8),(109.625,125.8),(109.625,125.31)])
poly('dp_trunk_fanout','USB_DP','In3.Cu',[(109.575,124.725),(109.5115,124.6615),(109.5115,124.0)])
poly('dm_trunk_fanout','USB_DM','In3.Cu',[(109.625,125.31),(110.05,124.885),(110.05,124.4),(109.7885,124.1385),(109.7885,124.0)])
via('dp_A6_via','USB_DP',(108.075,127.375));via('dp_B6_via','USB_DP',(108.65,131.754));via('dp_pin3_via','USB_DP',(108.152,123.749));via('dm_connector_via','USB_DM',(108.65,127.846));via('dp_output_via','USB_DP',(109.575,124.725));via('dm_output_via','USB_DM',(109.625,125.31))
poly('LED1_K_donor','LED1_K','In2.Cu',[(108.56,124.36),(108.7,124.5),(108.7,125.3),(109.2,125.8),(110.0,125.8),(110.775,126.575)],.127)
donor_uuid='7fed82a0-bca6-4de2-afbb-42c2e3662bcd'
orig_tracks=c.foreign_tracks[:]
c.foreign_tracks[:]=[t for t in orig_tracks if t['uuid']!=donor_uuid]
fixed_hits=[]
for s in segs:
 save=c.foreign_tracks[:];c.foreign_tracks[:]=[t for t in save if t['net']!=s['net']]
 for r in c.checkseg(s['net'],s['layer'],s['start'],s['end'],s['width']):fixed_hits.append(dict(proposal=s['id'],**r))
 c.foreign_tracks[:]=save
for v in vs:
 for r in c.checkvia(v['net'],v['at'],v['diameter']):fixed_hits.append(dict(proposal=v['id'],**r))
mutual=[]
for i,a in enumerate(segs):
 for b in segs[i+1:]:
  if a['net']!=b['net'] and a['layer']==b['layer']:
   mutual.append(dict(a=a['id'],b=b['id'],gap_mm=c.seg_seg(a['start'],a['end'],b['start'],b['end'])-(a['width']+b['width'])/2))
for v in vs:
 for s in segs:
  if v['net']!=s['net']:mutual.append(dict(a=v['id'],b=s['id'],gap_mm=c.point_seg(v['at'],s['start'],s['end'])[0]-v['diameter']/2-s['width']/2))
for i,a in enumerate(vs):
 for b in vs[i+1:]:
  if a['net']!=b['net']:mutual.append(dict(a=a['id'],b=b['id'],gap_mm=math.dist(a['at'],b['at'])-(a['diameter']+b['diameter'])/2))
mutual.sort(key=lambda x:x['gap_mm'])
paste=[]
for v in vs:
 for p in c.pads:
  if p['net']==v['net'] and any(l.endswith('.Paste') for l in p['layers']):
   g=c.seg_pad(v['at'],v['at'],p)-v['drill']/2
   if g<0:paste.append(dict(via=v['id'],pad=p['uuid'],drill_to_paste_boundary_mm=g))
bridges={'34111c85-6920-47b2-8378-5f4b143fa938','3a64059b-ba0e-4f2e-8e31-d65de297c836','f746048e-a455-4f00-84d8-c574ad90336b','2bb5dd39-b4da-41e5-ad25-1a3813fe3eef'}
local_usb=[t for t in c.usbtracks if min(t['start'][1],t['end'][1])>=123.749]
proposal=dict(source=str(c.S),sha256=c.H,layer='In3.Cu',width_mm=.15,minimum_clearance_mm=.127,segments=segs,vias=vs,preserve_bridge_uuids=sorted(bridges),replace_local_usb_track_uuids=[t['uuid'] for t in local_usb if t['uuid'] not in bridges],replace_foreign_track_uuids=[donor_uuid],reuse_existing_vias=[v['uuid'] for v in c.usbvias if v['at'][1]>123],new_vias=[v for v in vs if v['id']=='dm_output_via'],handoff={'USB_DP':[109.5115,124.0],'USB_DM':[109.7885,124.0]},notes=['No board edited. Analytic screen only, not native DRC or impedance validation.','Preserve original bridge copper and its UUIDs rather than recreate duplicates. Bridge entries here are present solely for mutual screening.','Replace all upstream and downstream USB routing that conflicts with the new full topology; parent owns completion beyond the listed output handoff.','A/B USB-C joins are the only unavoidable branches; no protection bypass, bridge-center launch, or dead-ended stubs is included.','Donor retains .127mm signal width; no power widths or ground contacts change.','Ordinary through vias have .45mm diameter/.20mm drill; all new via drills clear pasted SMD pads.'])
(D/'port-proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
report=dict(fixed_object_hit_count=len(fixed_hits),fixed_hits=fixed_hits,mutual_hit_count=sum(x['gap_mm']<.127-1e-8 for x in mutual),mutual_hits=[x for x in mutual if x['gap_mm']<.127-1e-8],smallest_mutual_gaps=mutual[:25],pasted_drill_intersections=paste)
(D/'port-screen.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
