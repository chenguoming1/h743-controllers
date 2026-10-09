exec(open('ordinary-routing/servo2-local-review/review_local.py').read().split('for xy in ')[0])
p0points=[[10.7,10.7],[11.01,11.01],[11.01,12.49274],[11.26142,12.74416],[12.79217,12.74416],[13.21354,12.32279],[13.21354,12.2144]]
p1points=[[10.16087,11.17593],[10.244,11.17593],[10.69,11.62193],[10.69,12.532],[11.163,13.005],[12.9,13.005],[13.035,12.87],[13.45,12.87],[13.45,11.8875]]
print('P0',json.dumps(trace_check(p0points)));print('P1',json.dumps(trace_check(p1points)));print('NEWVIA',json.dumps(via_check([10.7,10.7])))
g0=LineString(p0points).buffer(.0635,resolution=128).union(Point(10.7,10.7).buffer(.225,resolution=128))
g1=LineString(p1points).buffer(.0635,resolution=128).union(Point(10.16087,11.17593).buffer(.225,resolution=128))
print('PAIR',g0.difference(cut).distance(g1.difference(cut)))
