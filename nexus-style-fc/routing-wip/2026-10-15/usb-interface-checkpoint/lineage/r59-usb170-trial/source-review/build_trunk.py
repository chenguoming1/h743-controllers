"""Read-only In3 full-width paired-trunk primitives, clearance and actual saved-fill projection."""
from static_clearance import *
W=.150;G=.127;E=2*W+G;OFF=(W+G)/2;TOL=.000002
PTS=[[109.65,124],[109.65,122.6],[109.8,122.1],[109.9,121.4],[110.5,120.8],[110.5,114.4],[110.75,114.15],[110.75,111.8],[110.9,111.65],[110.9,110.6]]
def fillets(points,R=.25):
 out=[];cursor=np.array(points[0],float)
 for i in range(1,len(points)-1):
  p=np.array(points[i]);u=p-np.array(points[i-1]);u=u/np.linalg.norm(u);v=np.array(points[i+1])-p;v=v/np.linalg.norm(v);theta=math.acos(float(np.clip(np.dot(u,v),-1,1)));sgn=1 if u[0]*v[1]-u[1]*v[0]>0 else -1;d=R*math.tan(theta/2)
  assert d<math.dist(p,points[i-1])/2 and d<math.dist(p,points[i+1])/2
  a=p-u*d;b=p+v*d;c=a+sgn*R*np.array([-u[1],u[0]])
  out.append(dict(kind='segment',start=cursor.tolist(),end=a.tolist(),length_mm=math.dist(cursor,a)))
  out.append(dict(kind='arc',center=c.tolist(),start=a.tolist(),end=b.tolist(),radius_mm=R,start_radians=math.atan2(a[1]-c[1],a[0]-c[0]),sweep_radians=sgn*theta,length_mm=R*theta));cursor=b
 out.append(dict(kind='segment',start=cursor.tolist(),end=points[-1],length_mm=math.dist(cursor,points[-1])))
 return out
def offset(p,o):
 q=dict(p)
 if p['kind']=='segment':
  a=np.array(p['start']);b=np.array(p['end']);u=(b-a)/np.linalg.norm(b-a);n=np.array([-u[1],u[0]]);q['start']=(a+o*n).tolist();q['end']=(b+o*n).tolist()
 else:
  sgn=1 if p['sweep_radians']>0 else -1;r=p['radius_mm']-sgn*o;q['radius_mm']=r;q['length_mm']=r*abs(p['sweep_radians']);q['start']=[p['center'][0]+r*math.cos(p['start_radians']),p['center'][1]+r*math.sin(p['start_radians'])];ang=p['start_radians']+p['sweep_radians'];q['end']=[p['center'][0]+r*math.cos(ang),p['center'][1]+r*math.sin(ang)]
 return q
def sample(p,step=.01):
 n=max(1,math.ceil(p['length_mm']/step));t=(np.arange(n)+.5)/n
 if p['kind']=='segment':return np.array(p['start'])+t[:,None]*(np.array(p['end'])-p['start'])
 a=p['start_radians']+t*p['sweep_radians'];return np.array(p['center'])+p['radius_mm']*np.column_stack((np.cos(a),np.sin(a)))
def chords(p):
 if p['kind']=='segment':return [(p['start'],p['end'])],0
 n=math.ceil(abs(p['sweep_radians'])/(2*math.acos(1-TOL/p['radius_mm'])));a=np.linspace(p['start_radians'],p['start_radians']+p['sweep_radians'],n+1);pts=np.array(p['center'])+p['radius_mm']*np.column_stack((np.cos(a),np.sin(a)))
 return list(zip(pts[:-1],pts[1:])),p['radius_mm']*(1-math.cos(abs(p['sweep_radians'])/n/2))
