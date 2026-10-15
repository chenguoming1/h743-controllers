from pathlib import Path
import pcbnew as k,json,sys,math,hashlib,collections
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();uid=lambda x:x.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));center=(106.4485,112.408894)
def clone(p):return k.SHAPE_POLY_SET(p)
def hit(a,b):
 r=k.SHAPE.Collide(a,b,0);return r[0] if isinstance(r,tuple) else bool(r)
def rect(points):
 q=k.SHAPE_POLY_SET();c=k.SHAPE_LINE_CHAIN()
 for p in points:c.Append(vec(p))
 c.SetClosed(True);q.AddOutline(c);return q
def subtract(a,b):
 q=clone(a);q.BooleanSubtract(b);return q
def area(p):return abs(p.Area())/1e12
def patch(v,g):
 p=xy(v.GetPosition());rad=v.GetWidth(k.F_Cu)/2e6;drill=v.GetDrillValue()/2e6
 for ang in range(0,360,15):
  a=math.radians(ang);d=(math.cos(a),math.sin(a));n=(-d[1],d[0]);pts=[(p[0]+(.15+ax*.01)*d[0]+ny*.0635*n[0],p[1]+(.15+ax*.01)*d[1]+ny*.0635*n[1]) for ax,ny in [(-1,-1),(1,-1),(1,1),(-1,1)]]
  if not all(drill+.001<math.dist(p,x)<rad for x in pts):continue
  if area(subtract(rect(pts),g))<1e-10:return {'width_mm':.127,'depth_mm':.020,'corners':pts}
 return None
boards={};fills={};measure={}
ports=['0e353f99-f08a-45ce-95f8-37326f8e52cd','63de1067-fbce-4e94-9040-d8d8ab583e97']
for label,D in [('before',S),('after',O)]:
 P=D/'hardware/nexus-style-fc.kicad_pcb';b=k.LoadBoard(str(P));boards[label]=b;ts={uid(t):t for t in b.GetTracks()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};objs={u:q for u,q in {**ts,**ps}.items() if q.GetNetname()=='GND'};ls=list(b.GetEnabledLayers().CuStack());conn=b.GetConnectivity();adj=collections.defaultdict(set);ground={}
 for u,t in ts.items():
  if t.GetNetname()!='GND':continue
  for q in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)):
   w=uid(q)
   if u!=w and w in objs and any(t.IsOnLayer(l) and objs[w].IsOnLayer(l) and hit(t.GetEffectiveShape(l),objs[w].GetEffectiveShape(l)) for l in ls):adj[u].add(w);adj[w].add(u)
 for l in [k.In1_Cu,k.In4_Cu]:
  q=k.SHAPE_POLY_SET()
  for z in b.Zones():
   if not z.GetIsRuleArea() and z.GetNetname()=='GND' and z.IsOnLayer(l):q.BooleanAdd(z.GetFilledPolysList(l))
  ground[b.GetLayerName(l)]=q
 via_ids={u for u,t in ts.items() if isinstance(t,k.PCB_VIA) and t.GetNetname()=='GND' and math.dist(center,xy(t.GetPosition()))<=5};assert via_ids
 paths=[]
 for port in ports:
  queue=collections.deque([(port,[port])]);seen=set();found=[]
  while queue:
   u,path=queue.popleft()
   if u in seen:continue
   seen.add(u)
   if u in via_ids:
    contact=[]
    for lay,g in ground.items():
     components=[g.UnitSet(i) for i in range(g.OutlineCount())];ci=max(range(len(components)),key=lambda i:area(components[i]));proof=patch(ts[u],components[ci]);assert proof,(label,port,u,lay);contact.append({'layer':lay,'component_index':ci,'component_area_mm2':area(components[ci]),'finite_annular_patch':proof})
    found.append({'via':u,'position':xy(ts[u].GetPosition()),'direct_primitive_contact_path':path,'contacts_to_main_GND_component':contact})
   for w in sorted(adj[u]-seen):queue.append((w,path+[w]))
  assert found,(label,port,'No local plane-connected return via');paths.append({'retained_external_port':port,'reachable_local_ground_vias':found})
 ground_route=next(r for r in tr['routes'] if r['net']=='GND');routeids=ground_route['removed_uuids'] if label=='before' else ground_route['new_uuids'];measure[label]={'board_sha256':sha(P),'complete_ground_donor_length_mm':sum(ts[u].GetLength()/1e6 for u in routeids),'ground_donor_layer':'B.Cu','ground_donor_width_mm':.127,'all_local_GND_vias_within_5_mm':sorted(via_ids),'retained_ports_to_actual_plane_paths':paths};fills[label]=ground
assert measure['before']['board_sha256']==tr['source_board_sha256']
for a,b in zip(measure['before']['retained_ports_to_actual_plane_paths'],measure['after']['retained_ports_to_actual_plane_paths']):assert {x['via'] for x in a['reachable_local_ground_vias']}=={x['via'] for x in b['reachable_local_ground_vias']}
# A relocated signal-via antipad can change the plane only locally. Require no remote fill loss or new component split.
local=rect([(105.9,111.85),(107,111.85),(107,112.95),(105.9,112.95)]);changes=[]
for lay,old in fills['before'].items():
 new=fills['after'][lay];lost=subtract(old,new);added=subtract(new,old);assert area(subtract(lost,local))<1e-10 and area(subtract(added,local))<1e-10,(lay,'Nonlocal fill change');assert old.OutlineCount()==new.OutlineCount(),(lay,'Changed plane component count');changes.append({'layer':lay,'removed_GND_area_mm2':area(lost),'added_GND_area_mm2':area(added),'removed_outside_local_rect_mm2':area(subtract(lost,local)),'added_outside_local_rect_mm2':area(subtract(added,local)),'before_after_component_count':old.OutlineCount()})
out={'status':'PASS: complete full-width GND donor ports retain direct copper paths to the same local vias and finite contacts to the main In1/In4 GND components; via-antipad fill changes remain local without component splitting','source_sha256':sha(S/'hardware/nexus-style-fc.kicad_pcb'),'candidate_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'measurements':measure,'main_plane_changes':changes,'qualification':'Local finite copper and component continuity only; no high-frequency return impedance, power or system qualification.'};(O/'local-ground-return-proof.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
