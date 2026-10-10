"""Full-layer actual C obligations, followed by jointly guarded branch construction."""
import hashlib,json,signal,time
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely import unary_union
import composite_native11_C_TX_WP as g
import graph_native11 as gg
import route_native11 as rt
H=Path(__file__).resolve().parent;s=g.s;START=time.monotonic();DEADLINE=START+78
OUT=H/'U15-remaining-complete-branches11.json';objects=list(g.BASE)
out=dict(schema='f722-U15-remaining-complete-branches11/v1',source=g.binding(),initial_graphs=[],routes=[],vias=[],steps=[],actual_cut_checks=[],complete=False,native_candidate=False,selected=False,
         full_C_MCU_capacities_required_before_long_trunks=True,B_divider_still_pending=True,copper_process_only=True,reference_qualified=False)
def save():
 out['seconds']=time.monotonic()-START;out['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();OUT.write_text(json.dumps(out,indent=2)+'\n')
def stop(reason):out['terminal_reason']=reason;save();print('TERMINAL',reason,out['seconds'],flush=True);raise SystemExit(0)
def alarm(sig,frame):stop('Bounded construction deadline; partial paths remain unselected.')
signal.signal(signal.SIGALRM,alarm);signal.alarm(81)
jobs=[dict(branch=g.BRANCHES[i],target=key)for i,key in [(3,'R35.1'),(1,'R34.1'),(0,'J11.1')]]
def graph(job):
 if 'branch'in job:
  b=job['branch'];net,oo=g.branch_objects(b,objects);a=b['points'][-1];al=('F.Cu',)
 else:
  net=job['net'];oo=objects;p=g.one_pad(job['start']);a=p['xy'];al=tuple(p['copper'])
 p=g.one_pad(job['target']);gr=gg.build(net,oo);plan=gg.connect(gr,a,p['xy'],al,tuple(p['copper']))
 return net,oo,gr,plan
guards=[dict(net='PORT_C_RX_MCU',start='U1.28',target='R34.2'),dict(net='PORT_C_TX_MCU',start='U1.29',target='R35.2')]
for job in jobs+guards:
 net,oo,gr,plan=graph(job);label=job.get('branch',{}).get('name',job.get('net'))
 out['initial_graphs'].append(dict(name=label,target=job['target'],actual_bonded_pad=None if 'branch'not in job else('U15.1'if job['branch']['net']=='PORT_C_RX_EXT'else'U15.2'),prefix=None if 'branch'not in job else job['branch'],result=plan));save();print('GRAPH',label,plan['connected'],plan['additional_transition_count'],flush=True)
if not all(q['result']['connected']for q in out['initial_graphs']):stop('One or more actual C obligations are disconnected before any remaining long trunk is frozen.')
for index,job in enumerate(jobs):
 net,oo,gr,plan=graph(job);b=job['branch'];step=dict(name=b['name'],graph=plan,complete=False);out['steps'].append(step);save()
 if not plan['connected']:stop('An earlier complete branch closes a remaining actual protected branch; joint reconstruction must backtrack.')
 ve=[]
 for i,v in enumerate(plan['new_vias']):
  s.OBJECTS=oo+ve;s.HALF=.0635;cc=s.check(Point(v['xy']),s.obstacles(net,'B.Cu')[1],True)
  if not all(q['pass_with_polygon_error']for q in cc):step['via_failure']=cc;stop('Proposed C transitions are not mutually process-clear.')
  vv=dict(name=f'C-branch-{index}-via-{i}',net=b['net'],role=b['role'],xy=v['xy'],diameter_mm=.45,drill_mm=.20)
  q=g.via(net,vv['xy'],vv['name']);ve.append(q);out['vias'].append(vv)
  physical=g.via(vv['net'],vv['xy'],vv['name']);objects.append((dict(physical[0],role=vv['role']),physical[1],physical[2],physical[3]))
 for i,leg in enumerate(plan['legs']):
  if leg['start']==leg['end']:continue
  alias,local=g.branch_objects(b,objects);free,obs,vo=rt.domain(alias,leg['layer'],objects=local);comp=rt.component(free,leg['start'])
  pts=rt.route(comp,leg['start'],leg['end'],DEADLINE)
  if pts is None:step['unconstructed_leg']=leg;stop('Exact C path could not be constructed in the selected legal regions.')
  s.HALF=.0635;cc=s.check(LineString(pts),obs,True)
  if not all(q['pass_with_polygon_error']for q in cc):step['route_failure']=cc;stop('Exact C finite path check failed.')
  rr=dict(name=f'C-branch-{index}-route-{i}',net=b['net'],role=b['role'],layer=leg['layer'],width=.127,points=pts,length_mm=LineString(pts).length,nearest=cc[:4])
  out['routes'].append(rr);q=g.track(rr['net'],rr['layer'],pts,rr['name'],.127);objects.append((dict(q[0],role=rr['role']),q[1],q[2],q[3]));save();print('ROUTE',b['name'],rr['layer'],rr['length_mm'],flush=True)
 step['complete']=True
 # Explicit actual-pin cuts include both entire constructed branches and NC lands.
 out['actual_cut_checks']=[]
 for physical,key,nc in [('PORT_C_RX_EXT','U15.1','U15.10'),('PORT_C_TX_EXT','U15.2','U15.9')]:
  pin=s.geom(g.one_pad(key)['inside']['F.Cu']);up=[s.geom(g.one_pad(nc)['copper']['F.Cu'])];dn=[]
  prefixnames={r['name']:r for r in g.BRANCHES}
  for o,c,m,d in objects:
   if o['net']!=physical or'F.Cu'not in c or o['kind']=='pad':continue
   role=o.get('role')or prefixnames.get(o['uuid'],{}).get('role')
   if role=='upstream':up.append(c['F.Cu'])
   elif role=='downstream':dn.append(c['F.Cu'])
  a=unary_union(up).difference(pin);z=unary_union(dn).difference(pin);gap=a.distance(z)
  out['actual_cut_checks'].append(dict(actual_pad=key,gap_mm=gap,passed=gap>=.127+s.ERROR))
 if not all(q['passed']for q in out['actual_cut_checks']):stop('A complete path failed the actual bonded-pin cut.')
 save()
out['final_C_MCU_graphs']=[]
for job in guards:
 net,oo,gr,plan=graph(job);out['final_C_MCU_graphs'].append(dict(net=net,result=plan));save()
out['complete']=all(q['complete']for q in out['steps'])and all(q['result']['connected']for q in out['final_C_MCU_graphs'])
stop('All four protected C branches constructed with both MCU capacities preserved.'if out['complete']else'Protected paths exist but a remaining MCU capacity was lost; held for joint backtracking.')
