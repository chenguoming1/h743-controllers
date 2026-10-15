from pathlib import Path
import pcbnew as k,json,hashlib,sys,math,collections,importlib.util,copy
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();P=O/'hardware/nexus-style-fc.kicad_pcb';SP=S/'hardware/nexus-style-fc.kicad_pcb';assert sha(SP)==tr['source_board_sha256'];spec=importlib.util.spec_from_file_location('V',R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
a,b=[k.LoadBoard(str(p)) for p in [SP,P]];ls=list(b.GetEnabledLayers().CuStack());uid=lambda o:o.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));rm=set(tr['removed_uuids']);defs={r['uuid']:r for r in tr['added_primitives']};add=set(defs);taper={u for u,r in defs.items() if r['kind']=='taper_copper_polygon'}
st,ct=[V.parse_sexpr(p.read_text()) for p in [SP,P]];inv=V.invariant_checks(a,b,st,ct);assert inv['status']=='pass',inv
for tag in ['segment','arc','via','gr_poly','gr_line','gr_arc','gr_text','group']:
 aa,bb=[V.keyed_nodes(V.children(t,tag)) for t in [st,ct]];assert {u:v for u,v in aa.items() if u not in rm}=={u:v for u,v in bb.items() if u not in add},('Unexpected native node change',tag)
at={uid(x):x for x in a.GetTracks()};bt={uid(x):x for x in b.GetTracks()};ap={uid(p):p for f in a.GetFootprints() for p in f.Pads()};bp={uid(p):p for f in b.GetFootprints() for p in f.Pads()};bg={uid(x):x for x in b.GetDrawings() if uid(x) in taper};assert set(at)-set(bt)==rm and set(bt)-set(at)==add-taper;objs={**bt,**bp,**bg}
def hit(a,b,c=0):
 z=k.SHAPE.Collide(a,b,c);return z[0] if isinstance(z,tuple) else bool(z)
def polygon(o,l,loc=k.ERROR_INSIDE):
 p=k.SHAPE_POLY_SET();o.TransformShapeToPolygon(p,l,0,1,loc);return p
def area(o):return abs(o.Area())/1e12
shapes={(u,l):o.GetEffectiveShape(l) for u,o in objs.items() for l in ls if o.IsOnLayer(l)}
def touches(u,w):return [l for l in ls if (u,l) in shapes and (w,l) in shapes and hit(shapes[u,l],shapes[w,l])]
records=[]
for u,r in defs.items():
 o=objs[u];assert o.GetNetname()==r['net']
 if r['kind'] in ['segment','arc']:
  assert o.GetWidth()==round(r['width']*1e6) and b.GetLayerName(o.GetLayer())==r['layer'];assert xy(o.GetStart())==tuple(round(x,6) for x in r['start']) and xy(o.GetEnd())==tuple(round(x,6) for x in r['end'])
  if r['net'] in ['USB_DP','USB_DM']:assert r['width'] in [.15,.17]
  if r['net']=='VBUS_C':assert r['width']==.25
 elif r['kind']=='via':assert o.GetDrillValue()==200000 and o.GetWidth(k.F_Cu)==450000 and xy(o.GetPosition())==tuple(round(x,6) for x in r['at'])
 else:
  assert o.IsSolidFill() and o.GetWidth()==0 and b.GetLayerName(o.GetLayer())=='In3.Cu';p=o.GetPolyShape();assert p.OutlineCount()==1 and p.VertexCount()==4;assert [(p.CVertex(i).x,p.CVertex(i).y) for i in range(4)]==[tuple(round(x*1e6) for x in pt) for pt in r['vertices_mm']]
# Preserve all retained same-net original direct contacts; explicitly enumerate each removed net's external ports.
conn=a.GetConnectivity();seen=set();retained=0;ports=collections.defaultdict(set)
for u,t in at.items():
 for q in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)):
  w=uid(q);q=at.get(w) or ap.get(w);pair=tuple(sorted([u,w]));layers=[l for l in ls if t.IsOnLayer(l) and q.IsOnLayer(l) and hit(t.GetEffectiveShape(l),q.GetEffectiveShape(l))]
  if u==w or pair in seen or not layers or t.GetNetname()!=q.GetNetname():continue
  seen.add(pair)
  if u not in rm and w not in rm:assert touches(u,w),('retained contact lost',pair);retained+=1
  if u in rm and w not in rm:ports[t.GetNetname()].add(w)
  if w in rm and u not in rm:ports[t.GetNetname()].add(u)
