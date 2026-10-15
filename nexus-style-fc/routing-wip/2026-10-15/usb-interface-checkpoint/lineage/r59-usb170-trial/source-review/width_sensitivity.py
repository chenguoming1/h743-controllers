"""Bounded analytical width variants; writes separate proposed geometry only, never a board."""
from static_clearance import *
import copy
T=json.loads((D/'trunk-proposal.json').read_text());base=json.loads((D/'complete-transaction.json').read_text());W0=.15;G=.127;TOL=.000002
source_by_id={o['uuid']:o for o in tracks+vias};deleted=set(base['delete_uuids'])
fixed=[o for o in tracks+vias if o['uuid'] not in deleted and o['net'] not in ['USB_DP','USB_DM']]+pads
other=[o for o in base['add_primitives'] if o['group']!='trunk']+[source_by_id[u] for u in base['preserve_bridge_uuids']+base['reuse_via_uuids']]

def offset(p,o):
 q=copy.deepcopy(p)
 if p['kind']=='segment':
  a=np.array(p['start']);b=np.array(p['end']);u=(b-a)/np.linalg.norm(b-a);n=np.array([-u[1],u[0]]);q['start']=(a+o*n).tolist();q['end']=(b+o*n).tolist();q['length_mm']=math.dist(a,b)
 else:
  sign=1 if p['sweep_radians']>0 else -1;r=p['radius_mm']-sign*o;q['radius_mm']=r;q['length_mm']=r*abs(p['sweep_radians'])
  for k,a in [('start',p['start_radians']),('mid',p['start_radians']+p['sweep_radians']/2),('end',p['start_radians']+p['sweep_radians'])]:q[k]=[p['center'][0]+r*math.cos(a),p['center'][1]+r*math.sin(a)]
 return q

def chords(o):
 if o['kind']=='segment':return [(o['start'],o['end'])],0
 n=math.ceil(abs(o['sweep_radians'])/(2*math.acos(1-TOL/o['radius_mm'])));aa=np.linspace(o['start_radians'],o['start_radians']+o['sweep_radians'],n+1);pp=np.array(o['center'])+o['radius_mm']*np.column_stack((np.cos(aa),np.sin(aa)))
 return list(zip(pp[:-1],pp[1:])),o['radius_mm']*(1-math.cos(abs(o['sweep_radians'])/n/2))
def polyseg(poly,a,b):
 if MPath(np.array(poly)).contains_points(np.array([a,b]),radius=1e-10).any():return 0
 return min(seg_seg(p,q,a,b) for p,q in zip(poly,poly[1:]+poly[:1]))
def segobj(a,b,width,o):
 if o['kind']=='segment':return seg_seg(a,b,o['start'],o['end'])-(width+o['width'])/2
 if o['kind']=='via':return point_seg(o['at'],a,b)[0]-(width+o['diameter'])/2
 return seg_pad(a,b,o)-width/2

def twoplane(w,up,down,er,r):
 b=up+down;d=w+G
 return 120/math.sqrt(er)*(math.log(2*b/(math.pi*r)*math.sin(math.pi*up/b))-.5*math.log((math.cosh(math.pi*d/b)-math.cos(2*math.pi*up/b))/(math.cosh(math.pi*d/b)-1)))
