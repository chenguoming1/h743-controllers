import joint_hypothesis as j,copy,json,math
from shapely.geometry import Point,LineString
m=j.m;H=j.plan.HERE;raw=json.load(open(H/'complete-joint-proposal.json'));r=copy.deepcopy(raw);assert r['complete'];t=next(x for x in r['routes']if x['label']=='In3trunk');trials=[]
for p in [[17.97,8.94],[17.97,8.93],[17.97,8.92],[17.97,8.91],[17.98,8.92],[17.99,8.92]]:
 pts=copy.deepcopy(t['points']);pts[3]=p;rr=j.tracecheck('In3.Cu',pts);trials.append({'index':3,'point':p,'points':pts,'minimum':rr[0],'nearest':rr[:5]})
best=max(trials,key=lambda x:x['minimum']['extra_clearance_mm']);t['points']=best['points'];t['minimum']=best['minimum'];t['length']=LineString(t['points']).length;t['violations']=[];r['centering_trials']=trials;r['source_unchanged']=True
# Keep the already jointly checked CORE site fixed; no further supply changes.
assert t['minimum']['extra_clearance_mm']>=m.ERROR and r['COREvia']==[17.1,9.84]
(H/'complete-joint-refined.json').write_text(json.dumps(r,indent=2)+'\n');print('new minimum',t['minimum'],'selected point',best['point'])
