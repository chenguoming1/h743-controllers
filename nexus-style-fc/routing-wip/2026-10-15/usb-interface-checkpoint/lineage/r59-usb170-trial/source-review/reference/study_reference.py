"""Read-only source parser and finite sampled geometry. Writes reports only to reference/. No native KiCad, board/fill/route writes, solver, impedance calculation."""
import sys,copy
sys.path.insert(0,'/workspace/shared/nexus-usb-stack-review/r57-inner-pair')
from static_clearance import *
R=D/'reference'
proposal=json.loads((D/'trunk-proposal.json').read_text())
prims=[copy.deepcopy(s['primitive']) for s in proposal['sections']]
assert prims[-1]['kind']=='segment';prims[-1]['end'][1]=110.85;prims[-1]['length_mm']=math.dist(prims[-1]['start'],prims[-1]['end'])
E=.427; offsets=np.array([-.2135,-.1385,-.0635,0,.0635,.1385,.2135]);STEP=.001
centers=[];normals=[];weights=[];svalues=[];sections=[];cursor=0
for i,p in enumerate(prims):
 n=max(1,math.ceil(p['length_mm']/STEP)); t=(np.arange(n)+.5)/n
 if p['kind']=='segment':
  a=np.array(p['start']);u=np.array(p['end'])-a;u=u/np.linalg.norm(u)
  pts=a+t[:,None]*(np.array(p['end'])-a);ns=np.tile([-u[1],u[0]],(n,1))
 else:
  a=p['start_radians']+t*p['sweep_radians'];rad=np.column_stack((np.cos(a),np.sin(a)));sgn=np.sign(p['sweep_radians'])
  pts=np.array(p['center'])+p['radius_mm']*rad;ns=-sgn*rad
 centers.extend(pts);normals.extend(ns);weights.extend([p['length_mm']/n]*n);svalues.extend(cursor+t*p['length_mm']);sections.extend([i]*n);cursor+=p['length_mm']
P=np.array(centers);N=np.array(normals);W=np.array(weights);SV=np.array(svalues);SE=np.array(sections);Q=P[:,None,:]+N[:,None,:]*offsets[None,:,None];A=Q[:,0];B=Q[:,-1]
def pseg(P,a,b):
 a=np.array(a);b=np.array(b);ab=b-a
 if ab.ndim==1:
  den=np.sum(ab*ab); t=np.clip(np.sum((P-a)*ab,axis=-1)/den,0,1) if den else np.zeros(P.shape[:-1])
 else:
  den=np.sum(ab*ab,axis=-1);t=np.clip(np.sum((P-a)*ab,axis=-1)/np.where(den,den,1),0,1)
 return np.linalg.norm(P-(a+t[...,None]*ab),axis=-1)
def crossing_distance(A,B,c,d):
 c=np.array(c);d=np.array(d)
 def cross2(u,v):return u[...,0]*v[...,1]-u[...,1]*v[...,0]
 x1=cross2(B-A,c-A);x2=cross2(B-A,d-A);x3=cross2(d-c,A-c);x4=cross2(d-c,B-c)
 bounds=(np.maximum(np.minimum(A,B),np.minimum(c,d))<=np.minimum(np.maximum(A,B),np.maximum(c,d))+1e-12).all(axis=1)
 crossing=(x1*x2<=0)&(x3*x4<=0)&bounds
 out=np.minimum.reduce([pseg(A,c,d),pseg(B,c,d),pseg(c,A,B),pseg(d,A,B)])
 return np.where(crossing,0,out)
def amount(mask):return float(W[mask].sum())
def intervals(mask):
 ind=np.flatnonzero(mask);out=[]
 if not len(ind):return out
 chunks=np.split(ind,np.flatnonzero(np.diff(ind)>1)+1)
 for c in chunks:
  a,b=c[0],c[-1];out.append(dict(s_start_mm=float(SV[a]-W[a]/2),s_end_mm=float(SV[b]+W[b]/2),projected_centerline_length_mm=amount(np.isin(np.arange(len(W)),c)),first_sample_mm=P[a].tolist(),last_sample_mm=P[b].tolist(),sections=sorted(set(map(int,SE[c])))))
 return out
membership={};mpaths={l:[MPath(np.array(p)) for p in pp] for l,pp in fills.items()}
for l in ['In1.Cu','In2.Cu','In4.Cu']:
 data=np.zeros(Q.shape[:2],dtype=bool);fc=[]
 for i,poly in enumerate(mpaths[l]):
  m=poly.contains_points(Q.reshape((-1,2)),radius=1e-10).reshape(Q.shape[:2]);data|=m
  if m.any():fc.append(dict(source_fill=fill_ids[l][i],center_covered_mm=amount(m[:,3]),any_seven_line_covered_mm=amount(m.any(axis=1)),all_seven_line_covered_mm=amount(m.all(axis=1)),center_intervals=intervals(m[:,3])))
 membership[l]=data
 (R/(l+'-fill-components.json')).write_text(json.dumps(fc,indent=2)+'\n')