mpaths={l:[MPath(np.array(p)) for p in pp] for l,pp in fills.items()}
def refproj(p,l):
 oo=[-E/2,-OFF,-G/2,0,G/2,OFF,E/2];sets=[sample(offset(p,o)) for o in oo];N=len(sets[0]);masks=[];touch=[]
 for ss in sets:
  mm=np.zeros(len(ss),dtype=bool)
  for i,poly in enumerate(mpaths[l]):
   m=poly.contains_points(ss,radius=1e-10);mm|=m
   if m.any() and fill_ids[l][i] not in touch:touch.append(fill_ids[l][i])
  masks.append(mm)
 # Number of midpoint samples can vary slightly on offset arcs. For common-normal summary, resample all offsets using centerline parameter count.
 n=max(1,math.ceil(p['length_mm']/.01));t=(np.arange(n)+.5)/n;normal_sets=[]
 for o in oo:
  q=offset(p,o)
  if q['kind']=='segment':ss=np.array(q['start'])+t[:,None]*(np.array(q['end'])-q['start'])
  else:
   a=q['start_radians']+t*q['sweep_radians'];ss=np.array(q['center'])+q['radius_mm']*np.column_stack((np.cos(a),np.sin(a)))
  mm=np.zeros(n,dtype=bool)
  for poly in mpaths[l]:mm|=poly.contains_points(ss,radius=1e-10)
  normal_sets.append(mm)
 return dict(reference_layer=l,sample_spacing_centerline_mm=p['length_mm']/n,center_uncovered_mm=float((~normal_sets[3]).sum()*p['length_mm']/n),any_seven_line_uncovered_mm=float((~np.logical_and.reduce(normal_sets)).sum()*p['length_mm']/n),projected_saved_fill_ids=touch)
prim=fillets(PTS);res=[];minimum=(1e6,None)
for i,p in enumerate(prim):
 ch,err=chords(p);out=[]
 for t in foreign_tracks:
  if t['layer']!='In3.Cu':continue
  gap=min(seg_seg(a,b,t['start'],t['end']) for a,b in ch)-(E+t['width'])/2
  if gap<minimum[0]:minimum=(gap,t)
  if gap-err<.127:out.append(dict(gap_mm=gap,chord_error_mm=err,item=t))
 for v in foreign_vias:
  gap=min(point_seg(v['at'],a,b)[0] for a,b in ch)-(E+v['diameter'])/2
  if gap<minimum[0]:minimum=(gap,v)
  if gap-err<.127:out.append(dict(gap_mm=gap,chord_error_mm=err,item=v))
 for pad in pads:
  if 'In3.Cu' not in pad['layers'] and '*.Cu' not in pad['layers']:continue
  gap=min(seg_pad(a,b,pad) for a,b in ch)-E/2
  if gap<minimum[0]:minimum=(gap,pad)
  if gap-err<.2:out.append(dict(gap_mm=gap,chord_error_mm=err,item=pad))
 res.append(dict(index=i,primitive=p,obstructions=out,saved_reference_projection=[refproj(p,l) for l in ['In2.Cu','In4.Cu']]))
lanes=[]
for name,o in [('left',OFF),('right',-OFF)]:
 pp=[dict(offset(p,o),layer='In3.Cu',width_mm=W) for p in prim];lanes.append(dict(lane=name,points=[pp[0]['start'],pp[-1]['end']],primitives=pp,planar_length_mm=sum(p['length_mm'] for p in pp)))
obj=dict(source_path=str(S),source_sha256=H,status='GEOMETRY_SCREENED_TRUNK_ONLY_REFERENCE_AND_PORTS_PENDING',control_points_mm=PTS,fillet_radius_mm=.25,width_mm=W,edge_gap_mm=G,envelope_mm=E,minimum_retained_foreign_gap_mm=minimum[0],minimum_gap_object=minimum[1],sections=res,lanes=lanes,stack=stack,reference_summary={l:dict(center_uncovered_mm=sum(next(r for r in s['saved_reference_projection'] if r['reference_layer']==l)['center_uncovered_mm'] for s in res),any_seven_line_uncovered_mm=sum(next(r for r in s['saved_reference_projection'] if r['reference_layer']==l)['any_seven_line_uncovered_mm'] for s in res)) for l in ['In2.Cu','In4.Cu']},limits=['Every source non-USB track/via/pad is retained; only legacy USB copper is excluded. No board changes, native DRC/refill or solver.','This is only the main trunk. Complete J6/U7/MCU launch transactions and all new mutual checks are separate.','In2 mixed GND is the nearer adjacent copper (.1532 mm dielectric); In4 is .55 mm away. Both are quantified, neither inferred to be signal-free.','Saved-fill membership and unbroken sampled projection do not prove finite connected return, post-refill geometry or impedance.','No arbitrary length/skew cap, no neckdown, no part/placement/net changes.','A .150 mm internal pair is not claimed to be 90 ohms. Actual asymmetric stack, nearby copper, vias and laminate production data need qualification.'])
assert not any(x['obstructions'] for x in res)
assert hashlib.sha256(S.read_bytes()).hexdigest()==H
(D/'trunk-proposal.json').write_text(json.dumps(obj,indent=2)+'\n')
print('min',minimum[0],minimum[1]['net'],minimum[1]['uuid']);print('lengths',[(x['lane'],x['planar_length_mm'],x['points']) for x in lanes]);print('reference',obj['reference_summary'])
