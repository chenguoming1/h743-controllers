import plan,json,copy,math
from shapely.geometry import Point,LineString
from shapely.affinity import translate
m=plan.m;BASE=m.OBJECTS;R=json.load(open(plan.HERE/'refined-local-repair-results.json'));REMOVE=set(R['removed_only_in_hypothesis']);m.OBJECTS=[z for z in BASE if z[0]['uuid']not in REMOVE];ROWS={o['uuid']:(o,c,mask,d)for o,c,mask,d in BASE};CORE=next(r for r in R['core']if r['passed']);SINK=next(r for r in R['sink']if r['xy']==[19.55,18.1]);SOURCE=[17.13,9.26];TARGET=SINK['xy'];repairs=[]
o,c,mask,d=ROWS['4ac2092d-48da-4042-9f80-6d638e3072d9'];dx,dy=[CORE['xy'][i]-o['xy'][i]for i in range(2)];no=copy.deepcopy(o);no['uuid']='hypothesis-CORE-via';no['xy']=CORE['xy'];m.OBJECTS.append((no,{l:translate(g,dx,dy)for l,g in c.items()},{},translate(d,dx,dy)))
for j,r in enumerate(CORE['tracks']+[{'layer':'In2.Cu','points':SINK['ADC_points']} ]):
 net='+3V3_CORE'if j<2 else'ADC_DIV_MID';w=.2 if j<2 else.127
 for k,(a,b)in enumerate(zip(r['points'],r['points'][1:])):
  o={'uuid':f'hypothesis-{net}-{j}-{k}','kind':'track','net':net,'start':a,'end':b,'width':w};g=LineString([a,b]).buffer(w/2+.000001,quad_segs=128);m.OBJECTS.append((o,{r['layer']:g},{},None));repairs.append({'net':net,'layer':r['layer'],'points':[a,b],'width':w})
# Include the other worker's known proposal as extra obstacles, without claiming
# those objects exist on accepted source46 or are a completed ADC_BUS design.
ADC=json.load(open(plan.HERE/'planned_adc_obstacles.json'));assert ADC['source_board_sha256']==m.EXPECTED
m.OBJECTS=[(o,{l:translate(g,0,.3)for l,g in c.items()},{l:translate(g,0,.3)for l,g in mask.items()},d)if o.get('ref')=='R43'else(o,c,mask,d)for o,c,mask,d in m.OBJECTS]
for i,q in enumerate(ADC['ADC_BUS_vias_mm']):
 o={'uuid':'planned-ADC-BUS-via-'+str(i),'kind':'via','net':'ADC_BUS','xy':q,'barrel_layers':m.N['copper_layers']};g=Point(q).buffer(.225001,quad_segs=128);dr=Point(q).buffer(.100001,quad_segs=128);m.OBJECTS.append((o,{l:g for l in m.N['copper_layers']},{},dr))
for i,(a,b)in enumerate(zip(ADC['ADC_BUS_In3_points_mm'],ADC['ADC_BUS_In3_points_mm'][1:])):
 o={'uuid':'planned-ADC-BUS-In3-'+str(i),'kind':'track','net':'ADC_BUS','start':a,'end':b,'width':.127};m.OBJECTS.append((o,{'In3.Cu':LineString([a,b]).buffer(.063501,quad_segs=128)},{},None))
def obstacles(layer):return plan.trace_obs('SBUS_HV',layer,'U16.2')[0]
def tracecheck(layer,points):return m.check(LineString(points),obstacles(layer),True)
def viac(xy):
 vv=m.obstacles('SBUS_HV','F.Cu')[1]
 for o,c,mask,d in BASE:
  if o['net']=='SBUS_HV'and o['kind']!='pad':
   for l,g in c.items():
    if l in plan.KEY['U16.2']['copper']:g=g.difference(m.geom(plan.KEY['U16.2']['copper'][l]))
    if not g.is_empty:vv.append({'object':o['uuid'],'uuid':o['uuid'],'net':'SBUS_HV','kind':o['kind'],'category':'same_net_other_branch_outside_TVS_pad','layers':[l],'required_physical_gap_mm':.127,'moving_radius_mm':.225,'required_center_distance_mm':.352,'geometry':g})
 return m.check(Point(xy),vv,True)
if __name__=='__main__':
 for xy in [SOURCE,TARGET]:
  r=viac(xy);print(xy,[(x['object'],round(x['extra_clearance_mm'],7))for x in r[:3]]);assert r[0]['extra_clearance_mm']>=m.ERROR
 for r in repairs:
  for xy in [SOURCE,TARGET]:assert LineString(r['points']).distance(Point(xy))-(r['width']/2+.225+.127)>=m.ERROR,(r,xy)
 print('PASS joint portal+repair clearance including both planned SBUS vias')
