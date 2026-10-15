"""One bounded compact J6-join alternative; no source changes."""
import json,sys,math
from pathlib import Path
sys.path.insert(0,'/workspace/shared/nexus-usb-stack-review/r57-inner-pair')
import static_clearance as c
D=Path('/workspace/shared/nexus-usb-stack-review/r57-inner-pair/ports')
a=json.loads((D/'port-proposal.json').read_text())
remove={'dp_B6_1','dp_join_ingress_1','dp_join_ingress_2','dp_join_ingress_3','dm_connector_join_1','dm_connector_join_2','dm_connector_join_3'}
a['segments']=[s for s in a['segments'] if s['id'] not in remove]
for v in a['vias']:
 if v['id']=='dp_B6_via':v['at']=[108.66,129.82]
a['vias'].append(dict(kind='via',id='dm_B7_via',net='USB_DM',at=[108.08,129.77],diameter=.45,drill=.2,layers=['F.Cu','B.Cu']))
a['vias'].append(dict(kind='via',id='VBUS_C_relocated_via',net='VBUS_C',at=[109.245,129.845],diameter=.45,drill=.2,layers=['F.Cu','B.Cu']))
def poly(name,net,layer,pts,w=.15):
 for i,(u,v) in enumerate(zip(pts,pts[1:])):a['segments'].append(dict(kind='segment',id=f'{name}_{i+1}',net=net,layer=layer,start=u,end=v,width=w))
poly('compact_dp_B6','USB_DP','F.Cu',[(108.65,130.65),(108.65,130.25),(108.66,129.82)])
poly('compact_dp_B6_to_A6','USB_DP','In4.Cu',[(108.66,129.82),(108.075,127.375)])
poly('compact_dm_B7','USB_DM','F.Cu',[(108.15,130.65),(108.15,129.84),(108.08,129.77)])
poly('compact_dm_B7_to_A7','USB_DM','In3.Cu',[(108.08,129.77),(108.65,127.846)])
poly('VBUS_C_relocated_F','VBUS_C','F.Cu',[(109.245,129.845),(109.5,129.6)],.25)
poly('VBUS_C_relocated_B','VBUS_C','B.Cu',[(109.245,129.845),(109.245,130.1),(108.4,130.9)],.25)
poly('VBUS_C_relocated_In2','VBUS_C','In2.Cu',[(109.245,129.845),(109.245,129.15),(107.732,128.645)],.25)
a['replace_foreign_track_uuids']+=['9d44ed26-9c00-46f8-bae2-d6c9450e8c39','a8c14c58-c428-41b2-a1b5-19e9f92325b7','e585a894-f9ca-4ca8-a469-3926f53c3771']
a['replace_foreign_via_uuids']=['dec81706-decb-4019-9e9c-89950cffcba7']
a['remove_old_usb_via_uuids']=['db390431-9541-45e8-b28b-b2ca008f591a']
a['reuse_existing_vias']=[x for x in a['reuse_existing_vias'] if x not in a['remove_old_usb_via_uuids']]
a['new_vias']=[v for v in a['vias'] if v['id'] in ['dm_output_via','dp_B6_via','dm_B7_via','VBUS_C_relocated_via']]
a['notes']+=['Alternative replaces lower J6 excursion, adds one net USB through via versus baseline, uses short In4 DP and In3 DM joins; these launches are not continuously coupled.','All VBUS_C connections preserved: complete replacement of one via plus its three incident paths. CC1 is unaffected.','VBUS_C via foreign-pad minimum gap is near 0.130mm, so preserve exact coordinates and verify manufacturing/native DRC margins.']
(D/'compact-port-proposal.json').write_text(json.dumps(a,indent=2)+'\n')
c.foreign_tracks[:]=[s for s in c.foreign_tracks if s['uuid'] not in a['replace_foreign_track_uuids']]
c.foreign_vias[:]=[v for v in c.foreign_vias if v['uuid'] not in a.get('replace_foreign_via_uuids',[])]
fixed=[]
for s in a['segments']:
 ot=c.foreign_tracks[:];ov=c.foreign_vias[:];c.foreign_tracks[:]=[t for t in ot if t['net']!=s['net']];c.foreign_vias[:]=[v for v in ov if v['net']!=s['net']]
 for q in c.checkseg(s['net'],s['layer'],s['start'],s['end'],s['width']):fixed.append(dict(proposal=s['id'],**q))
 c.foreign_tracks[:]=ot;c.foreign_vias[:]=ov
for v in a['vias']:
 ot=c.foreign_tracks[:];ov=c.foreign_vias[:];c.foreign_tracks[:]=[t for t in ot if t['net']!=v['net']];c.foreign_vias[:]=[z for z in ov if z['net']!=v['net']]
 for q in c.checkvia(v['net'],v['at'],v['diameter']):fixed.append(dict(proposal=v['id'],**q))
 c.foreign_tracks[:]=ot;c.foreign_vias[:]=ov
mut=[];s=a['segments'];vs=a['vias']
for i,u in enumerate(s):
 for v in s[i+1:]:
  if u['net']!=v['net'] and u['layer']==v['layer']:mut.append(dict(a=u['id'],b=v['id'],gap_mm=c.seg_seg(u['start'],u['end'],v['start'],v['end'])-(u['width']+v['width'])/2))
for v in vs:
 for t in s:
  if v['net']!=t['net']:mut.append(dict(a=v['id'],b=t['id'],gap_mm=c.point_seg(v['at'],t['start'],t['end'])[0]-v['diameter']/2-t['width']/2))
for i,u in enumerate(vs):
 for v in vs[i+1:]:
  if u['net']!=v['net']:mut.append(dict(a=u['id'],b=v['id'],gap_mm=math.dist(u['at'],v['at'])-(u['diameter']+v['diameter'])/2))
mut.sort(key=lambda q:q['gap_mm'])
paste=[]
for v in vs:
 for p in c.pads:
  if any(x.endswith('.Paste') for x in p['layers']):
   d=c.seg_pad(v['at'],v['at'],p)
   paste.append(dict(via=v['id'],pad=f"{p['ref']}.{p['pin']}",pad_net=p['net'],drill_to_paste_gap_mm=d-v['drill']/2,annulus_to_paste_gap_mm=d-v['diameter']/2))
paste.sort(key=lambda q:q['annulus_to_paste_gap_mm'])
result=dict(fixed_hits=fixed,mutual_hits=[q for q in mut if q['gap_mm']<.127-1e-8],smallest_mutual_gaps=mut[:15],paste_drill_hits=[q for q in paste if q['drill_to_paste_gap_mm']<0],paste_annulus_hits=[q for q in paste if q['annulus_to_paste_gap_mm']<0],closest_paste_boundaries=paste[:15])
(D/'compact-port-screen.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