# Physical same-net graphs include native net-assigned taper polygons. No pad-to-pad internal device connection is inferred.
nets=sorted({r['net'] for r in defs.values()});graphs={};components={}
for net in nets:
 ids=[u for u,o in objs.items() if o.GetNetname()==net];adj={u:set() for u in ids}
 for i,u in enumerate(ids):
  for w in ids[:i]:
   if touches(u,w):adj[u].add(w);adj[w].add(u)
 graphs[net]=adj
 def walk(seed,removed=set()):
  seen={seed};todo=[seed]
  while todo:
   u=todo.pop()
   for w in adj[u]-seen-removed:seen.add(w);todo.append(w)
  return seen
 seeds=[u for u in add if defs[u]['net']==net];reached=walk(seeds[0]);assert set(seeds)|ports[net]<=reached,(net,'replacement component/ports disconnected')
 components[net]={'replacement_objects':len(seeds),'complete_external_ports':sorted(ports[net]),'component_object_count':len(reached)}
 if net in ['USB_DP','USB_DM']:
  required={u for u,p in bp.items() if p.GetNetname()==net};assert len(required)==5 and required<=reached;components[net]['required_pads']=[{'uuid':u,'ref':bp[u].GetParentFootprint().GetReference(),'pin':bp[u].GetNumber()} for u in sorted(required)]
  connector={u for u in required if bp[u].GetParentFootprint().GetReference()=='J6'};mcu=next(u for u in required if bp[u].GetParentFootprint().GetReference()=='U1');cuts=[]
  for bridge in tr['preserve_bridge_uuids']:
   if bt[bridge].GetNetname()!=net:continue
   for start in connector:assert mcu not in walk(start,{bridge}),('protection bridge bypass',net,bridge)
   cuts.append(bridge)
  components[net]['external_bridge_cut_checks']=cuts
# Finite full-width track-to-pad/via entries and complete retained track endpoint joints.
def patch(t,p,l):
 if isinstance(t,k.PCB_ARC):return None
 aa,zz=xy(t.GetStart()),xy(t.GetEnd());length=math.dist(aa,zz);dr=((zz[0]-aa[0])/length,(zz[1]-aa[1])/length);n=(-dr[1],dr[0]);rad=t.GetWidth()/2e6;cen=xy(p.GetPosition());proj=sum((cen[i]-aa[i])*dr[i] for i in range(2));off=abs(sum((cen[i]-aa[i])*n[i] for i in range(2)))
 for q in [proj+d for d in [0,.11,-.11,.13,-.13,.15,-.15,.18,-.18]]+[i*length/100 for i in range(1,100)]:
  if not .01<=q<=length-.01:continue
  corners=[(aa[0]+(q+s*.01)*dr[0]+c*rad*n[0],aa[1]+(q+s*.01)*dr[1]+c*rad*n[1]) for s in [-1,1] for c in [-1,1]]
  if not all(hit(p.GetEffectiveShape(l),vec(pt)) for pt in corners):continue
  dist=math.hypot(max(abs(proj-q)-.01,0),max(off-rad,0))
  if isinstance(p,k.PCB_VIA) and dist<p.GetDrillValue()/2e6+.001:continue
  return {'track':uid(t),'port':uid(p),'layer':b.GetLayerName(l),'width_mm':rad*2,'depth_mm':.02,'corners':corners}
 return None
