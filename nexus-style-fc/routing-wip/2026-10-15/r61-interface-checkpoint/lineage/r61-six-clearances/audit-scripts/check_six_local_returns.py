from pathlib import Path
import pcbnew as k,sys,json,hashlib,collections
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();uid=lambda o:o.m_Uuid.AsString();area=lambda p:abs(p.Area())/1e12;ret=json.loads((O/'usb-reference-return-verification.json').read_text());j=json.loads((O/'source-review/0-transaction-proposal.json').read_text());sda=json.loads((O/'source-review/1-sda-scl-imu-transaction.json').read_text());vsys=json.loads((O/'source-review/2-vsys-transaction.json').read_text());groups=[{'name':r['name'],'old':r['removed_uuids'],'new':r['new_uuids']} for r in j['routes']]+[{'name':'coordinated_SDA_SCL_IMU','old':sda['removed_uuids'],'new':[x['uuid'] for x in sda['added_primitives']]},{'name':'F2_VSYS_escape','old':vsys['removed_uuids'],'new':[x['uuid'] for x in vsys['added_primitives']]}];measure=[];paths=[];lengths={};boards=[]
def hit(a,b):
 z=k.SHAPE.Collide(a,b,0);return z[0] if isinstance(z,tuple) else bool(z)
def polygon(o,l):
 p=k.SHAPE_POLY_SET();o.TransformShapeToPolygon(p,l,0,1,k.ERROR_INSIDE)
 if isinstance(o,k.PCB_VIA):
  h=k.PCB_TRACK(o.GetBoard());h.SetLayer(l);h.SetStart(o.GetPosition());h.SetEnd(o.GetPosition());h.SetWidth(o.GetDrillValue());q=k.SHAPE_POLY_SET();h.TransformShapeToPolygon(q,l,0,1,k.ERROR_OUTSIDE);p.BooleanSubtract(q)
 return p
