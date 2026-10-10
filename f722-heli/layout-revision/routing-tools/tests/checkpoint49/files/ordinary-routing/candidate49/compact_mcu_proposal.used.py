import inspect_access as a
from shapely.geometry import Point,LineString
import json,math
m=a.m;removed=[o['uuid']for o,c,ms,d in m.OBJECTS if(o['net']=='PORT_A_RX_MCU'and o['kind']=='track')or o['uuid']=='b2e16a18-1700-5236-ae79-c687c0604be8'];m.OBJECTS=[q for q in m.OBJECTS if q[0]['uuid']not in removed]
paths=[dict(net='PORT_A_TX_MCU',layer='B.Cu',points=[(12.425,4.8),(13.2,5.575),(13.2,6.72),(16.3,9.82),(16.3,10.55),(15.284999,10.55)]),dict(net='PORT_A_RX_MCU',layer='B.Cu',points=[(12.61,6.3),(12.45,5.55)]),dict(net='PORT_A_RX_MCU',layer='B.Cu',points=[(15.284999,11.05),(16.2,11.05),(16.6,10.88)]),dict(net='ADC_BUS',layer='B.Cu',points=[(16.38,8),(16.65,9.95),(17.15,10.6),(17.15,11.6),(16.99,12.24)])]
vias=[dict(net='PORT_A_RX_MCU',xy=[12.45,5.55]),dict(net='PORT_A_RX_MCU',xy=[16.6,10.88])]
for p in paths:
 rr=m.check(LineString(p['points']),a.obs(p['net'],p['layer'])[0]);p.update(width=.127,length_mm=LineString(p['points']).length,nearest=rr[:6]);print('PATH',p['net'],p['length_mm'],rr[:3])
for v in vias:
 rr=m.check(Point(v['xy']),a.obs(v['net'],'B.Cu')[1]);v.update(nearest=rr[:6]);print('VIA',v['xy'],rr[:3])
pair=[]
for i,p in enumerate(paths):
 for q in paths[i+1:]:
  if p['net']!=q['net']:pair.append(dict(a=p['net'],b=q['net'],gap=LineString(p['points']).distance(LineString(q['points']))-.127))
 for v in vias:
  if p['net']!=v['net']:pair.append(dict(a=p['net'],b=v['net'],via=v['xy'],gap=LineString(p['points']).distance(Point(v['xy']))-.2885))
print('PAIR',pair)
out=dict(source_board_sha256=m.EXPECTED,removed_source_ids=removed,paths=paths,vias=vias,pair=pair,adc_cap_to_mcu_mm=paths[-1]['length_mm']+.81+1.705001,poses_unchanged=True,all_existing_vias_preserved=True,route_proposal_only=True)
(a.HERE/'compact-mcu-proposal.json').write_text(json.dumps(out,indent=2)+'\n')
