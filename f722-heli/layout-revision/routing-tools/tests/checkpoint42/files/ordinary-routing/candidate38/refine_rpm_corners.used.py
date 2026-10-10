#!/usr/bin/env python3
"""Bounded corner repair, then native-checked LOS simplification. No board edits."""
import importlib.util,json,pathlib,sys,copy
import numpy as np
import shapely
from shapely.geometry import LineString,Point,box
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('rpm_screen',HERE/'screen.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
s=q.s
ARR={l:np.array([o['geometry'] for o in obs],dtype=object) for l,obs in q.OBS.items()}
REQ={l:np.array([o['required_center_distance_mm'] for o in obs]) for l,obs in q.OBS.items()}
FULLARR=ARR.copy();FULLREQ=REQ.copy()
def margin(points,layer):
 g=LineString(points)
 if not s.OUTLINE.covers(g):return -999
 return float(np.min(shapely.distance(g,ARR[layer])-REQ[layer]))
def valid(points,layer):return margin(points,layer)>=s.ERROR
raw=q.raw['traces'];rawb=raw[0]['requested_corners_mm'];rawf=raw[1]['requested_corners_mm'];f=copy.deepcopy(rawf);repairs=[]
# Two disjoint existing path windows only. Endpoints remain fixed; no foreign geometry altered.
for name,lo,hi,which in [('SBUS_HV_clearance',16,23,'sb'),('R43_2_clearance',41,47,'r43')]:
 pts=rawf[lo:hi+1];start,end=pts[0],pts[-1];roi=box(min(x[0] for x in pts)-.001,min(x[1] for x in pts)-.001,max(x[0] for x in pts)+.001,max(x[1] for x in pts)+.001)
 mask=shapely.distance(roi,FULLARR['F.Cu']) <= FULLREQ['F.Cu']+.001
 ARR['F.Cu']=FULLARR['F.Cu'][mask];REQ['F.Cu']=FULLREQ['F.Cu'][mask]
 print('LOCAL',name,'obstacles',len(REQ['F.Cu']),flush=True)
 # First try every monotone-index shortcut of retained points within this window.
 alternatives=[]
 for a in range(len(pts)-1):
  for b in range(a+1,len(pts)):
   if b==a+1:continue
   c=pts[:a+1]+pts[b:]
   if valid(c,'F.Cu'):alternatives.append((LineString(c).length,c,{'type':'existing_corner_shortcut','kept_join_indices':[lo+a,lo+b]}))
 # Bounded repair inserts only one/two corners derived from existing window endpoints.
 for a in range(len(pts)-1):
  for b in range(a+1,len(pts)):
   pa,pb=pts[a],pts[b]
   candidates=list(s.paths2(pa,pb))
   # Local diagonal corners shifted by bounded 0.005-0.20 mm. 40 steps.
   for d in [i*.005 for i in range(1,41)]:
    for sign in [-1,1]:
     candidates += [[pa,[pa[0]+sign*d,pa[1]],[pb[0]+sign*d,pb[1]],pb],[pa,[pa[0],pa[1]+sign*d],[pb[0],pb[1]+sign*d],pb]]
   for cand in candidates:
    cand=[[round(float(x),5),round(float(y),5)] for x,y in cand];c=pts[:a]+cand+pts[b+1:]
    c=[p for i,p in enumerate(c) if i==0 or p!=c[i-1]]
    g=LineString(c)
    if roi.covers(g) and valid(c,'F.Cu'):alternatives.append((g.length,c,{'type':'bounded_existing_corner_replacement','replaced_raw_index_range':[lo+a,lo+b]}))
 if not alternatives:
  print('NO LOCAL REPAIR',name,flush=True);repairs.append({'name':name,'raw_index_window':[lo,hi],'passed':False});continue
 robust=[x for x in alternatives if margin(x[1],'F.Cu')>=.00015]
 if robust:alternatives=robust
 alternatives.sort(key=lambda x:(x[0],len(x[1])))
 best=alternatives[0]
 repairs.append({'name':name,'raw_index_window':[lo,hi],'raw_points_mm':pts,'revised_points_mm':best[1],'passed':True,'passed_alternatives':len(alternatives),'selection':best[2],'minimum_extra_mm':margin(best[1],'F.Cu'),'bounded_roi_mm':list(roi.bounds)})
 print('REPAIRED',name,'points',best[1],'min',repairs[-1]['minimum_extra_mm'],flush=True)
# Replace windows in reverse raw-index order.
for r in sorted([x for x in repairs if x['passed']],key=lambda x:x['raw_index_window'][0],reverse=True):
 lo,hi=r['raw_index_window'];f[lo:hi+1]=r['revised_points_mm']
report={'source_identity':q.ID,'refine_helper_sha256':q.sha(__file__),'scope':'Two fixed raw-path windows only; shortest exact-source-clearing replacement among monotone shortcuts, orthogonal/45-degree endpoint bends, and at most 0.20 mm displaced two-corner doglegs, all contained in original window bbox expanded 0.001 mm. No grid/maze search or foreign geometry edits.','repairs':repairs,'repaired_f_points_mm':f,'repaired_f_check':q.screen_trace(f,'F.Cu')}
(HERE/'corner-repair.json').write_text(json.dumps(report,indent=2)+'\n')
print('REPAIR STATUS',report['repaired_f_check']['minimum_extra_clearance_mm'],flush=True)