for state,D,which in [('source',S,'old'),('candidate',O,'new')]:
 b=k.LoadBoard(str(D/'hardware/nexus-style-fc.kicad_pcb'));boards.append(b);ts={uid(t):t for t in b.GetTracks()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};layers=list(b.GetEnabledLayers().CuStack());fills={}
 for l in layers:
  g=k.SHAPE_POLY_SET()
  for z in b.Zones():
   if z.GetNetname()=='GND' and not z.GetIsRuleArea() and z.IsOnLayer(l):g.BooleanAdd(z.GetFilledPolysList(l))
  fills[b.GetLayerName(l)]=g
 for group in groups:
  for net in sorted({ts[u].GetNetname() for u in group[which]}):
   for layer,refs in [('F.Cu',['In1.Cu']),('B.Cu',['In4.Cu']),('In2.Cu',['In1.Cu','In3.Cu']),('In3.Cu',['In2.Cu','In4.Cu'])]:
    l=b.GetLayerID(layer);selected=[ts[u] for u in group[which] if not isinstance(ts[u],k.PCB_VIA) and ts[u].GetNetname()==net and ts[u].GetLayer()==l]
    if not selected:continue
    length=sum(x.GetLength()/1e6 for x in selected);lengths[state,group['name'],net,layer]=length;p=k.SHAPE_POLY_SET()
    for t in selected:p.BooleanAdd(polygon(t,l))
    for ref in refs:
     g=fills[ref];miss=k.SHAPE_POLY_SET(p);miss.BooleanSubtract(g);components=[]
     for i in range(g.OutlineCount()):
      q=k.SHAPE_POLY_SET(p);q.BooleanIntersection(g.UnitSet(i));ar=area(q)
      if ar>1e-10:
       key=f'{ref}:{i}';d=next(x for x in ret['measurements'][state]['filled_components'] if x['id']==key);assert d['finite_via_connected_to_main_ground'];components.append(key)
     measure.append({'state':state,'group':group['name'],'net':net,'layer':layer,'reference_layer':ref,'centerline_length_mm':length,'full_width_copper_area_mm2':area(p),'uncovered_area_mm2':area(miss),'ground_coverage_fraction':1-area(miss)/area(p),'actual_finitely_connected_reference_components':components})
 # Explicit native physical GND contact graph, excluding zone shortcuts.
 objs={**{u:t for u,t in ts.items() if t.GetNetname()=='GND'},**{u:p for u,p in ps.items() if p.GetNetname()=='GND'}};adj={u:set() for u in objs};conn=b.GetConnectivity();edge={}
 for u,t in ts.items():
  if u not in objs:continue
  for q0 in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)):
   w=uid(q0)
   if w not in objs or w==u:continue
   q=objs[w]
   for l in layers:
    if t.IsOnLayer(l) and q.IsOnLayer(l) and hit(t.GetEffectiveShape(l),q.GetEffectiveShape(l)):
     # Positive geometric overlap; full-width new contacts are separately proved.
     p=polygon(t,l);p.BooleanIntersection(polygon(q,l));ar=area(p)
     if ar>1e-6:adj[u].add(w);adj[w].add(u);edge[tuple(sorted([u,w]))]={'layer':b.GetLayerName(l),'finite_overlap_area_mm2':ar};break
 mainvia={x['via'] for x in ret['measurements'][state]['finite_ground_via_component_contacts'] if x['component'] in ret['measurements'][state]['main_plane_root_components']}
 for u,p in ps.items():
  if not (p.GetNetname()=='GND' and (p.GetParentFootprint().GetReference() in ['C6','C11'] or p.GetParentFootprint().GetReference()=='U1' and p.GetNumber()=='12')):continue
  todo=[(u,[u])];seen={u};found=None
  while todo:
   w,path=todo.pop(0)
   if w in mainvia:found=path;break
   for q in adj[w]-seen:seen.add(q);todo.append((q,path+[q]))
  assert found,('Missing local finite main-plane return',state,u);paths.append({'state':state,'reference':p.GetParentFootprint().GetReference(),'pin':p.GetNumber(),'pad':u,'physical_path_to_finite_main_plane_via':found,'edge_overlaps':[edge[tuple(sorted([aa,bb]))] for aa,bb in zip(found,found[1:])]})
old={ (x['net'],x['routing_layer'],x['reference_layer']):x for x in ret['measurements']['source']['full_width_usb_projection']};usb=[]
for x in ret['measurements']['candidate']['full_width_usb_projection']:
 key=(x['net'],x['routing_layer'],x['reference_layer']);d=x['uncovered_area_mm2']-old[key]['uncovered_area_mm2'];assert abs(d)<1e-9;usb.append({'net_layer_reference':list(key),'added_uncovered_mm2':d})
deltas=[]
for name,net,layer in sorted({k[1:] for k in lengths}):deltas.append({'group':name,'net':net,'layer':layer,'source_length_mm':lengths.get(('source',name,net,layer),0),'candidate_length_mm':lengths.get(('candidate',name,net,layer),0)})
out={'status':'PASS: actual local references and finite C6/C11/U1.12 ground returns; USB projection unchanged','source_board_sha256':sha(S/'hardware/nexus-style-fc.kicad_pcb'),'candidate_board_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'per_net_layer_length_changes':deltas,'full_width_local_reference_measurements':measure,'critical_local_ground_paths':paths,'unchanged_USB_reference_projection':usb,'power_return_scope':j['return_power_implications'],'VSYS_supply_side_roles':vsys['actual_vsys_branches_after_cutting_new_transaction'],'qualification':'All affected power copper remains on its original layers at original widths; 3V3 and VSYS total donor lengths decrease. The direct B.Cu U1.12/C11.2 ground donor is shorter, with finite local main-plane paths retained. Projection/copper continuity does not establish impedance, capacitor derating, loop transient performance, fault current or assembly qualification. C27/C31/J4 redesign remains a separate future transaction.'};(O/'local-return-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status']);print(json.dumps(deltas,indent=2))
