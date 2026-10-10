"""Complete the remaining RPM bridge leg using the established whole-outline layer graph."""
import routing_context15 as c
import json,time,math,heapq,signal
from shapely.geometry import Point,LineString
from shapely import unary_union
from shapely.strtree import STRtree
from shapely.ops import nearest_points,polylabel
t0=time.monotonic();signal.alarm(87);P=c.H/'complete-bridge-proposal.json';prior=c.read(P);assert prior['source_board_sha256']==c.n['board_sha256'];assert len(prior['routes'])==3 and prior['routes'][-1]['passed'];A=[9.013184,20.667320];B=c.MCU;c.vias=prior['vias'];c.own=unary_union([Point(v['xy']).buffer(.225+.127+.01,quad_segs=96)for v in c.vias]);layers=['F.Cu','B.Cu','In2.Cu','In3.Cu'];components={};trees={}
for layer in layers:
 components[layer]=c.parts(c.free(c.obstacles(layer,layer=='B.Cu'),layer,layer=='B.Cu'));trees[layer]=STRtree(components[layer])
def belongs(xy):
 p=Point(xy);return{l:int(i)for l in layers for i in trees[l].query(p)if components[l][i].covers(p)}
vo=c.s.obstacles(c.net,'F.Cu')[1]
for o in c.source:vo.append(dict(object=o.get('key',o['uuid']),layers=['B.Cu'],category='retained_source_clamp_bypass_guard',geometry=c.s.geom(o['copper']['B.Cu']),required_center_distance_mm=.352))
expanded=unary_union([o['geometry'].buffer((o['required_center_distance_mm']+.0001)/math.cos(math.pi/128),quad_segs=32)for o in vo if o['category']!='edge_npth_copper']);legal=c.s.OUTLINE.buffer(-.4791).difference(expanded).difference(unary_union([Point(v['xy']).buffer(.4501,quad_segs=96)for v in c.vias]));nodes=[dict(xy=A,components=belongs(A)),dict(xy=B,components=belongs(B))];direct=LineString([A,B]);assert c.s.OUTLINE.covers(direct)
for region in c.parts(legal):
 if region.area<1e-7:continue
 inner=region.buffer(-.003);p=nearest_points(direct,inner)[1]if not inner.is_empty else polylabel(region,tolerance=.0001);xy=[round(v,6)for v in p.coords[0]];comps=belongs(xy);z=c.s.check(Point(xy),vo)
 if len(comps)<2 or z[0]['extra_clearance_mm']<.00001:continue
 nodes.append(dict(xy=xy,components=comps,via_region_area_mm2=region.area,nearest=z[:3]))
bycomp={}
for i,node in enumerate(nodes):
 for l,k in node['components'].items():bycomp.setdefault((l,k),[]).append(i)
queue=[(0,0)];dist={0:0};prev={}
while queue:
 cost,i=heapq.heappop(queue)
 if cost!=dist[i]:continue
 if i==1:break
 for l,k in nodes[i]['components'].items():
  for j in bycomp[(l,k)]:
   if i==j:continue
   cost2=cost+math.dist(nodes[i]['xy'],nodes[j]['xy'])+(5 if j>1 else 0)
   if cost2<dist.get(j,1e100):dist[j]=cost2;prev[j]=(i,l);heapq.heappush(queue,(cost2,j))
out=dict(prior,schema='f722-complete-RPM-layer-transition-proposal/v3',complete=False,layer_graph=dict(nodes=nodes,component_counts={l:len(p)for l,p in components.items()},connected=1 in dist),script_sha256=c.sha(c.H/'complete_layer_graph15.py'),context_sha256=c.sha(c.H/'routing_context15.py'),attempts=[])
def save():out['elapsed_seconds']=time.monotonic()-t0;(c.H/'complete-layer-proposal.json').write_text(json.dumps(out,indent=2)+'\n')
save();assert 1 in dist,'No whole-outline layer graph path';legs=[];seq=[1]
while seq[-1]!=0:legs.append((prev[seq[-1]][0],seq[-1],prev[seq[-1]][1]));seq.append(prev[seq[-1]][0])
legs.reverse();out['layer_graph']['selected_legs']=[dict(layer=l,start=nodes[i]['xy'],end=nodes[j]['xy'])for i,j,l in legs];out['layer_graph']['new_transition_vias']=[nodes[i]for i in reversed(seq[1:-1])];print('GRAPH',out['layer_graph']['selected_legs'],time.monotonic()-t0,flush=True)
for k,node in enumerate(out['layer_graph']['new_transition_vias']):out['vias'].append(dict(name='RPM-extra-transition-'+str(k),net=c.net,xy=node['xy']))
c.own=unary_union([Point(v['xy']).buffer(.225+.127+.01,quad_segs=96)for v in out['vias']]);save()
for k,(i,j,l)in enumerate(legs):
 r=c.route(nodes[i]['xy'],nodes[j]['xy'],l,l=='B.Cu');r['name']='RPM-extra-leg-'+str(k);out['attempts'].append(r);save();print(r,flush=True)
 if not r['passed']:raise SystemExit(2)
 out['routes'].append(r);save()
out['complete']=True;out['pair_drill_gaps']=[dict(a=a['name'],b=b['name'],gap_mm=math.dist(a['xy'],b['xy'])-.2,passed=math.dist(a['xy'],b['xy'])-.2>=.25)for i,a in enumerate(out['vias'])for b in out['vias'][i+1:]];out['complete']=all(r['passed']for r in out['pair_drill_gaps']);save();assert out['complete'];print('COMPLETE',time.monotonic()-t0,flush=True)
