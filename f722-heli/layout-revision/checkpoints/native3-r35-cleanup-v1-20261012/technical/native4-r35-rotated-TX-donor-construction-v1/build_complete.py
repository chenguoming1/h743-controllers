"""Non-executing source excerpts. See SOURCE-PROVENANCE.json for original identity.
Dependencies belong to the original implementation; use reproduction/replay_native.py
for the standalone verifier and exact sealed-recipe replay.
"""

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def phase(s):
 global PHASE
 assert __import__('shutil').disk_usage(ROOT).free>=64*1024**2,'64 MiB disk reserve required'
 PHASE=s
 if (ROOT/'stop-requested').exists():raise TimeoutError('Cooperative stop requested')
 print(json.dumps({'phase':s,'elapsed_seconds':time.monotonic()-START}),flush=True)

def timeout(*_):raise TimeoutError('180 second total construction bound')

def save(name,v,binary=False):
 global WRITTEN
 data=v if binary else (json.dumps(v,separators=(',',':'),allow_nan=False)+'\n').encode();assert WRITTEN+len(data)<=8*1024**2
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(data);WRITTEN+=len(data)

def q(v):return float((Decimal(str(v))*1000000).quantize(Decimal(1),rounding=ROUND_HALF_EVEN)/1000000)

def poly(ps):return unary_union([Polygon(p['outer'],p.get('holes',[])) for p in ps])

def ps(g):return [{'outer':[list(p) for p in g.exterior.coords],'holes':[[list(p) for p in r.coords] for r in g.interiors]}]

def polygons(g):return [] if g.is_empty else [g] if g.geom_type=='Polygon' else [p for p in g.geoms if p.geom_type=='Polygon' and not p.is_empty]

def buf(g,r,via=False):return g.buffer(r*(VFACTOR if via else FACTOR),quad_segs=16 if via else 64)

def native_shape(o,l):
 if o['kind']=='track':return buf(LineString([o['start'],o['end']]),o['width']/2+EPS)
 if o['kind']=='via':return buf(Point(o['xy']),o['width_by_layer'][l]/2+EPS,True)
 return poly(o['copper'][l])

def digest(o):return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def load_defs(path,names,env):
 tree=ast.parse(Path(path).read_text());fs=[f for f in tree.body if isinstance(f,ast.FunctionDef) and f.name in names];assert {f.name for f in fs}==set(names);exec(compile(ast.Module(body=fs,type_ignores=[]),str(path),'exec'),env)

def group_for(groups,key):return next(g for g in groups if key in g['pads'])

def model_track(t):
 return {**t,'width_by_layer':{t['layer']:t['width']},'copper':{t['layer']:ps(buf(LineString([t['start'],t['end']]),t['width']/2+EPS))}}

def model_via(v,layers):
 land=ps(buf(Point(v['xy']),.225+EPS,True));hole=ps(buf(Point(v['xy']),.1+EPS,True))
 return {**v,'width':.45,'width_by_layer':{l:.45 for l in layers},'copper':{l:land for l in layers},'drill':{'start':v['xy'],'end':v['xy'],'width':.2,'outside':hole}}

def body_shapes(native):
 result=[]
 for f in native['footprints']:
  for l in ['F.Fab','B.Fab']:
   gs=[];lines=[]
   for g in f['graphics']:
    if g['layer']!=l:continue
    if g['shape']=='Line':lines.append(LineString([g['start'],g['end']]))
    elif g['shape'] in ['Rect','Rectangle']:
     a,b=g['start'],g['end'];gs.append(box(min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])))
    elif g.get('polygons'):gs.append(poly(g['polygons']))
   gs+=list(polygonize(unary_union(lines)));body=unary_union(gs)
   if not body.is_empty:result.append((f['ref'],l,body))
 return result

def body_flags(native,xy):
 land=Point(xy).buffer(.225,quad_segs=128)
 return [{'ref':r,'layer':l,'land_body_overlap_mm2':land.intersection(g).area} for r,l,g in body_shapes(native) if g.intersects(land)]

