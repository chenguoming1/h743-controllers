"""Read-only exact WRL triangle/slab and rounded-slot cross-section checks."""
from pathlib import Path
import re,json,math,hashlib
O=Path(__file__).parent;P=O.parent/'mechanical-integration/main-left-vias-06';F=P/'hardware/library/NexusFC.3dshapes/nexus-header-board-root-relief-candidate.wrl'
t=F.read_text();assert hashlib.sha256(t.encode()).hexdigest()=='e1f0da0372a9d95a13fcff612a7effc7f4033363e482d384f0d170019d3f5dbe'
stack=[];br={}
for i,c in enumerate(t):
 if c=='{':stack.append(i)
 elif c=='}':br[stack.pop()]=i
trans=[]
for m in re.finditer(r'DEF (TXFM_\d+) Transform \{',t):
 h=t[m.end():t.index('children',m.end())];tr=tuple(map(float,re.search(r'translation ([^\n]+)',h)[1].split()));assert tuple(map(float,re.search(r'rotation ([^\n]+)',h)[1].split()))==(0,0,1,0);assert tuple(map(float,re.search(r'\n  scale ([^\n]+)',h)[1].split()))==(1,1,1);trans.append((m.start(),br[m.end()-1],tr,m[1]))
def clip(poly,limit,greater):
 if not poly:return []
 out=[];old=poly[-1];oldin=(old[2]>=limit if greater else old[2]<=limit)
 for p in poly:
  inside=(p[2]>=limit if greater else p[2]<=limit)
  if inside!=oldin:
   q=(limit-old[2])/(p[2]-old[2]);out.append(tuple(old[i]+q*(p[i]-old[i]) for i in range(3)))
  if inside:out.append(p)
  old,oldin=p,inside
 return out
polys=[];meshes=0;faces=0
for m in re.finditer(r'DEF (SHAPE_\d+) Shape \{',t):
 body=t[m.end():br[m.end()-1]];ps=list(zip(*[iter(map(float,re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',re.search(r'point\s*\[([^]]+)\]',body)[1])))]*3));trs=[x for x in trans if x[0]<m.start()<x[1]];off=[sum(x[2][i] for x in trs) for i in range(3)];ps=[tuple((p[i]+off[i])*2.54 for i in range(3)) for p in ps];ps=[(22.4-p[0],2.4-p[2],p[1]) for p in ps];ix=[int(v) for v in re.findall(r'-?\d+',re.search(r'coordIndex\s*\[([^]]+)\]',body)[1])];face=[];meshes+=1
 for k in ix:
  if k!=-1:face.append(ps[k]);continue
  faces+=1;clipped=clip(clip(face,-1.6,True),-1e-5,False)
  if clipped:polys.append((m[1],clipped))
  face=[]
 assert not face
nominal=[]
for L,W in [(10,2.1),(10.1,2.1),(10.1,2.2)]:
 def clearance(p,cx):return .5-math.hypot(max(abs(p[0]-cx)-(L/2-.5),0),max(abs(p[1]-2.4)-(W/2-.5),0))
 bad=[];minimum=1e9
 for name,poly in polys:
  cands=[min(clearance(p,cx) for p in poly) for cx in [5.6,16.8]];gap=max(cands);minimum=min(minimum,gap)
  if gap < -1e-8:bad.append({'mesh':name,'gap':gap,'polygon':poly})
 nominal.append({'slot_length':L,'slot_width':W,'minimum_model_triangle_clearance_in_main_slab':minimum,'interfering_clipped_triangles':len(bad),'witnesses':bad[:5]})
def corner(L,W,T,t,r,pitch,dx,dy):
 qx=max(0,T/2+pitch/2+abs(dx)-(L/2-r));qy=max(0,t/2+abs(dy)-(W/2-r));return r-math.hypot(qx,qy)
def ymax(L,W,T,t,r,pitch,dx):
 qx=max(0,T/2+pitch/2+abs(dx)-(L/2-r))
 if qx>r:return None
 return W/2-r+math.sqrt(r*r-qx*qx)-t/2
coupled=[]
for L,W,r,pitch,dx,dy in [(9.9,1.9,.6,.4,.1,0),(9.9,1.9,.6,.4,.1,.01),(9.9,1.9,.6,.4,.1,.02),(9.9,1.9,.6,.4,.1,.05),(9.9,1.9,.6,.4,.05,.03),(9.9,1.9,.55,.4,.1,.03),(9.9,1.9,.5,.4,.1,.04),(9.9,1.9,.6,.2,.1,.05),(10.1,1.9,.6,.4,.1,.05),(9.9,2.0,.6,.4,.1,0),(9.9,2.0,.6,.4,.1,.05),(9.9,2.0,.6,.4,.1,.065435605732),(9.9,2.0,.6,.4,.1,.07)]:
 coupled.append({'finished_slot_length':L,'width':W,'tab_width':8.6,'thickness':1.76,'radius':r,'pitch_mismatch':pitch,'common_x_half_window':dx,'common_y_half_window':dy,'minimum_corner_radial_gap':corner(L,W,8.6,1.76,r,pitch,dx,dy),'maximum_y_half_window_at_this_x':ymax(L,W,8.6,1.76,r,pitch,dx)})
# Required nominal L for a rectangular +/-x,+/-y positioning window at stated worst sizes/radius/pitch.
required=[]
for dy in [0,.01,.025,.03,.04,.05,.07]:
 r=.6;qy=max(0,.88+dy-(.95-r));extra=math.sqrt(max(0,r*r-qy*qy));Lmin=8.6+.4+2*.1+2*r-2*extra
 required.append({'x_half_window':.1,'y_half_window':dy,'minimum_nominal_L_with_minus0p2_tolerance':Lmin+.2})
res={'source_model':str(F),'model_sha256':hashlib.sha256(t.encode()).hexdigest(),'nominal_scope':'All exported model mesh faces clipped to the open interior of the nominal main slab Z=-1.6 to -0.00001; every clipped polygon must be wholly contained in one convex true-R0.5 rounded slot. Main outer material is conservatively treated as present everywhere outside the slots. Coplanar seating at Z=0 is intentional contact, not penetration.','mesh_count':meshes,'face_count':faces,'clipped_face_count':len(polys),'nominal_actual_mesh_checks':nominal,'coupled_corner_formula':'qx=max(0,T/2+P/2+abs(dx)-(L/2-r)); qy=max(0,t/2+abs(dy)-(W/2-r)); no interference iff qx^2+qy^2<=r^2','coupled_scope':'Rigid perpendicular tabs, symmetric split of pair-pitch mismatch about actual feasible midpoint; no additional absolute datum/bow/finish errors. Sized worst-case volumes are analytic variants, not measured manufactured parts.','coupled_cases':coupled,'required_slot_lengths_for_rectangular_fixture_windows':required,'conclusion':'10.10x2.10 nominal supports +/-0.10 x only with tightly bounded transverse offset (R0.60/pitch0.40 adverse stack, at most +/-0.0154356 y). The bounded 10.10x2.20 alternative supports +/-0.10 x and +/-0.05 y with 0.0139966 radial reserve, but its exact-source copper screen independently finds three DSM_DATA violations at 0.2865 mm. Independent x/y free-play totals cannot be combined. Neither option self-registers contacts; full tolerance acceptance and a demonstrated alignment/holding method remain necessary.'}
assert hashlib.sha256(F.read_bytes()).hexdigest()=='e1f0da0372a9d95a13fcff612a7effc7f4033363e482d384f0d170019d3f5dbe'
(O/'full-radius-model-check.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res,indent=2))
