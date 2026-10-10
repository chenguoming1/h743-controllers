import inspect_access as a
from shapely.affinity import translate,rotate
from shapely.geometry import Point,LineString
import json,hashlib,math
m=a.m;net='ADC_BUS';remove={'6bf63e0b-d6e1-404c-8d41-db5d79061a6c','576ebcd8-0895-4502-9caa-8b8e82b84cb9'}
routes=[{'net':'ADC_BUS','layer':'B.Cu','width':.127,'points':[[15.284999,13.05],[16.99,13.05],[16.99,12.24]]},{'net':'ADC_BUS','layer':'In3.Cu','width':.127,'points':json.load(open(a.HERE/'trunk-In3.Cu46.json'))['points']},{'net':'ADC_BUS','layer':'F.Cu','width':.127,'points':[[21.99,17.9],[21.99,17.6],[22.,17.27]]},{'net':'ADC_BUS','layer':'B.Cu','width':.127,'points':[[16.38,8.0],[16.99,12.24]]},{'net':'GND','layer':'B.Cu','width':.25,'points':[[15.42,8.0],[16.4252,7.0556]]}]
routes[1]['points'][-1]=[22.,17.27]
modified=[]
for o,c,ms,d in m.OBJECTS:
 if o['uuid']in remove:continue
 if o.get('ref')=='R43':c={l:translate(g,0,.3)for l,g in c.items()};ms={l:translate(g,0,.3)for l,g in ms.items()}
 if o.get('ref')=='C31':
  change=lambda g:translate(rotate(g,180,origin=(14,24.1)),1.9,-16.1)
  c={l:change(g)for l,g in c.items()};ms={l:change(g)for l,g in ms.items()}
 modified.append((o,c,ms,d))
m.OBJECTS=modified;witness=[]
for r in routes:
 obs=a.obs(r['net'],r['layer'])[0]
 for o in obs:
  o['required_center_distance_mm']+=r['width']/2-m.HALF;o['moving_radius_mm']=r['width']/2
 # Account for every other newly added foreign-net route.
 for other in routes:
  if other['net']==r['net']or other['layer']!=r['layer']:continue
  obs.append({'object':'proposed-'+other['net'],'uuid':None,'net':other['net'],'kind':'track','category':'proposed_foreign_copper','layers':[r['layer']],'required_physical_gap_mm':.127,'moving_radius_mm':r['width']/2,'required_center_distance_mm':.127+r['width']/2,'geometry':LineString(other['points']).buffer(other['width']/2,quad_segs=128)})
 rr=m.check(LineString(r['points']),obs,True);witness.append({'route':r,'minimum':rr[0],'nearest':rr[:8],'violations':[o for o in rr if o['extra_clearance_mm']<m.ERROR]})
for q in [[16.99,12.24],[22,17.27]]:
 v=a.obs('ADC_BUS','F.Cu')[1];rr=m.check(Point(q),v,True);witness.append({'via':q,'minimum':rr[0],'nearest':rr[:8],'violations':[o for o in rr if o['extra_clearance_mm']<m.ERROR]})
for row in witness:print(json.dumps({k:v for k,v in row.items()if k!='nearest'}),flush=True)
out={'source_board_sha256':m.EXPECTED,'routes':routes,'vias':[[16.99,12.24],[22,17.27]],'remove_source_uuids':sorted(remove),'footprint_changes':{'R43':{'before':[22.5,17.6,0,'F.Cu'],'after':[22.5,17.9,0,'F.Cu']},'C31':{'before':[14,24.1,0,'B.Cu'],'after':[15.9,8,180,'B.Cu']}},'witnesses':witness,'passed':all(not r['violations']for r in witness),'ground_width_mm':.25}
(a.HERE/'proposal.json').write_text(json.dumps(out,indent=2)+'\n');assert out['passed']