summary=[]
for w in [.16,.17,.18]:
 centers=[copy.deepcopy(s['primitive']) for s in T['sections']];centers[0]['start'][1]=123.8;centers[-1]['end'][1]=111.05
 new=[];tapers=[]
 for net,sgn in [('USB_DP',-1),('USB_DM',1)]:
  for i,c in enumerate(centers):
   o=offset(c,sgn*(w+G)/2);o.update(net=net,width=w,layer='In3.Cu',id=net+'_wide_'+str(i));new.append(o)
  for name,cx,y0,y1 in [('south',109.65,124.,123.8),('north',110.9,110.85,111.05)]:
   # Inner taper edges stay vertical at +/-gap/2; outer edges expand by width delta.
   inner=cx+sgn*G/2;narrowouter=cx+sgn*(G/2+W0);wideouter=cx+sgn*(G/2+w)
   poly=[[inner,y0],[narrowouter,y0],[wideouter,y1],[inner,y1]]
   tapers.append(dict(kind='taper_copper_polygon',net=net,layer='In3.Cu',id=net+'_'+name+'_taper',vertices_mm=poly,start_port=[cx+sgn*(G+W0)/2,y0],end_port=[cx+sgn*(G+w)/2,y1],start_width_mm=W0,end_width_mm=w,axial_length_mm=.2))
 # Every swept envelope of widened arcs is checked; fixed roundrect uses conservative rectangle.
 rows=[]
 for p in new:
  ch,err=chords(p)
  for q in fixed+other:
   if q['net']==p['net']:continue
   if q['kind']=='segment' and q['layer']!='In3.Cu':continue
   if q['kind']=='pad' and 'In3.Cu' not in q['layers'] and '*.Cu' not in q['layers']:continue
   req=.2 if q.get('type')=='np_thru_hole' else .127
   g=min(segobj(a,b,w,q) for a,b in ch);rows.append(dict(id=p['id'],other=q.get('id',q.get('uuid')),net=q['net'],gap_mm=g,lower_bound_mm=g-err,required_mm=req))
 for p in tapers:
  poly=p['vertices_mm']
  for q in fixed+other:
   if q['net']==p['net']:continue
   if q['kind']=='segment':
    if q['layer']!='In3.Cu':continue
    g=polyseg(poly,q['start'],q['end'])-q['width']/2
   elif q['kind']=='via':g=polyseg(poly,q['at'],q['at'])-q['diameter']/2
   elif q['kind']=='pad':
    if 'In3.Cu' not in q['layers'] and '*.Cu' not in q['layers']:continue
    g=min(seg_pad(a,b,q) for a,b in zip(poly,poly[1:]+poly[:1]))
    if MPath(np.array(poly)).contains_point(q['at']):g=0
   else:continue
   req=.2 if q.get('type')=='np_thru_hole' else .127;rows.append(dict(id=p['id'],other=q.get('id',q.get('uuid')),net=q['net'],gap_mm=g,lower_bound_mm=g,required_mm=req))
 rows.sort(key=lambda r:r['lower_bound_mm']-r['required_mm']);fails=[r for r in rows if r['lower_bound_mm']<r['required_mm']-1e-8]
 vals={}
 for name,up,down in [('In2_In4',.1608,.5576),('In1_In4',.726,.5576)]:
  xx=[twoplane(w,up,down,er,r) for er in [4.16,4.6] for r in [w/4,(w+.0152)/4]];vals[name]=dict(sensitivity_proxy_range_ohm=[min(xx),max(xx)],representative_proxy_ohm=twoplane(w,up,down,4.38,(w+.0152)/4))
 v=dict(source_sha256=H,baseline_transaction_sha256=hashlib.sha256((D/'complete-transaction.json').read_bytes()).hexdigest(),status='SEPARATE_READ_ONLY_WIDTH_SENSITIVITY_NOT_ADOPTED',width_mm=w,gap_mm=G,envelope_mm=2*w+G,replace_baseline_trunk_only=new,taper_shapes=tapers,minimum_screened_margins=rows[:15],failures=fails,minimum_inside_copper_bend_radius_mm=.25-(2*w+G)/2,analytic_impedance_proxy=vals,connection_note='Taper polygons start at unchanged .150 handoff ports and overlap the new wider round-ended primitives at their wide ends. Their fixed inner edges retain exactly .127 separation. Tangent concentric offset arcs and parallel lines retain .127; full taper-to-opposite-lane same-section construction is analytic. Polygon conversion to real KiCad net copper and full native checks remain unperformed.',qualifications=['No PCB changed, no complete alternate native transaction applied. These separate variants do not supersede the sealed .150 transaction.','Two .200 mm axial taper regions per rail fit the existing straight terminal portions. The taper length is a construction coordinate, not a route-length cap.','The taper is an explicit copper trapezoid, not a silently widened constant-width track. Executable KiCad realization and full-port/native validation remain pending.','Clearance checks include retained foreign source plus all unchanged proposed ports/MCU/donors. No plane-refill changes are simulated.','Analytic sensitivity range is not an error bound or fabricated impedance acceptance.','Wider copper reduces remote-reference impedance but does not remove reference variation and tightens inside bend curvature.'])
 (D/f'width-{int(w*1000):03d}-variant.json').write_text(json.dumps(v,indent=2)+'\n');summary.append(dict(width_mm=w,failures=len(fails),minimum_margin=rows[0],minimum_inside_copper_bend_radius_mm=v['minimum_inside_copper_bend_radius_mm'],impedance=vals))
(D/'width-sensitivity-summary.json').write_text(json.dumps(dict(source_sha256=H,variants=summary,disposition='All remain separate conditional sensitivity cases; no variant selected as electrically qualified.'),indent=2)+'\n')
print(json.dumps(summary,indent=2))
