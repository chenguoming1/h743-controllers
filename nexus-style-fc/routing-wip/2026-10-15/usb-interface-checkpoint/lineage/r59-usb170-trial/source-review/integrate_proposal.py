"""Read-only source-bound primitive transaction and cross-subsection screen. Writes reports only."""
from static_clearance import *
import copy
P=json.loads((D/'ports/compact-in1-port-proposal.json').read_text());M=json.loads((D/'mcu/candidate.json').read_text());T=json.loads((D/'trunk-proposal.json').read_text())
assert P['sha256']==M['source_sha256']==T['source_sha256']==H
bridges=set(P['preserve_bridge_uuids']);reuse=set(P['reuse_existing_vias'])
deleted={t['uuid'] for t in usbtracks if t['uuid'] not in bridges}|{v['uuid'] for v in usbvias if v['uuid'] not in reuse}|set(P['replace_foreign_track_uuids'])|set(P['replace_foreign_via_uuids'])|set(M['removed_uuids'])
source_by_id={o['uuid']:o for o in tracks+vias+pads}
new=[]
for s in P['segments']:
 if 'bridge_preserve' not in s['id']:new.append(dict(s,group='ports'))
for v in P['new_vias']:new.append(dict(v,group='ports'))
for i,o in enumerate(M['new_objects']):new.append(dict(o,group='mcu',id='mcu_'+str(i)))
trunk=[]
for lane in T['lanes']:
 net='USB_DM' if lane['lane']=='left' else 'USB_DP'
 pp=copy.deepcopy(lane['primitives']);pp[-1]['end'][1]=110.85;pp[-1]['length_mm']=math.dist(pp[-1]['start'],pp[-1]['end'])
 for i,o in enumerate(pp):
  o.update(net=net,width=o.pop('width_mm'),group='trunk',id=net+'_trunk_'+str(i))
  if o['kind']=='arc':
   a=o['start_radians']+o['sweep_radians']/2;o['mid']=[o['center'][0]+o['radius_mm']*math.cos(a),o['center'][1]+o['radius_mm']*math.sin(a)]
  trunk.append(o)
new+=trunk
retained_usb=[dict(source_by_id[u],group='preserved') for u in bridges|reuse]
all_usb=[o for o in new+retained_usb if o['net'] in ('USB_DP','USB_DM')]

def chorded(o):
 if o['kind']!='arc':return [o]
 tol=.000002;r=o['radius_mm'];n=math.ceil(abs(o['sweep_radians'])/(2*math.acos(1-tol/r)));aa=np.linspace(o['start_radians'],o['start_radians']+o['sweep_radians'],n+1);pp=np.array(o['center'])+r*np.column_stack((np.cos(aa),np.sin(aa)))
 return [dict(o,kind='segment',start=a.tolist(),end=b.tolist(),chord_error_mm=r*(1-math.cos(abs(o['sweep_radians'])/n/2))) for a,b in zip(pp[:-1],pp[1:])]

def gap(a,b):
 if a['kind']==b['kind']=='segment':
  if a['layer']!=b['layer']:return math.inf
  return seg_seg(a['start'],a['end'],b['start'],b['end'])-(a['width']+b['width'])/2
 if a['kind']==b['kind']=='via':return math.dist(a['at'],b['at'])-(a['diameter']+b['diameter'])/2
 if b['kind']=='pad':
  if a['kind']=='segment':
   if a['layer'] not in b['layers'] and '*.Cu' not in b['layers']:return math.inf
   return seg_pad(a['start'],a['end'],b)-a['width']/2
  return seg_pad(a['at'],a['at'],b)-a['diameter']/2
 if a['kind']=='pad':return gap(b,a)
 v,t=(a,b) if a['kind']=='via' else (b,a)
 return point_seg(v['at'],t['start'],t['end'])[0]-(v['diameter']+t['width'])/2
flat=[q for o in new+retained_usb for q in chorded(o)]
# Independent subsection screens already exist. Here test every cross-subsection foreign contact.
cross=[]
for i,a in enumerate(flat):
 for b in flat[:i]:
  if a['net']==b['net'] or a['group']==b['group']:continue
  g=gap(a,b);err=a.get('chord_error_mm',0)+b.get('chord_error_mm',0)
  if g<.3:cross.append(dict(a=a.get('id',a.get('uuid')),b=b.get('id',b.get('uuid')),groups=[a['group'],b['group']],gap_mm=g,chord_error_bound_mm=err))
cross.sort(key=lambda q:q['gap_mm']);fail=[r for r in cross if r['gap_mm']+r['chord_error_bound_mm']<.127-1e-8]
# Physical copper components include finite pad/via/trace overlap. Arc chords have tiny conservative geometry uncertainty.
components=[]
for net in ['USB_DP','USB_DM']:
 objs=[o for o in flat if o['net']==net]+[dict(p,group='pad') for p in pads if p['net']==net]
 adj={i:set() for i in range(len(objs))}
 for i,a in enumerate(objs):
  for j,b in enumerate(objs[:i]):
   if a['kind']==b['kind']=='pad':continue
   if gap(a,b)<=1e-8:adj[i].add(j);adj[j].add(i)
 seen=set();comps=[]
 for i in adj:
  if i in seen:continue
  sub={i};todo=[i];seen.add(i)
  while todo:
   k=todo.pop()
   for j in adj[k]-seen:seen.add(j);sub.add(j);todo.append(j)
  comps.append(dict(object_count=len(sub),pads=[objs[j]['ref']+'.'+objs[j]['pin'] for j in sub if objs[j]['kind']=='pad']))
 components.append(dict(net=net,components=comps))
