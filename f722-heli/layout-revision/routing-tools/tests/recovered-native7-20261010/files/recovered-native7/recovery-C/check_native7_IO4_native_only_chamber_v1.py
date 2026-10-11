"""One native7-only IO4 chamber query after complete old return/stitch release."""
import argparse,json,signal,time
from pathlib import Path
from native7_IO4_native_only_model_v1 import build,adapter,HERE,ROOT

def main(path):
 start=time.monotonic();ct=json.loads(path.read_text());end=start+ct['internal_seconds'];out={'schema':'f722-native7-IO4-native-only-chamber/v1','selected':False,'native_board_edited':False,'routes':[],'checks':[],'RX_plans':[],'source_context':'exact native7 only,11 declared support/prefix cuts,4 candidate pad-net changes'};output=ROOT/ct['receipt']
 def save():out['seconds']=time.monotonic()-start;output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
 def alarm(sig,frame):out['terminal_reason']='Native-only structural query deadline';save();raise TimeoutError()
 for x in ct['source_files']:assert adapter.digest(ROOT/x['path'])==x['sha256'],x['path']
 signal.signal(signal.SIGALRM,alarm);signal.alarm(ct['internal_seconds'])
 try:
  from shapely import unary_union
  from shapely.geometry import Point
  from shapely.ops import nearest_points
  g,base,C,view,work,inventory=build();out['inventory']=inventory;out['source']=g.binding();out['contract_sha256']=adapter.digest(path)
  old=base.entry(base.by['97282ff5-d6b5-415f-a3c4-0390df70f0ea']);out['old_GND_stitch_saved_fill_contacts']=[]
  for z in base.N['zones']:
   if z['rule'] or z['net']!='GND':continue
   for l,ps in z['filled'].items():
    if l not in ('In1.Cu','In4.Cu') or not ps:continue
    fill=g.s.geom(ps);assert fill.is_valid;area=fill.intersection(old[1][l].difference(old[3])).area
    if area>0:out['old_GND_stitch_saved_fill_contacts'].append({'zone_uuid':z['uuid'],'layer':l,'annular_overlap_mm2':area,'new_return_and_fresh_plane_continuity_unproved':True})
  def add(points,name,role):
   net,peers=view('PORT_C_RX_EXT',role,work);finite=g.check_track(net,'F.Cu',points,width=.127,objects=peers);r={'kind':'track','name':name,'net':'PORT_C_RX_EXT','logical_net':'PORT_C_RX_EXT','role':role,'layer':'F.Cu','points':points,'width':.127};out['routes'].append(r);row={'name':name,'passed':C._passed(finite),'nearest':finite[:8]};row['full_width_actual_pad_entries']=C._section(g,r,work);row['passed']=row['passed'] and any(v['actual_pad']=='U15.5' and v['point']==points[0] and v['passed'] for v in row['full_width_actual_pad_entries']);out['checks'].append(row)
   if not row['passed']:raise C.CFailure('Finite native-only source contact fails '+name)
   q=g.track(r['net'],r['layer'],points,name,.127);work.append((dict(q[0],role=role),*q[1:]))
  add([g.one_pad('U15.5')['xy'],g.one_pad('U15.6')['xy']],'native-only-IO4-up-bonded-bridge','upstream')
  add([g.one_pad('U15.5')['xy'],[24.7,18.6]],'native-only-IO4-down-west-prefix','downstream')
  io=g.entry(g.one_pad('U15.5'))[1]['F.Cu'];up=work[-2][1]['F.Cu'].difference(io);down=work[-1][1]['F.Cu'].difference(io);out['outside_IO5_role_separation']={'gap_mm':up.distance(down),'minimum_mm':.127,'passed':up.distance(down)>=.127+g.s.ERROR};assert out['outside_IO5_role_separation']['passed']
  for name,role,a,target in [('RX_down','downstream',[24.7,18.6],'R34.1'),('RX_up','upstream',g.one_pad('U15.6')['xy'],'J11.1')]:
   b=g.one_pad(target);job={'name':name,'net':'PORT_C_RX_EXT','role':role,'width':.127,'a':a,'b':b['xy'],'start_layers':['F.Cu'],'end_layers':list(b['copper']),'layers':list(C.ORDINARY)};p,graph=C._plan(g,view,job,work,end);row={'job':job,'plan':p};out['RX_plans'].append(row);save();alias,peers=C._view(view,job,work)
   def reach(seeds):
    seen=set(seeds);stack=list(seeds)
    while stack:
     for nxt,w,e in graph['adj'][stack.pop()]:
      if nxt not in seen:seen.add(nxt);stack.append(nxt)
    return seen
   ss=reach(p['start_nodes']);tt=reach(p['end_nodes']);src=unary_union([graph['nodes'][i][1] for i in ss if graph['nodes'][i][0]=='F.Cu']);eligible=unary_union([graph['eligible'][i] for i in ss if i in graph['eligible'] and graph['nodes'][i][0]=='F.Cu']);row['source_F']={'area_mm2':src.area,'bounds':None if src.is_empty else list(src.bounds),'wkb_hex':src.wkb_hex,'legal_via_area_mm2':eligible.area,'legal_via_wkb_hex':eligible.wkb_hex}
   pairs=sorted([(graph['nodes'][i][1].distance(graph['nodes'][j][1]),i,j) for i in ss if graph['nodes'][i][0]=='F.Cu' for j in tt if graph['nodes'][j][0]=='F.Cu'])
   row['actual_target_connected_F_frontiers']=[]
   for gap,i,j in pairs[:6]:
    if i==j:continue
    x,y=nearest_points(graph['nodes'][i][1],graph['nodes'][j][1]);pts=[list(x.coords[0]),list(y.coords[0])];checks=g.check_track(alias,'F.Cu',pts,width=.127,objects=peers);bad=[q for q in checks if not q['pass_with_polygon_error']]
    row['actual_target_connected_F_frontiers'].append({'gap_mm':gap,'points':pts,'source_node':i,'target_node':j,'blockers':bad,'ordinary_target_connection_is_graph_proven':True})
   save()
  out['both_RX_graphs_connected']=all(q['plan']['connected'] for q in out['RX_plans']);out['terminal_reason']='Native7-only actual IO5 exits and target-connected F separators measured; all GND/HOLD replacements and full route closure still required';save()
 except TimeoutError:pass
 except Exception as e:out['terminal_reason']=str(e);out['exception_type']=type(e).__name__;save()
 finally:
  signal.alarm(0);print(json.dumps({'seconds':time.monotonic()-start,'terminal_reason':out.get('terminal_reason'),'RX':[(r['job']['name'],r['plan']['connected']) for r in out['RX_plans']],'receipt_sha256':adapter.digest(output)},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);main(p.parse_args().contract)
