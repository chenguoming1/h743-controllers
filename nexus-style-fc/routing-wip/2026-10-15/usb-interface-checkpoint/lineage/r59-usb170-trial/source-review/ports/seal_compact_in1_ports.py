"""Read-only final donor contact comparison and orientation path accounting."""
import sys,json,math,hashlib
from pathlib import Path
sys.path.insert(0,'/workspace/shared/nexus-usb-stack-review/r57-inner-pair')
import static_clearance as c
D=Path('/workspace/shared/nexus-usb-stack-review/r57-inner-pair/ports');a=json.loads((D/'compact-in1-port-proposal.json').read_text())
def layer_set(o):
 if o['kind']=='segment':return {o['layer']}
 if o['kind']=='via' or '*.Cu' in o.get('layers',[]):return set(c.ls)
 return set(o['layers'])
def touch(u,v):
 if u['net']!=v['net'] or not layer_set(u)&layer_set(v):return False
 if u['kind']=='pad' and v['kind']=='pad':raise ValueError('No pad-pad comparison is required.')
 if v['kind']=='pad':u,v=v,u
 if u['kind']=='pad':
  if v['kind']=='segment':return c.seg_pad(v['start'],v['end'],u)<=v['width']/2+1e-9
  return c.seg_pad(v['at'],v['at'],u)<=v['diameter']/2+1e-9
 if u['kind']=='via' and v['kind']=='segment':u,v=v,u
 if u['kind']=='segment' and v['kind']=='segment':return c.seg_seg(u['start'],u['end'],v['start'],v['end'])<=(u['width']+v['width'])/2+1e-9
 if u['kind']=='segment':return c.point_seg(v['at'],u['start'],u['end'])[0]<=(u['width']+v['diameter'])/2+1e-9
 return math.dist(u['at'],v['at'])<=(u['diameter']+v['diameter'])/2+1e-9
summary=[]
for net,prefix in [('LED1_K','LED1_K_donor'),('VBUS_C','VBUS_C_relocated')]:
 old=[o for o in c.tracks+c.vias if o['net']==net and o['uuid'] in a['replace_foreign_track_uuids']+a['replace_foreign_via_uuids']]
 new=[o for o in a['segments']+a['vias'] if o['net']==net and o['id'].startswith(prefix)]
 oldids={o['uuid'] for o in old};retained=[o for o in c.tracks+c.vias+c.pads if o['net']==net and o['uuid'] not in oldids]
 contacts=[]
 for o in retained:
  oc=[v['uuid'] for v in old if touch(v,o)];nc=[v['id'] for v in new if touch(v,o)]
  if oc or nc:contacts.append(dict(retained_uuid=o['uuid'],retained_object=o,old_contacts=oc,new_contacts=nc))
 summary.append(dict(net=net,removed_objects=old,replacement_object_ids=[o['id'] for o in new],retained_object_count_examined=len(retained),contact_comparison=contacts,lost_retained_contacts=[q['retained_uuid'] for q in contacts if q['old_contacts'] and not q['new_contacts']],added_retained_contacts=[q['retained_uuid'] for q in contacts if q['new_contacts'] and not q['old_contacts']]))
(D/'compact-in1-donor-contact-comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
planar=json.loads((D/'compact-in1-port-lengths.json').read_text())
via_defs={v['id']:v for v in a['vias']}
def transition(v,fr,to):return dict(via_id=v,at=via_defs[v]['at'],from_layer=fr,to_layer=to,used_barrel_mm=abs(c.zcenters[fr]-c.zcenters[to]))
paths={
 'A_USB_DP':[transition('dp_A6_via','F.Cu','In3.Cu'),transition('dp_pin3_via','In3.Cu','B.Cu'),transition('dp_output_via','B.Cu','In3.Cu')],
 'A_USB_DM':[transition('dm_connector_via','F.Cu','B.Cu'),transition('dm_output_via','B.Cu','In3.Cu')],
 'B_USB_DP':[transition('dp_B6_via','F.Cu','In1.Cu'),transition('dp_A6_via','In1.Cu','In3.Cu'),transition('dp_pin3_via','In3.Cu','B.Cu'),transition('dp_output_via','B.Cu','In3.Cu')],
 'B_USB_DM':[transition('dm_B7_via','F.Cu','In3.Cu'),transition('dm_connector_via','In3.Cu','B.Cu'),transition('dm_output_via','B.Cu','In3.Cu')]
}
pr=[]
for key,trans in paths.items():
 orient,net=key.split('_',1);pl=planar[orient+'_orientation_centerline_mm'][net];barrel=sum(t['used_barrel_mm'] for t in trans)
 pr.append(dict(orientation=orient,net=net,planar_centerline_mm=pl,via_transition_count=len(trans),transitions=trans,used_barrel_mm=barrel,planar_plus_used_barrel_mm=pl+barrel))
(D/'compact-in1-path-via-accounting.json').write_text(json.dumps(dict(copper_center_z_mm=c.zcenters,paths=pr,note='Physical centerline bookkeeping only; not delay or impedance matching. Ordinary unused through-via barrel portions remain. Pad propagation excluded.'),indent=2)+'\n')
print(json.dumps(dict(donors=[dict(net=q['net'],retained_objects=q['retained_object_count_examined'],touched_retained_objects=len(q['contact_comparison']),lost=q['lost_retained_contacts'],added=q['added_retained_contacts']) for q in summary],paths=pr),indent=2))