# Exact endpoint centerline graph. Zero-length barrel/contact edges explicitly are not delay estimates.
def key(layer,p):return (layer,round(p[0],8),round(p[1],8))
pathreports=[]
for net in ['USB_DP','USB_DM']:
 oo=[o for o in all_usb if o['net']==net];adj=collections.defaultdict(list)
 def edge(a,b,w,item):adj[a].append((b,w,item));adj[b].append((a,w,item))
 for o in oo:
  oid=o.get('id',o.get('uuid'))
  if o['kind'] in ['segment','arc']:edge(key(o['layer'],o['start']),key(o['layer'],o['end']),o.get('length_mm',math.dist(o['start'],o['end'])),dict(kind=o['kind'],id=oid,layer=o['layer']))
  else:
   for l in ls:edge(key(ls[0],o['at']),key(l,o['at']),0,dict(kind='synthetic_zero_length_via_transition',id=oid))
 jnums=['A6','B6'] if net=='USB_DP' else ['A7','B7'];mcupin='45' if net=='USB_DP' else '44'
 endpad=next(p for p in pads if p['ref']=='U1' and p['pin']==mcupin);end=key('B.Cu',endpad['at'])
 for jn in jnums:
  p=next(p for p in pads if p['ref']=='J6' and p['pin']==jn);start=key('F.Cu',p['at']);dist={start:0};prev={};q=[(0,start)]
  while q:
   d,k=heapq.heappop(q)
   if d!=dist[k]:continue
   for j,w,it in adj[k]:
    if d+w<dist.get(j,math.inf)-1e-10:dist[j]=d+w;prev[j]=(k,it);heapq.heappush(q,(d+w,j))
  route=[];cur=end
  if end in dist:
   while cur!=start:pr,it=prev[cur];route.append(it);cur=pr
  route=route[::-1]
  pathreports.append(dict(net=net,connector='J6.'+jn,mcu='U1.'+mcupin,connected_by_exact_endpoint_graph=end in dist,planar_centerline_mm=dist.get(end),via_count=len({r['id'] for r in route if r['kind']=='synthetic_zero_length_via_transition'}),route=route))
transaction=dict(source_path=str(S),source_sha256=H,status='CONDITIONAL_STATIC_COMPLETE_TOPOLOGY_NOT_NATIVE_OR_SI_ACCEPTED',delete_uuids=sorted(deleted),delete_expected_records=[source_by_id[u] for u in sorted(deleted)],preserve_bridge_uuids=sorted(bridges),reuse_via_uuids=sorted(reuse),add_primitives=new,all_other_source_objects_unchanged=True,arc_definition='KiCad arc start/mid/end included; exact circular geometry, not chord replacement',usb_width_mm=.15,ordinary_via_size_drill_mm=[.45,.2],conditions=['Owner review of actual reference/impedance variation before adopting; no claim of SI completion.','Native refill, DRC/connectivity/parity, mask/paste/return audit required in exclusive heavy lane.','Sub-micron nominal clearance margin at retained B_TX/GND gate is not manufacturing tolerance qualification.','No parts, nets, ground donor geometry, shielding, ESD return, or approved power widths changed.'])
summary=dict(source_sha256_before=H,source_sha256_after=hashlib.sha256(S.read_bytes()).hexdigest(),add_count=len(new),delete_count=len(deleted),cross_subsection_failures=fail,minimum_cross_subsection_gaps=cross[:30],physical_usb_components=components,exact_endpoint_paths=pathreports,trunk_lane_length_mm={net:sum(o['length_mm'] for o in trunk if o['net']==net) for net in ['USB_DP','USB_DM']},all_net_planar_copper_totals_mm={net:sum(o.get('length_mm',math.dist(o['start'],o['end'])) for o in all_usb if o['net']==net and o['kind']!='via') for net in ['USB_DP','USB_DM']},all_net_via_counts={net:sum(o['kind']=='via' for o in all_usb if o['net']==net) for net in ['USB_DP','USB_DM']},length_caution='Planar centerline only. Endpoint graph uses synthetic zero-length via transition edges, omits physical barrels and pad spreading. Not electrical delay, does not claim propagation matching.',source_sha256=H)
(D/'complete-transaction.json').write_text(json.dumps(transaction,indent=2)+'\n');(D/'integration-screen.json').write_text(json.dumps(summary,indent=2)+'\n')
print('counts',len(new),len(deleted),'crossfail',len(fail));print('components',components);print('paths',[(r['connector'],r['connected_by_exact_endpoint_graph'],r['planar_centerline_mm'],r['via_count']) for r in pathreports]);print('trunk',summary['trunk_lane_length_mm']);print('source',summary['source_sha256_after'])
