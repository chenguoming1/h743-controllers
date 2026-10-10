exec(open('ordinary-routing/servo2-local-review/review_local.py').read().split('for xy in ')[0])
p0points=[[10.7,10.7],[11.01,11.01],[11.01,12.505],[11.25,12.745],[12.79133,12.745],[13.21354,12.32279],[13.21354,12.2144]]
p1points=[[10.16087,11.17593],[10.244,11.17593],[10.69,11.62193],[10.69,12.556],[11.138,13.004],[12.899,13.004],[13.035,12.868],[13.45,12.868],[13.45,11.8875]]
p0in3=[[10.16087,10.03687],[10.16087,10.3],[10.56087,10.7],[10.7,10.7]]
g0=LineString(p0points).buffer(.0635,resolution=256).union(Point(10.7,10.7).buffer(.225,resolution=256));g1=LineString(p1points).buffer(.0635,resolution=256).union(Point(10.16087,11.17593).buffer(.225,resolution=256));g3=LineString(p0in3).buffer(.0635,resolution=256)
for label,g,layer in [('P0',g0,'F.Cu'),('P1',g1,'F.Cu'),('P0_IN3',g3,'In3.Cu')]:
 print(label,'closest',json.dumps(sorted([brief(o,l,g.distance(poly)) for o,l,poly in local if l==layer and o['net']!='SERVO2_MCU'],key=lambda v:v['gap'])[:3]))
print('PAIR_F',g0.difference(cut).distance(g1.difference(cut)))
print('P0IN3_OLD_VIA',g3.distance(Point(10.16087,11.17593).buffer(.225,resolution=256)))
