"""Cache the three disconnected current C graphs and annotate exact source/peer cuts."""
import hashlib,json,signal,time
from pathlib import Path
from shapely.geometry import LineString
from shapely.ops import nearest_points
from shapely.strtree import STRtree
import composite_native11_C_TX_WP as _c_source
import composite_native11_complete_BOOT as g
import graph_native11 as gg
H=Path(__file__).resolve().parent;s=g.s;START=time.monotonic()
OUT=H/'C-remaining-exact-cuts11.json'
out=dict(schema='f722-current-C-remaining-cuts11/v2',source=g.binding(),cases=[],copper_only=True,saved_plane_reference_filter_applied=False,native_candidate=False,
         complete_ordinary_BOOT_held=True,corrected_foreign_channel_identity=True,
         pending_B_divider_explicit=True,complete_TX_WP_held=True)
def save():
 out['seconds']=time.monotonic()-START;out['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();OUT.write_text(json.dumps(out,indent=2)+'\n')
def alarm(sig,frame):out['timeout']=True;save();print('TERMINAL_TIMEOUT',flush=True);raise SystemExit(0)
signal.signal(signal.SIGALRM,alarm);signal.alarm(40)
def reachable(gr,initial):
 seen=set(initial);todo=list(initial)
 while todo:
  for b,w,e in gr['adj'][todo.pop()]:
   if b not in seen:seen.add(b);todo.append(b)
 return seen
jobs=[dict(branch=g.BRANCHES[0],target='J11.1'),dict(net='PORT_C_RX_MCU',start='U1.28',target='R34.2'),dict(net='PORT_C_TX_MCU',start='U1.29',target='R35.2')]
for job in jobs:
 if 'branch'in job:
  b=job['branch'];net,objects=g.branch_objects(b,g.BASE);start=b['points'][-1];sl=('F.Cu',);name=b['name']
 else:
  net=job['net'];objects=g.BASE;p=g.one_pad(job['start']);start=p['xy'];sl=tuple(p['copper']);name=net
 target=g.one_pad(job['target']);gr=gg.build(net,objects);plan=gg.connect(gr,start,target['xy'],sl,tuple(target['copper']))
 row=dict(name=name,job=job,graph_result=plan,closest_cuts=[]);out['cases'].append(row)
 if plan['connected']:save();continue
 aa=reachable(gr,plan['start_nodes']);bb=reachable(gr,plan['end_nodes'])
 row['source_reachable_nodes']=sorted(aa);row['target_reachable_nodes']=sorted(bb)
 row['cached_components']=[dict(id=i,layer=gr['nodes'][i][0],area_mm2=gr['nodes'][i][1].area,bounds=list(gr['nodes'][i][1].bounds),
                                wkb_hex=gr['nodes'][i][1].wkb_hex,side='source'if i in aa else'target',
                                legal_new_transition_area_mm2=gr['eligible'][i].area if i in gr['eligible']else 0)
                           for i in sorted(aa|bb)]
 for layer in ['F.Cu','B.Cu','In2.Cu','In3.Cu']:
  left=[i for i in aa if gr['nodes'][i][0]==layer];right=[i for i in bb if gr['nodes'][i][0]==layer]
  if not left or not right:continue
  tree=STRtree([gr['nodes'][i][1]for i in right]);best=None
  for a in left:
   p=gr['nodes'][a][1];b=right[int(tree.nearest(p))];q=gr['nodes'][b][1];d=p.distance(q)
   if best is None or d<best[0]:best=(d,a,b)
  d,a,b=best;x,y=nearest_points(gr['nodes'][a][1],gr['nodes'][b][1]);pts=[list(x.coords[0]),list(y.coords[0])]
  s.HALF=.0635;checks=s.check(LineString(pts),gr['obstacles'][layer],True)
  blockers=[]
  for ck in checks:
   if ck['pass_with_polygon_error']:continue
   ck=dict(ck);ck['provenance']='retained accepted native11 copper'if ck['uuid']in g.by else'conditional peer geometry'
   blockers.append(ck)
  row['closest_cuts'].append(dict(layer=layer,source_node=a,target_node=b,gap_mm=d,witness=pts,blockers=blockers))
 save();print('CUT',name,[(z['layer'],z['gap_mm'],[(x['uuid'],x['provenance'])for x in z['blockers']])for z in row['closest_cuts']],flush=True)
save();print('TERMINAL',out['seconds'],flush=True)