coverage={l:dict(center_uncovered_mm=amount(~m[:,3]),any_seven_line_uncovered_mm=amount(~m.all(axis=1)),center_uncovered_intervals=intervals(~m[:,3]),any_seven_line_uncovered_intervals=intervals(~m.all(axis=1))) for l,m in membership.items()}
m2=membership['In2.Cu'];m1=membership['In1.Cu'];m4=membership['In4.Cu']
cond=dict(in2_absent_center_mm=amount(~m2[:,3]),in2_absent_center_with_in1_mm=amount(~m2[:,3]&m1[:,3]),in2_absent_center_with_in4_mm=amount(~m2[:,3]&m4[:,3]),in2_absent_center_with_both_in1_in4_mm=amount(~m2[:,3]&m1[:,3]&m4[:,3]),in2_absent_center_with_neither_mm=amount(~m2[:,3]&~m1[:,3]&~m4[:,3]),in2_any_line_absent_but_in1_covers_all_lines_mm=amount(~m2.all(axis=1)&m1.all(axis=1)),in2_any_line_absent_but_in4_covers_all_lines_mm=amount(~m2.all(axis=1)&m4.all(axis=1)),in2_any_line_absent_but_remote_union_covers_all_lines_mm=amount(~m2.all(axis=1)&(m1|m4).all(axis=1)),in2_absent_center_and_in1_absent_intervals=intervals(~m2[:,3]&~m1[:,3]))
objects=[];masks={};netmasks={};clrmasks={}
for t in tracks:
 if t['layer']!='In2.Cu' or t['net']=='GND':continue
 dist=crossing_distance(A,B,t['start'],t['end'])-t['width']/2
 if dist.min()>.75:continue
 direct=dist<=0; clearance=dist<.2
 o=dict(source=t,minimum_edge_distance_to_envelope_mm=float(dist.min()),projected_copper_overlap_mm=amount(direct),projected_0200_zone_clearance_overlap_mm=amount(clearance),copper_overlap_intervals=intervals(direct),clearance_overlap_intervals=intervals(clearance),saved_in2_center_absence_near_this_0200_clearance_mm=amount(clearance&~m2[:,3]),saved_in2_any_line_absence_near_this_0200_clearance_mm=amount(clearance&~m2.all(axis=1)))
 objects.append(o);masks[t['uuid']]=direct
 netmasks[t['net']]=netmasks.get(t['net'],np.zeros(len(W),bool))|direct
 clrmasks[t['net']]=clrmasks.get(t['net'],np.zeros(len(W),bool))|clearance
viaobjects=[]
for v in vias:
 if v['net']=='GND':continue
 dist=pseg(np.array(v['at']),A,B)-v['diameter']/2
 if dist.min()>.75:continue
 direct=dist<=0;clearance=dist<.2
 viaobjects.append(dict(source=v,minimum_edge_distance_to_envelope_mm=float(dist.min()),projected_copper_overlap_mm=amount(direct),projected_0200_zone_clearance_overlap_mm=amount(clearance),copper_overlap_intervals=intervals(direct),clearance_overlap_intervals=intervals(clearance)))
net_summary=[dict(net=n,union_projected_copper_overlap_mm=amount(netmasks[n]),union_projected_0200_clearance_overlap_mm=amount(clrmasks[n]),copper_intervals=intervals(netmasks[n]),clearance_intervals=intervals(clrmasks[n])) for n in sorted(netmasks)]
all_direct=np.logical_or.reduce(list(netmasks.values()));all_clearance=np.logical_or.reduce(list(clrmasks.values()))
(R/'reference-analysis.json').write_text(json.dumps(dict(source=str(S),source_sha256=H,trunk_proposal_sha256=hashlib.sha256((D/'trunk-proposal.json').read_bytes()).hexdigest(),trimmed_end_y_mm=110.85,trunk_center_length_mm=cursor,width_mm=.15,gap_mm=.127,envelope_mm=E,sample_max_step_mm=STEP,sample_count=len(W),coverage=coverage,remote_reference_conditions=cond,non_ground_in2_tracks=objects,non_ground_through_vias=viaobjects,by_net=net_summary,track_copper_union_mm=amount(all_direct),track_clearance_union_mm=amount(all_clearance),unexplained_saved_center_absence_outside_track_0200_clearance_intervals=intervals(~m2[:,3]&~all_clearance),unexplained_saved_any_line_absence_outside_track_0200_clearance_intervals=intervals(~m2.all(axis=1)&~all_clearance),limits=['Saved-fill point membership only, not finite connectivity or impedance. All source fills retained.','Numerical projected intervals are midpoint estimates at <=.001 mm arclength spacing; transition error up to one sample per boundary.','Seven projection rays are the envelope edges, lane centers, inner edges and pair center. Complete continuous fill coverage is not proven.','Non-ground copper projection is continuous across each sampled .427 mm normal section, including inter-pair gap.','0.200 mm clearance model follows source In2 GND zone clearance; it is explanatory geometry only, not a refill or DRC.','Foreign via lands/through-holes persist on In2 regardless of external route changes.']),indent=2)+'\n')
np.savez_compressed(R/'numerical-projection.npz',centers=P,normals=N,weights=W,svalues=SV,sections=SE,offsets=offsets,in1=m1,in2=m2,in4=m4)
assert hashlib.sha256(S.read_bytes()).hexdigest()==H
print('length',cursor);print('coverage', {l:{k:v for k,v in r.items() if k.endswith('_mm')} for l,r in coverage.items()});print('conditional',cond)
for n in net_summary:
 if n['union_projected_0200_clearance_overlap_mm']:print('NET',n['net'],n['union_projected_copper_overlap_mm'],n['union_projected_0200_clearance_overlap_mm'])
for v in viaobjects:
 if v['projected_0200_zone_clearance_overlap_mm']:print('VIA',v)