portproofs=[]
for net,pp in ports.items():
 for u in pp:
  p=objs[u];proof=None
  for w in graphs[net][u]&add:
   t=objs[w]
   if w in taper or isinstance(t,k.PCB_VIA):continue
   if isinstance(p,k.PCB_VIA) or isinstance(p,k.PAD):proof=patch(t,p,t.GetLayer())
   else:
    common=set([xy(t.GetStart()),xy(t.GetEnd())])&set([xy(p.GetStart()),xy(p.GetEnd())])
    if common and t.GetWidth()>=p.GetWidth():proof={'port':u,'new_track':w,'shared_endpoints':list(common),'retained_width_mm':p.GetWidth()/1e6,'new_width_mm':t.GetWidth()/1e6}
   if proof:break
  # A preserved bridge or existing via can have an incidental overlap plus its unchanged full-width primary entry.
  if not proof:
   for w in graphs[net][u]-add:
    t=objs[w]
    if not isinstance(t,k.PCB_TRACK) or isinstance(t,k.PCB_VIA) or isinstance(t,k.PCB_ARC):continue
    if isinstance(p,(k.PCB_VIA,k.PAD)):
     entry=patch(t,p,t.GetLayer())
     if entry and (graphs[net][w]&add):proof={'port':u,'unchanged_full_width_entry':entry,'direct_new_component_contacts':sorted(graphs[net][u]&add),'bridge_new_contacts':sorted(graphs[net][w]&add)};break
  if not proof and isinstance(p,k.PCB_TRACK) and not isinstance(p,k.PCB_VIA):
   for w in graphs[net][u]&add:
    q=objs[w]
    if isinstance(q,k.PCB_VIA):
     pp=patch(p,q,p.GetLayer())
     if pp:proof={'port':u,'retained_track_full_width_into_new_via':pp};break
   if not proof:
    # Preserve the full inherited-width primary route through unchanged exact-endpoint donors,
    # separately from an incidental lateral overlap with the removed/replaced branch.
    eligible={w for w,q in objs.items() if isinstance(q,k.PCB_TRACK) and not isinstance(q,k.PCB_VIA) and q.GetNetname()==net and q.GetLayer()==p.GetLayer() and q.GetWidth()>=p.GetWidth()}
    queue=[(w,[w]) for w in add&eligible];seen2=set(w for w,path in queue)
    while queue and not proof:
     w,path=queue.pop(0)
     if w==u:proof={'port':u,'kind':'full inherited-width primary donor chain with exact centerline joints; incidental direct overlap remains','width_mm':p.GetWidth()/1e6,'layer':b.GetLayerName(p.GetLayer()),'chain':path};break
     ends={xy(objs[w].GetStart()),xy(objs[w].GetEnd())}
     for qid in eligible-seen2:
      if ends&{xy(objs[qid].GetStart()),xy(objs[qid].GetEnd())}:seen2.add(qid);queue.append((qid,path+[qid]))
  assert proof,('Unproved external finite full-width port',net,u);portproofs.append(proof)
viaproofs=[]
for u in add:
 v=objs[u]
 if not isinstance(v,k.PCB_VIA):continue
 adj=graphs[v.GetNetname()][u];layers={objs[w].GetLayer() for w in adj if isinstance(objs[w],k.PCB_TRACK) and not isinstance(objs[w],k.PCB_VIA)};entries=[]
 for l in layers:
  proofs=[patch(objs[w],v,l) for w in adj if isinstance(objs[w],k.PCB_TRACK) and not isinstance(objs[w],(k.PCB_VIA,k.PCB_ARC)) and objs[w].GetLayer()==l];proofs=[x for x in proofs if x];assert proofs,('New via annular entry missing',u,b.GetLayerName(l));entries.append(proofs[0])
 assert len(layers)>=2;viaproofs.append({'via':u,'entries':entries})
