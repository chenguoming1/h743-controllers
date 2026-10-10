import plan,json,math,copy
from shapely.geometry import Point,LineString
from shapely.affinity import translate
m=plan.m;BASE=m.OBJECTS;remove={'4ac2092d-48da-4042-9f80-6d638e3072d9','4c08b337-8a52-4b54-91f6-5521720e8561','e712d11a-7e0e-4cb8-9a2a-275159c4142c','a502a7e6-5c8c-4e37-91e0-b48000060a82'};m.OBJECTS=[z for z in BASE if z[0]['uuid']not in remove];records={o['uuid']:o for o,c,ma,d in BASE}
def tc(net,layer,pts,w=.127):
 t,_,_=m.obstacles(net,layer)
 for o in t:o['moving_radius_mm']=w/2;o['required_center_distance_mm']=o['required_physical_gap_mm']+w/2
 return m.check(LineString(pts),t,True)
vcore=m.obstacles('+3V3_CORE','F.Cu')[1];vsbus=m.obstacles('SBUS_HV','F.Cu')[1];result={'source_board_sha256':m.EXPECTED,'removed_only_in_hypothesis':sorted(remove),'core':[],'source':[],'sink':[]}
for x,y in [(17.1,9.84),(17.1,9.85),(17.10,9.86),(17.095,9.85),(17.105,9.84),(17.095,9.84)]:
 q=[x,y];vc=m.check(Point(q),vcore,True);paths=[('B.Cu',[[17.554095,9.866127],q]),('F.Cu',[q,[16.648445,9.6]])];checks=[tc('+3V3_CORE',l,p,.2)for l,p in paths];ok=vc[0]['extra_clearance_mm']>=m.ERROR and all(c[0]['extra_clearance_mm']>=m.ERROR for c in checks);r={'xy':q,'passed':ok,'via_minimum':vc[0],'tracks':[{'layer':l,'points':p,'minimum':c[0]}for(l,p),c in zip(paths,checks)]};result['core'].append(r);print('core',q,ok,vc[0]['extra_clearance_mm'],[c[0]['extra_clearance_mm']for c in checks],flush=True)
for q in [[17.1,9.25],[17.125,9.25],[17.125,9.26],[17.13,9.26],[17.115,9.26],[17.12,9.265]]:
 vc=m.check(Point(q),vsbus,True);r={'xy':q,'minimum':vc[0],'passed':vc[0]['extra_clearance_mm']>=m.ERROR};result['source'].append(r);print('source',q,r['passed'],[(c['object'],c['extra_clearance_mm'])for c in vc[:2]],flush=True)
a=records['a502a7e6-5c8c-4e37-91e0-b48000060a82']['start'];b=records['a502a7e6-5c8c-4e37-91e0-b48000060a82']['end'];c=[round(a[0]+1.5,6),round(a[1]-1.5,6)];delta=.2;pts=[a,[a[0],round(a[1]-delta,6)],[round(c[0]-delta,6),c[1]],c,b];ac=tc('ADC_DIV_MID','In2.Cu',pts)
for q in [[19.55,18.1],[19.55,18.095],[19.56,18.1],[19.54,18.1]]:
 vc=m.check(Point(q),vsbus,True);gap=LineString(pts).distance(Point(q))-.4155;ok=vc[0]['extra_clearance_mm']>=m.ERROR and gap>=m.ERROR and ac[0]['extra_clearance_mm']>=m.ERROR;r={'xy':q,'passed':ok,'via_minimum':vc[0],'ADC_points':pts,'ADC_minimum':ac[0],'ADC_to_newvia_extra':gap};result['sink'].append(r);print('sink',q,ok,vc[0]['extra_clearance_mm'],gap,ac[0]['extra_clearance_mm'],flush=True)
(plan.HERE/'refined-local-repair-results.json').write_text(json.dumps(result,indent=2)+'\n')