def route(native,net,source_key,target_key,forced_site=None,actual_io_key=None,width=.127,allowed_layers=None):
 global HALF,LAYERS
 HALF=width/2;LAYERS=['F.Cu','In2.Cu','In3.Cu','B.Cu']
 phase('route '+net);obs={o['uuid']:o for o in native['objects']};own={u:o for u,o in obs.items() if o['net']==net};before,_=contacts_env['graph'](own)
 groups={'S':group_for(before['groups'],source_key),'T':group_for(before['groups'],target_key)};assert groups['S'] is not groups['T'] and set(groups['S']['records']+groups['T']['records'])==set(own)
 io=next((o for o in own.values() if o.get('key')==actual_io_key),None) if actual_io_key else None;io_cut=poly(io['inside']['B.Cu']) if io else None;io_inside=io_cut.buffer(-HALF) if io else None
 connector={}
 if io:
  for u in groups['S']['records']:
   if u==io['uuid']:continue
   for l in own[u]['copper']:connector.setdefault(l,[]).append(native_shape(own[u],l))
  connector={l:unary_union(gs).difference(io_cut) if l=='B.Cu' else unary_union(gs) for l,gs in connector.items()}
 outline=poly(native['outline_with_npth']['polygons']);foreign={u:{l:native_shape(o,l) for l in o['copper']} for u,o in obs.items() if o['net']!=net};holes=[(o,poly(o['drill']['outside'])) for o in obs.values() if o.get('drill')];masks=[(o['uuid'],poly(m['polygons'])) for o in obs.values() for m in o.get('mask',{}).values() if m.get('polygons')];rules=[(z,poly(z['outline'])) for z in native['zones'] if z['rule']]
 frees={};comps={};members={};guards={}
 for l in LAYERS:
  phase(net+' free '+l);rs=[(buf(gs[l],.127+HALF),u) for u,gs in foreign.items() if l in gs]
  rs +=[(buf(g,.254+HALF),o['uuid']+':NPTH') for o,g in holes if o.get('npth')]
  rs +=[(buf(g,HALF),z['uuid']+':rule') for z,g in rules if l in z['layers'] and(z['forbid']['copper'] or z['forbid']['tracks'])]
  if l in connector:
   cg=buf(connector[l],.127+HALF);rs.append((cg.difference(io_inside) if l=='B.Cu' else cg,'retained-connector-outside-actual-IO'))
  free=outline.buffer(-(.254+HALF)).difference(unary_union([g for g,_ in rs]));assert free.is_valid;frees[l]=free;guards[l]=rs;members[l]=[]
  for i,c in enumerate(sorted(polygons(free),key=lambda c:(-c.area,c.bounds))):k=l+':'+str(i);comps[k]=c;members[l].append(k)
 points={'S':{'xy':next(o['xy'] for o in own.values() if o.get('key')==source_key),'new_via':False,'allowed_layers':[]},'T':{'xy':next(o['xy'] for o in own.values() if o.get('key')==target_key),'new_via':False,'allowed_layers':[]}}
 for label,g in groups.items():
  gg={'records':[io['uuid']],'pads':[actual_io_key]} if io and label=='S' else g
  rows=supported_contacts(own,gg,comps,members)
  assert rows,(net,label,'No supported physical terminal access')
  for i,row in enumerate(rows):points[label+'-contact-'+str(i)]={**row,'terminal_group':label}
 # Exact all-layer process domain, using fresh moved-pad masks and held first route.
 gs=[];seen=set()
 for shapes in foreign.values():
  for g in shapes.values():
   if g.wkb not in seen:seen.add(g.wkb);gs.append(buf(g,.225+.127,True))
 gs +=[buf(g,.225+.127,True) for g in connector.values()]
 gs +=[buf(g,.1+.25,True) for _,g in holes]+[buf(g,.1+.2,True) for _,g in masks]
 gs +=[buf(g,.225+.254,True) for o,g in holes if o.get('npth')]
 gs +=[buf(g,.225,True) for z,g in rules if z['forbid']['copper'] or z['forbid']['vias']]
 domain=outline.buffer(-(.225+.254)).difference(unary_union(gs));assert domain.is_valid
 if forced_site:
  assert domain.covers(Point(forced_site)),('Bound MCU transition rejected',forced_site);points['bound-MCU-via']={'xy':forced_site,'new_via':True,'assembly_unresolved':bool(body_flags(native,forced_site))}
 else:
  bodyguard=unary_union([buf(g,.225,True) for _,_,g in body_shapes(native)])
  for i,w in enumerate(sorted(polygons(domain),key=lambda g:(-g.area,g.bounds))):
   if w.area<1e-8:continue
   clear=sorted(polygons(w.difference(bodyguard)),key=lambda g:-g.area);candidate=clear[0] if clear else w
   p=polylabel(candidate,tolerance=.001);xy=[q(p.x),q(p.y)]
   if not candidate.covers(Point(xy)):continue
   points['window-'+str(i)]={'xy':xy,'new_via':True,'window':i,'assembly_unresolved':not bool(clear)}
 memberships,fullgraph=make_graph(points,members,comps);modes=[allowed_layers,LAYERS] if allowed_layers else [LAYERS];mode_results=[]
 for selected_layers in modes:
  graph={a:[e for e in edges if e[1].startswith('actual-fixed-') or e[1].split(':')[0] in selected_layers] for a,edges in fullgraph.items()};best,path=finite_path(points,graph,'S','T');mode_results.append({'routing_layers':selected_layers,'connected':bool(path)})
  if path:break
 summary={'net':net,'source_groups':groups,'points':points,'memberships':memberships,'graph':dict(graph),'path':path,'connected':bool(path),'bounded_layer_modes':mode_results};save(ATTEMPT+'/'+net+'/graph.json',summary)
 if not path:
  save(ATTEMPT+'/'+net+'/result.json',{'complete':False,'status':'FINITE_GRAPH_DISCONNECTED','scope':'Only this frozen geometry and finite ordinary transition set'});return None
 raw=[]
 for i,e in enumerate(path):
  if e['component'].startswith('actual-fixed-'):continue
  phase(net+' path '+str(i));line,_,_=component_polyline(comps[e['component']],points[e['from']]['xy'],points[e['to']]['xy']);raw.append({'layer':e['component'].split(':')[0],'points':line})
 used={e[k] for e in path for k in ['from','to']};vias=[];tracks=[]
 for i,row in enumerate(raw):
  pts=[[q(x),q(y)] for x,y in row['points']]
  assert all(a!=b and frees[row['layer']].covers(LineString([a,b])) for a,b in zip(pts,pts[1:]))
  for j,(a,b) in enumerate(zip(pts,pts[1:])):tracks.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'native4-R35-rotated-TX-donors-v1:'+ATTEMPT+':'+net+':'+str((i,j)))),'kind':'track','net':net,'layer':row['layer'],'width':width,'start':a,'end':b})
 for label in sorted(used):
  if points[label]['new_via']:
   xy=points[label]['xy'];assert domain.covers(Point(xy));vias.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'native4-R35-rotated-TX-donors-v1:'+ATTEMPT+':'+net+':via:'+label)),'kind':'via','net':net,'xy':xy,'diameter':.45,'drill':.2,'layers':native['copper_layers'],'type':'through','tented':{'F.Mask':True,'B.Mask':True}})
 assert all(math.dist(a['xy'],b['xy'])>=.45 for i,a in enumerate(vias) for b in vias[:i])
 joined=dict(own);joined.update({t['uuid']:{**t,'proposed':True} for t in tracks});joined.update({v['uuid']:model_via(v,native['copper_layers']) for v in vias});after,_=contacts_env['graph'](joined);assert len(after['groups'])==1 and after['groups'][0]['pads']==sorted(groups['S']['pads']+groups['T']['pads'])
 ioproof=None
 if io:
  protected={}
  for u in groups['T']['records']:
   for l in own[u]['copper']:protected.setdefault(l,[]).append(native_shape(own[u],l))
  for t in tracks:protected.setdefault(t['layer'],[]).append(buf(LineString([t['start'],t['end']]),HALF+EPS))
  for v in vias:
   for l in native['copper_layers']:protected.setdefault(l,[]).append(buf(Point(v['xy']),.225+EPS,True))
  outside={l:unary_union(g).difference(io_cut) if l=='B.Cu' else unary_union(g) for l,g in protected.items()};gaps={l:g.distance(connector[l]) for l,g in outside.items() if l in connector and not connector[l].is_empty};assert gaps and all(g>=.127 for g in gaps.values()),('Outside actual IO separation',gaps)
  ioproof={'IO':actual_io_key,'connector':'J11.2','protected_terminal':'R35.1','outside_gaps_mm':gaps,'actual_IO_cut_required_native':True,'no_NC_internal_continuity':True}
 result={'complete':True,'net':net,'width_mm':width,'new_via_count':len(vias),'minimum_new_track_width_mm':min(t['width'] for t in tracks),'permitted_new_routing_layers':selected_layers,'retained_terminal_groups':groups,'add_tracks':tracks,'add_vias':vias,'used_site_body_flags':[{'uuid':v['uuid'],'xy':v['xy'],'flags':body_flags(native,v['xy'])} for v in vias],'raw_paths':raw,'contact_graph':after,'actual_IO_proof':ioproof,'new_length_mm':sum(math.dist(t['start'],t['end']) for t in tracks),'native_all_contacts_and_assembly_reference_pending':True};save(ATTEMPT+'/'+net+'/result.json',result)
 return result
