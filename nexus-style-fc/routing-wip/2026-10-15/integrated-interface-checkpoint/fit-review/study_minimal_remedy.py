"""Read-only conditional slot-length remedy; pure function reuse after script inspection."""
from pathlib import Path
import ast,hashlib,json,math,sys
from math import sqrt
ROOT=Path('/workspace/scratch/8a35c1f26232');OUT=Path(__file__).parent;P=ROOT/'nexus-recovery-20261015/mechanical-integration/main-left-vias-06';P=Path(sys.argv[1]) if len(sys.argv)>1 else P;PCB=P/'hardware/nexus-style-fc.kicad_pcb'
sys.path.insert(0,str(P/'tools'));import sexpr as s
text=PCB.read_text();h=hashlib.sha256(text.encode()).hexdigest();assert h in {'ccb4bcac2adc3baffce2fcc5f2c891fe91b17384b1ba0064506ade2df7338d8f','1d40a35cf373bef251f8032001766016f09500b007f22ff27ccb6578b0c4e263','ccd8865f6785fd1cdec0214a08fe409faed4d47bb01e8474f09264ee36acab99'};b=s.parse(text)
source=ROOT/'nexus-recovery-20261015/header-fit-review-readonly/audit_existing_copper.py'
tree=ast.parse(source.read_text());only=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]);ns={'s':s,'math':math};exec(compile(only,str(source),'exec'),ns)
vals,xy,st,segbox,pbox=(ns[k] for k in ['vals','xy','st','segbox','pbox'])
def eff(L,W,t,r):q=max(0,t/2-(W/2-r));return L-2*r+2*sqrt(r*r-q*q)
def arcbox(a,m,e,box):
 # Analytic circular-arc distance to a rectangle, using all endpoint,
 # side-stationary, corner-stationary, and edge-intersection candidates.
 ax,ay=a;bx,by=m;cx,cy=e
 den=2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by));assert abs(den)>1e-15
 ux=((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/den
 uy=((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/den
 r=math.hypot(ax-ux,ay-uy);sa=math.atan2(ay-uy,ax-ux);ma=math.atan2(by-uy,bx-ux);ea=math.atan2(cy-uy,cx-ux);tau=2*math.pi
 ccw=(ma-sa)%tau<=(ea-sa)%tau+1e-10
 def on(a):return ((a-sa)%tau<=(ea-sa)%tau+1e-10) if ccw else ((sa-a)%tau<=(sa-ea)%tau+1e-10)
 angles=[sa,ea,0,math.pi/2,math.pi,3*math.pi/2]
 angles.extend(math.atan2(y-uy,x-ux) for x,y in ns['corners'](box))
 for x in [box[0],box[2]]:
  if abs(x-ux)<=r:
   d=math.acos(max(-1,min(1,(x-ux)/r)));angles.extend([d,-d])
 for y in [box[1],box[3]]:
  if abs(y-uy)<=r:
   d=math.asin(max(-1,min(1,(y-uy)/r)));angles.extend([d,math.pi-d])
 return min(pbox((ux+r*math.cos(a),uy+r*math.sin(a)),box) for a in angles if on(a))
cases={}
for L,W in [(10.,2.1),(10.04,2.1),(10.10,2.1),(10.10,2.2)]:
 cores=[(100+cx-L/2+.5,102.4-W/2+.5,100+cx+L/2-.5,102.4+W/2-.5) for cx in (5.6,16.8)]
 records=[]
 for item in s.find(b,'segment'):
  a,c=xy(item,'start'),xy(item,'end');w=float(vals(item,'width')[0]);gap=min(segbox(a,c,core)-.5-w/2 for core in cores)
  records.append({'kind':'segment','uuid':st(item,'uuid'),'net':st(item,'net'),'gap':gap})
 for item in s.find(b,'via'):
  a=xy(item,'at');w=float(vals(item,'size')[0]);gap=min(pbox(a,core)-.5-w/2 for core in cores)
  records.append({'kind':'via','uuid':st(item,'uuid'),'net':st(item,'net'),'gap':gap})
 for item in s.find(b,'arc'):
  a,m,e=xy(item,'start'),xy(item,'mid'),xy(item,'end');w=float(vals(item,'width')[0]);gap=min(arcbox(a,m,e,core)-.5-w/2 for core in cores)
  records.append({'kind':'arc','uuid':st(item,'uuid'),'net':st(item,'net'),'gap':gap})
 # Native J1 pad-to-rounded-slot gap: rectangle/core separation minus corner radius.
 j=next(fp for fp in s.find(b,'footprint') if any(s.text(p[1])=='Reference' and s.text(p[2])=='J1' for p in s.find(fp,'property')));pads=[]
 for p in s.find(j,'pad'):
  x,y=xy(p,'at');w,d=xy(p,'size');box=(100+x-w/2,100+y-d/2,100+x+w/2,100+y+d/2)
  gap=min(math.hypot(max(box[0]-c[2],c[0]-box[2],0),max(box[1]-c[3],c[1]-box[3],0))-.5 for c in cores)
  pads.append({'number':s.text(p[1]),'net':st(p,'net'),'at':[x,y],'gap':gap})
 play=eff(L-.2,W-.2,1.76,.6)-8.6-.4
 cases[str(L) if W==2.1 else f'{L}x{W}']={'length':L,'width':W,'adverse_remaining_total_x_budget_R0p6_pitch0p4':play,'half_window':play/2,'reserve_each_side_beyond_fixture_plusminus0p1':play/2-.1,'nominal_outer_rail':5.6-L/2,'nominal_centre_web':11.2-L,'plus0p2_length_outer_rail':5.6-(L+.2)/2,'plus0p2_length_centre_web':11.2-(L+.2),'nominal_front_rail':2.4-W/2,'plus0p2_width_front_rail':2.4-(W+.2)/2,'nominal_cutout_area':L*W-(4-math.pi)*.5*.5,'minimum_segment_gap':min(r['gap'] for r in records if r['kind']=='segment'),'minimum_arc_gap':min(r['gap'] for r in records if r['kind']=='arc'),'minimum_via_gap':min(r['gap'] for r in records if r['kind']=='via'),'below_0p3_records':[r for r in records if r['gap']<.3-1e-8],'main_contact_gaps':pads,'records':records}
old={r['uuid'][0]:r for r in cases['10.0']['records']};
for c in cases.values():
 c['reduced_existing_copper_gaps']=[dict(r,old_gap=old[r['uuid'][0]]['gap']) for r in c['records'] if r['gap']<old[r['uuid'][0]]['gap']-1e-8 and r['gap']<.4]
 del c['records']
result={'source_main':str(PCB),'source_main_sha256':h,'arithmetic_source':str(source),'arithmetic_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'method':'Straight-segment, analytic circular-arc and circular-via edge distances to exact nominal rounded rectangles; J1 rectangular pads. No native calls or source edits. Existing fills are not rescanned or regenerated.','segment_count':len(s.find(b,'segment')),'via_count':len(s.find(b,'via')),'arc_count':len(s.find(b,'arc')),'cases':cases,'theoretical_minimum_nominal_slot_length_for_plusminus0p1':10.+.2-cases['10.0']['adverse_remaining_total_x_budget_R0p6_pitch0p4'],'bounded_stack':['Slot length/width ±0.20 mm','Full finished tab envelope 8.4±0.20 mm','Child thickness 1.6±10%','Maximum finished slot radius 0.60 mm (requires explicit agreement)','Absolute two-pair pitch mismatch <=0.40 mm (illustrative, not guaranteed by public dimensional spec)','Fixture copper/outline common translation ±0.10 mm, measured about the actual feasible-window midpoint; no additional unallocated positional/bow/finish/tilt error'],'critical_limit':'These X results assume Y is centred; use full-radius-model-check.json for coupled X/Y limits. Widening L alone does not guarantee ±0.10 mm about the nominal CAD origin if slot/tab absolute positions or asymmetric pitch errors shift the feasible-window midpoint. Need datum/registration definition or per-assembly gauging; radius/pitch bounds need acceptance.'}
assert hashlib.sha256(PCB.read_bytes()).hexdigest()==h
(OUT/('minimal-remedy-study.json' if len(sys.argv)==1 else P.name+'-copper-width-study.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
