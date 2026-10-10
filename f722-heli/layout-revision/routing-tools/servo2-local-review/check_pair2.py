exec(open('ordinary-routing/servo2-local-review/review_local.py').read().split('for xy in ')[0])
from shapely.ops import nearest_points
p0points=[[10.7,10.7],[11.01,11.01],[11.01,12.49274],[11.26142,12.74416],[12.79217,12.74416],[13.21354,12.32279],[13.21354,12.2144]]
p1points=[[10.16087,11.17593],[10.244,11.17593],[10.69,11.62193],[10.69,12.545],[11.148,13.003],[12.9,13.003],[13.035,12.868],[13.45,12.868],[13.45,11.8875]]
g0=LineString(p0points).buffer(.0635,resolution=256).union(Point(10.7,10.7).buffer(.225,resolution=256))
g1=LineString(p1points).buffer(.0635,resolution=256).union(Point(10.16087,11.17593).buffer(.225,resolution=256))
for label,g in [('P0',g0),('P1',g1)]:
 print(label,'closest',json.dumps(sorted([brief(o,l,g.distance(poly)) for o,l,poly in local if l=='F.Cu' and o['net']!='SERVO2_MCU'],key=lambda v:v['gap'])[:4]))
print('PAIR',g0.difference(cut).distance(g1.difference(cut)))
vp=Point(10.7,10.7).buffer(.225,resolution=256);vd=Point(10.7,10.7).buffer(.1,resolution=256)
print('VIA_COPPER',json.dumps(sorted([brief(o,l,vp.distance(poly)) for o,l,poly in local if l not in ['In1.Cu','In4.Cu'] and o['net']!='SERVO2_MCU'],key=lambda v:v['gap'])[:5]))
print('VIA_MASK',json.dumps(sorted([brief(o,l,vd.distance(poly)) for o,l,poly in masks],key=lambda v:v['gap'])[:5]))
print('VIA_DRILL',json.dumps(sorted([brief(o,'drill',vd.distance(poly)) for o,poly in drills],key=lambda v:v['gap'])[:5]))
for z in n['zones']:
 if z.get('rule') and z.get('forbid',{}).get('vias') and vp.intersects(geom(z['outline'])):print('VIA_KEEP_OUT',z['uuid'],z['name'],z['layers'])
