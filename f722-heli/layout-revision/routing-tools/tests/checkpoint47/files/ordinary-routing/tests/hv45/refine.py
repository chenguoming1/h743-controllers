"""Reproduce the bounded local-centering decisions without changing the sealed proposal."""
import json,copy,pathlib,hashlib
import plan
m=plan.m;H=plan.HERE;r=json.load(open(H/'rpm-F-route.json'));final=json.load(open(H/'rpm-F-final-proposal.json'));obs=plan.trace_obs('RPM_HV','F.Cu','U16.1')[0];points=r['points'];history=[]
def sweep(index,choices):
 global points
 trials=[]
 for p in choices:
  pts=copy.deepcopy(points);pts[index]=p;z=m.check(m.LineString(pts),obs,True)
  trials.append({'index':index,'candidate_point':p,'points':pts,'minimum':z[0],'nearest':z[:5]})
 selected=max(trials,key=lambda t:t['minimum']['extra_clearance_mm']);points=selected['points'];history.append({'trials':trials,'selected_point':points[index]})
sweep(2,[[14.61,18.22],[14.62,18.22],[14.63,18.23],[14.63,18.24],[14.63,18.2],[14.64,18.24],[14.64,18.22]])
for index in [1,8]:
 base=points[index];sweep(index,[[round(base[0]+dx,6),round(base[1]+dy,6)]for dx,dy in [(0,0),(.01,0),(.02,0),(.03,0),(.04,0),(.06,0),(.08,0),(0,-.01),(0,-.02),(.03,-.02),(.06,-.02)]])
sweep(5,[points[5],[14.89,16.02],[14.89,16.0],[14.89,15.99],[14.87,16.0]])
sweep(1,[points[1],[13.77,18.78],[13.77,18.8],[13.77,18.82],[13.77,18.84]])
assert points==final['points'];checks=m.check(m.LineString(points),obs,True);assert checks[0]==final['minimum']
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
r={'schema':'f722-HV-bounded-local-centering/v1','source_board_sha256':m.EXPECTED,'source_native_sha256':sha(m.SOURCE),'raw_proposal_sha256':sha(H/'rpm-F-route.json'),'final_proposal_sha256':sha(H/'rpm-F-final-proposal.json'),'script_sha256':sha(__file__),'initial_points':r['points'],'final_points':points,'sweeps':history,'final_exact_minimum':checks[0],'all_native_rules_unchanged':True,'limit':'Each sweep moves one existing route vertex only. No foreign geometry, pad, source copper, width or clearance changes. Extra CAD clearance is not manufacturing margin.'}
(H/'refinement-history.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS reproduced final points and exact nearest-distance record')
