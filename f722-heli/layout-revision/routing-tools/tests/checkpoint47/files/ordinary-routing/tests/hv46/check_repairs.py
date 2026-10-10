import plan,json,copy,math,pathlib
from shapely.geometry import Point,LineString
from shapely.affinity import translate
m=plan.m;BASE=m.OBJECTS;oldvia='4ac2092d-48da-4042-9f80-6d638e3072d9';ct=['4c08b337-8a52-4b54-91f6-5521720e8561','e712d11a-7e0e-4cb8-9a2a-275159c4142c'];adc='a502a7e6-5c8c-4e37-91e0-b48000060a82';removed={oldvia,*ct,adc};m.OBJECTS=[z for z in BASE if z[0]['uuid']not in removed]
records={o['uuid']:o for o,c,ma,d in BASE}
def exact(net,layer,pts,width=.127):
 t,v,_=m.obstacles(net,layer)
 for o in t:o['moving_radius_mm']=width/2;o['required_center_distance_mm']=o['required_physical_gap_mm']+width/2
 return m.check(LineString(pts),t,True)
def via(net,xy):return m.check(Point(xy),m.obstacles(net,'F.Cu')[1],True)
out=[]
for q in [[17.110541,9.86],[17.110541,9.88],[17.110541,9.90],[17.08,9.9],[17.14,9.9]]:
 paths=[{'layer':'B.Cu','points':[[17.554095,9.866127],q]},{'layer':'F.Cu','points':[q,[16.648445,9.6]]}];v=via('+3V3_CORE',q);checks=[exact('+3V3_CORE',r['layer'],r['points'],.2)for r in paths];bad=[[x['object'],x['net'],x['extra_clearance_mm']]for x in v if x['extra_clearance_mm']<m.ERROR];r={'kind':'CORE','via':q,'via_violations':bad,'paths':paths,'track_violations':[[[x['object'],x['net'],x['extra_clearance_mm']]for x in z if x['extra_clearance_mm']<m.ERROR]for z in checks]};out.append(r);print(json.dumps(r),flush=True)
a=records[adc]['start'];b=records[adc]['end']
for q in [[19.55,18.075],[19.6,18.075],[19.625,18.075],[19.6,18.09],[19.65,18.09]]:
 v=via('SBUS_HV',q);bad=[[x['object'],x['net'],x['extra_clearance_mm']]for x in v if x['extra_clearance_mm']<m.ERROR];print('SBUSsink',q,bad,flush=True)
 for delta in [.10,.15,.2,.25]:
  # Rejoin the unchanged diagonal after a1.5 mm local dogleg.
  c=[round(a[0]+1.5,6),round(a[1]-1.5,6)];p=[[a[0],a[1]],[a[0],round(a[1]-delta,6)],[c[0]-delta,c[1]],c,b];rr=exact('ADC_DIV_MID','In2.Cu',p);margin=LineString(p).distance(Point(q))-(.225+.127+.0635);r={'kind':'ADC','SBUSvia':q,'points':p,'delta':delta,'via_violations':bad,'new_via_to_ADC_extra':margin,'violations':[[x['object'],x['net'],x['extra_clearance_mm']]for x in rr if x['extra_clearance_mm']<m.ERROR]};out.append(r)
  if not r['violations']and not bad and margin>=m.ERROR:print('COMPLETE LOCAL',json.dumps(r),flush=True)
(plan.HERE/'local-repair-results.json').write_text(json.dumps({'source_board_sha256':m.EXPECTED,'removed_only_in_hypothesis':sorted(removed),'results':out},indent=2)+'\n')