# Exact native taper geometry plus finite overlap and an uninterrupted 0.150 mm capsule
# through the complete taper. Some incoming fanouts are angled, so an axis-aligned
# rectangle across their endpoint would test the wrong conductor direction.
taperproofs=[]
for u in taper:
 r=defs[u];p=bg[u];poly=polygon(p,k.In3_Cu);joints=[];union=k.SHAPE_POLY_SET(poly)
 for key,widthkey in [('start_port','start_width_mm'),('end_port','end_width_mm')]:
  pt=tuple(round(x,6) for x in r[key]);touched=[bt[w] for w in graphs[r['net']][u] if w in bt and not isinstance(bt[w],k.PCB_VIA) and pt in [xy(bt[w].GetStart()),xy(bt[w].GetEnd())]];assert len(touched)==1;track=touched[0];assert track.GetWidth()==round(r[widthkey]*1e6);cp=polygon(track,k.In3_Cu);over=k.SHAPE_POLY_SET(poly);over.BooleanIntersection(cp);assert area(over)>.001;union.BooleanAdd(cp);joints.append({'port':key,'track':uid(track),'native_width_mm':track.GetWidth()/1e6,'finite_overlap_area_mm2':area(over)})
 start,end=r['start_port'],r['end_port'];mid=[start[0],start[1]+(end[1]-start[1])*.25];path=[start,mid,end];tests=[]
 for aa,zz in zip(path,path[1:]):
  capsule=k.PCB_TRACK(b);capsule.SetLayer(k.In3_Cu);capsule.SetStart(vec(aa));capsule.SetEnd(vec(zz));capsule.SetWidth(150000);test=polygon(capsule,k.In3_Cu);test.BooleanSubtract(union);assert area(test)<1e-8,('full-width taper path constriction',u,aa,zz,area(test));tests.append(area(test))
 taperproofs.append({'uuid':u,'net':r['net'],'joints':joints,'full_transition_no_neck_capsule_width_mm':.15,'capsule_path_points':path,'uncovered_capsule_area_mm2':tests,'method':'Exact approved trapezoid plus adjoining native copper contains two joined 0.150 mm swept round-ended conductors: first 0.050 mm axially from the narrow seam, then to the wide endpoint. Delaying the centerline shift until the taper has widened avoids the artificial straight-axis edge wedge. The shared full-radius disk proves continuity at the bend. Polygon approximation 1 nm; unchanged residual-area tolerance 0.00000001 mm2.'})

pa,pb=V.drill_paste_contacts(a),V.drill_paste_contacts(b);old={(r['via_uuid'],r['pad_uuid']) for r in pa};new={(r['via_uuid'],r['pad_uuid']) for r in pb};assert not new-old,('new pasted via contacts',new-old)
power=V.power_width_preservation(a,b);assert power['status']=='pass';pid='5f922c73-82b6-4073-8e98-d520c70499ca';p=bp[pid];assert p.GetNetname()=='unconnected-(U10-EN-Pad3)';en=[]
for l in ls:
 if not p.IsOnLayer(l):continue
 for u,o in objs.items():
  if u!=pid and o.IsOnLayer(l) and hit(p.GetEffectiveShape(l),o.GetEffectiveShape(l)):en.append(u)
 for z in b.Zones():
  if z.IsOnLayer(l) and not z.GetIsRuleArea() and hit(p.GetEffectiveShape(l),z.GetFilledPolysList(l)):en.append(uid(z))
assert not en
for f in (S/'hardware').rglob('*'):
 if f.is_file() and f.name!='nexus-style-fc.kicad_pcb':assert sha(f)==sha(O/'hardware'/f.relative_to(S/'hardware'))
out={'status':'PASS source-bound six-clearance geometry, complete physical ports and unchanged accepted USB; qualification pending','source_sha256':sha(SP),'candidate_sha256':sha(P),'invariants':inv,'untouched_original_direct_contacts_preserved':retained,'complete_components':components,'external_finite_port_proofs':portproofs,'new_via_finite_annular_entries':viaproofs,'taper_seam_proofs':taperproofs,'power_width_preservation':power,'pasted_vias_before':V.contact_summary(pa),'pasted_vias_after':V.contact_summary(pb),'new_pasted_contacts':[],'en_conductive_contacts':en,'qualification':'Exact source-bound complete replacement geometry and native connectivity are proved. Actual post-refill reference/return/mask require separate checks; no SI or manufacturing qualification.'};(O/'geometry-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['status','candidate_sha256','untouched_original_direct_contacts_preserved','pasted_vias_after']}))
