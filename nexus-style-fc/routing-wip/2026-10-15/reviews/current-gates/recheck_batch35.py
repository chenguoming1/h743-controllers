"""Fresh read-only board geometry review. No board mutation, save, refill or DRC."""
from pathlib import Path
import pcbnew as k,json,hashlib,math,re,heapq,collections
D=Path('/workspace/shared/nexus-boardlevel-review-recovery')
S=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/published/nexus-style-fc/routing-wip/2026-10-15/batch35/hardware/nexus-style-fc.kicad_pcb')
H='55b8508480f5fb098d0188e66229a3ab448cef8f7d6b534599da3d6637f52477'
assert hashlib.sha256(S.read_bytes()).hexdigest()==H
b=k.LoadBoard(str(S)); ls=list(b.GetEnabledLayers().CuStack()); ts={t.m_Uuid.AsString():t for t in b.GetTracks()}; ps={p.m_Uuid.AsString():p for f in b.GetFootprints() for p in f.Pads()}; allitems={**ts,**ps}; zones=[z for z in b.Zones() if z.GetNetname()=='GND' and not z.GetIsRuleArea()]
xy=lambda p:[p.x/1e6,p.y/1e6]
v=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6))
uid=lambda t:t.m_Uuid.AsString()
def desc(t):
 r={'uuid':uid(t),'net':t.GetNetname(),'layers':[b.GetLayerName(l) for l in ls if t.IsOnLayer(l)]}
 if isinstance(t,k.PAD):r.update(kind='pad',ref=t.GetParentFootprint().GetReference(),value=t.GetParentFootprint().GetValue(),pin=t.GetNumber(),at=xy(t.GetPosition()),size=xy(t.GetSize()),drill=xy(t.GetDrillSize()),plated=t.GetAttribute()==k.PAD_ATTRIB_PTH)
 elif isinstance(t,k.PCB_VIA):r.update(kind='via',at=xy(t.GetPosition()),diameter=t.GetWidth(k.F_Cu)/1e6,drill=t.GetDrillValue()/1e6)
 else:r.update(kind='track',start=xy(t.GetStart()),end=xy(t.GetEnd()),width=t.GetWidth()/1e6,length_mm=t.GetLength()/1e6)
 return r
def shape(t,l):
 if isinstance(t,k.PAD):return t.GetEffectiveShape(l)
 if isinstance(t,k.PCB_VIA):return k.SHAPE_CIRCLE(t.GetPosition(),t.GetWidth(l)//2)
 assert not isinstance(t,k.PCB_ARC)
 return k.SHAPE_SEGMENT(t.GetStart(),t.GetEnd(),t.GetWidth())
def contacts(t):
 out=[]
 for z in zones:
  l=z.GetLayer()
  if t.IsOnLayer(l):
   q=z.GetFilledPolysList(l);out.append({'layer':b.GetLayerName(l),'polygon_count':q.OutlineCount(),'center_polygon_ids':[i for i in range(q.OutlineCount()) if q.Contains(t.GetPosition(),i)],'copper_intersects_fill':bool(k.SHAPE.Collide(q,shape(t,l),0)),'zone_connection_mode':int(z.GetPadConnection()),'spoke_mm':z.GetThermalReliefSpokeWidth()/1e6,'clearance_mm':z.GetLocalClearance()/1e6})
 return out
parts=[desc(p) for f in b.GetFootprints() if f.GetReference() in ['U10','C18','C19','U7','C28','D5','D6'] for p in f.Pads()]
groups={
 'U10_output':['a287c7d5-a48b-4d29-a5ef-c7be54d3702b','bdbe0053-df2f-430f-a388-8d2015ab70ec','d48d609d-0488-42cd-bd70-535e343fc803','27961961-aebc-4e21-abce-c170061b0970','379803c4-3c43-4a54-afe8-1aabe6e556c7','f9d03d4c-6fc9-491c-940f-232766770f8c'],
 'U10_input':['16764742-6246-471b-b23f-55a089d3fc36','382c42bd-28db-4867-8a39-e01afa8fc026','54aabec8-33dc-4725-92db-c353e1612ad5','561575cf-f2d6-4ff8-b3ef-d1a67c206cec'],
 'U7_ground':['d64afead-6ea6-45a2-811b-5a466b437dc3','9be8b8df-854c-4dcf-9628-47a6ecc05b08','d0198785-0d5c-45ac-81d2-dd48da876dab','48fbbdf8-48ac-4023-b4bb-4f0111a49d35'],
 'USB_ground_donor':['f3b26300-209a-441a-b917-158227e4afba']}
assert all(u in ts for ids in groups.values() for u in ids)
groupdata={n:{'items':[desc(ts[u]) for u in ids],'planar_length_mm':sum(ts[u].GetLength()/1e6 for u in ids if not isinstance(ts[u],k.PCB_VIA))} for n,ids in groups.items()}
# Historical coordinates preserved in authored conversation; this is not the missing proposal file.
paths=[{'name':'U10_output_F','net':'3V3_SENS','layer':'F.Cu','width':.25,'points':[[108.45,105.9],[108.45,106.5],[107.895,107.055],[107.895,108.95],[108.625,109.8]]},
 {'name':'U10_input_F','net':'VSYS','layer':'F.Cu','width':.25,'points':[[108.45,108.2],[108.45,107.65],[108.925,107.35]]},
 {'name':'U10_input_B','net':'VSYS','layer':'B.Cu','width':.25,'points':[[108.925,107.35],[107.728574,105.820545]]},
 {'name':'USB_ground_B','net':'GND','layer':'B.Cu','width':.127,'points':[[106,125.834],[106.775,125.975]]},
 {'name':'USB_ground_F','net':'GND','layer':'F.Cu','width':.127,'points':[[106.775,125.975],[106,127.65]]},
 {'name':'USB_VBUS_B','net':'VBUS','layer':'B.Cu','width':.25,'points':[[103.966,127.98],[104.5,126.8],[107.1,126.8],[107.56,127],[107.53,127.85],[108.4,128.7]]},
 {'name':'rejected_outer_input','net':'VSYS','layer':'F.Cu','width':.25,'points':[[108.45,108.2],[108.45,107.65],[108.95,107.2],[108.95,105.04],[108.15,105.04],[107.991,105.096],[107.771,105.316],[107.728574,105.820545]]}]
for p in paths:p['length_mm']=sum(math.dist(a,e) for a,e in zip(p['points'],p['points'][1:]))
# Existing endpoint graph only; no new-path routing search. All layer transitions through source vias.
def existing_path(net,ref1,pin1,ref2,pin2):
 adj=collections.defaultdict(list)
 def node(p,l):return(p.x,p.y,int(l))
 for t in ts.values():
  if t.GetNetname()!=net:continue
  if isinstance(t,k.PCB_VIA):
   ns=[node(t.GetPosition(),l) for l in ls if t.IsOnLayer(l)]
   for a,e in zip(ns,ns[1:]):adj[a].append((e,0,uid(t)));adj[e].append((a,0,uid(t)))
  else:
   a,e=node(t.GetStart(),t.GetLayer()),node(t.GetEnd(),t.GetLayer());adj[a].append((e,t.GetLength()/1e6,uid(t)));adj[e].append((a,t.GetLength()/1e6,uid(t)))
 def pad(ref,pin):return next(p for p in ps.values() if p.GetParentFootprint().GetReference()==ref and p.GetNumber()==pin)
 a0,e0=pad(ref1,pin1),pad(ref2,pin2);starts=[node(a0.GetPosition(),l) for l in ls if a0.IsOnLayer(l)];ends={node(e0.GetPosition(),l) for l in ls if e0.IsOnLayer(l)};heap=[(0,n,[]) for n in starts];seen=set()
 while heap:
  cost,n,path=heapq.heappop(heap)
  if n in seen:continue
  seen.add(n)
  if n in ends:return {'planar_length_mm':cost,'item_uuids':path,'track_items':[desc(ts[u]) for u in path if not isinstance(ts[u],k.PCB_VIA)]}
  for nn,w,u in adj[n]:heapq.heappush(heap,(cost+w,nn,path+[u]))
 return {'status':'No exact-endpoint path; not evidence of an electrical open.'}
inputpath=existing_path('VSYS','C18','1','U10','1');groundpath=existing_path('GND','C19','2','U10','2')
serial_ids=['abb6d92c-fe4d-4098-9639-a5176a79b8cf','7050ad6f-9636-4133-ba0b-11f6e38331d3','4d573730-8312-45a6-a98e-3d8cfed2019b','e0ea22eb-7130-400d-9532-cf8cdccb26c6','20c92583-f061-4cfc-9cd0-70d5d54fc129','2122ed59-e6e7-4653-a9f1-b199de5811a2','a85b7648-2f13-44d9-af39-35e11cb35d4a','79c2d0d0-a175-4560-bfe6-3ff9a505332c','d0b3f615-e8ef-477f-a373-dfa08c81d05b','4ddde9b9-0a61-4774-8248-8928b07a2441','3841d624-65e7-4456-a4dd-6d947d586701','372f5df5-cbd1-44bd-bc7c-c369fcd0e6f9','ce0c83ec-dabe-41bb-a4f2-460dd49ca91c','54aabec8-33dc-4725-92db-c353e1612ad5','382c42bd-28db-4867-8a39-e01afa8fc026','561575cf-f2d6-4ff8-b3ef-d1a67c206cec','16764742-6246-471b-b23f-55a089d3fc36']
serial_items=[ts[u] for u in serial_ids];c18=next(p for p in ps.values() if p.GetParentFootprint().GetReference()=='C18' and p.GetNumber()=='1');inp=next(p for p in ps.values() if p.GetParentFootprint().GetReference()=='U10' and p.GetNumber()=='1');chain=[c18]+serial_items+[inp];contact_edges=[]
for a,e in zip(chain,chain[1:]):
 common=[l for l in ls if a.IsOnLayer(l) and e.IsOnLayer(l) and k.SHAPE.Collide(shape(a,l),shape(e,l),0)]
 contact_edges.append({'a':uid(a),'b':uid(e),'physical_contact_layers':[b.GetLayerName(l) for l in common]})
 assert common,('serial contact absent',uid(a),uid(e))
serial={'track_count':sum(not isinstance(t,k.PCB_VIA) for t in serial_items),'planar_track_length_sum_mm':sum(t.GetLength()/1e6 for t in serial_items if not isinstance(t,k.PCB_VIA)),'items':[desc(t) for t in serial_items],'physical_contact_edges':contact_edges,'limit':'Sum of complete centerline segments including entry overlap within C18 pad; not a pad-center-to-pad-center impedance length.'}

portids=['34005548-97c7-42f4-9c78-119e53803953','c189d3e3-eabe-4e49-804a-4f0944dcadfe','52feebb2-f8a6-4a9f-85d1-cf662039237e']+[uid(p) for p in ps.values() if p.GetParentFootprint().GetReference()=='J6' and p.GetNumber()=='EP']
ports=[dict(desc(allitems[u]),stored_fill_contacts=contacts(allitems[u])) for u in portids]
via=ts['c189d3e3-eabe-4e49-804a-4f0944dcadfe'];tr=ts['48fbbdf8-48ac-4023-b4bb-4f0111a49d35'];direct=bool(k.SHAPE.Collide(shape(via,k.B_Cu),shape(tr,k.B_Cu),0))
spokes=[]
for p in ps.values():
 if p.GetParentFootprint().GetReference()!='J6' or p.GetNumber()!='EP':continue
 x,y=xy(p.GetPosition())
 for z in zones:
  if z.GetLayer() not in [k.In1_Cu,k.In4_Cu]:continue
  q=z.GetFilledPolysList(z.GetLayer());r={'pad_uuid':uid(p),'at':[x,y],'layer':b.GetLayerName(z.GetLayer()),'stations':[]}
  for name,dx,dy,tx,ty in [('N',0,-.65,1,0),('S',0,.65,1,0),('W',-.775,0,0,1),('E',.775,0,0,1)]:
   cx,cy=x+dx,y+dy
   def hit(off):return q.Contains(v([cx+off*tx,cy+off*ty]))
   lo=hi=0
   if hit(0):
    while lo>-.4 and hit(lo-.001):lo-=.001
    while hi<.4 and hit(hi+.001):hi+=.001
   dist=math.dist([cx,cy],[107.02,127.32]);r['stations'].append({'side':name,'station':[cx,cy],'filled_span_lower_bound_mm':round(hi-lo,3),'moved_CC1_distance_mm':dist,'inside_analytical_CC1_zone_antipad':dist<.225+z.GetLocalClearance()/1e6})
  spokes.append(r)
# Fresh scoped candidate shape checks; EN set is validated item-by-item against durable source.
EN=['e8add440-829f-45c7-bbaa-d799f64a4715','47066852-29e6-485d-86e9-9371d82f7556','de7e52a3-518a-4940-9b9e-4db1e1631026','3ce30b5f-5db3-47b8-8601-f7afbc1acfb3','0fbc0aaa-49d7-414a-8e6c-4c09758c504b','ca8105b2-021f-4f94-b576-04539450aef8','d5ccf428-2b7a-430c-95f3-c8a70489dc8c','5bfef2a9-df8d-401b-86ff-7f44eacf4385','9344bd41-8f85-4a73-b389-76a10385ad42','ff63ffe7-401a-4c92-84ed-4055a252d381'];assert all(u in ts and ts[u].GetNetname()=='VSYS' for u in EN)
remove=set(EN+groups['U10_output']+groups['U10_input']);checks=[]
for pp in [paths[0],paths[-1]]:
 segs=[k.SHAPE_SEGMENT(v(a),v(e),250000) for a,e in zip(pp['points'],pp['points'][1:])];near=[]
 for u,t in allitems.items():
  if u in remove or not t.IsOnLayer(k.F_Cu) or (t.GetNetname()==pp['net'] and u!='5f922c73-82b6-4073-8e98-d520c70499ca'):continue
  ss=shape(t,k.F_Cu)
  if not any(k.SHAPE.Collide(s,ss,300000) for s in segs):continue
  lo=0;hi=300000
  if any(k.SHAPE.Collide(s,ss,0) for s in segs):gap=-1
  else:
   while hi-lo>1:
    mid=(lo+hi)//2
    if any(k.SHAPE.Collide(s,ss,mid) for s in segs):hi=mid
    else:lo=mid
   gap=hi/1e6
  near.append({'gap_mm':gap,'item':desc(t)})
 checks.append({'name':pp['name'],'near_foreign_copper':sorted(near,key=lambda r:r['gap_mm'])})
projection=[]
for pp in paths[:3]:
 layer=k.In1_Cu if pp['layer']=='F.Cu' else k.In4_Cu;z=next(z for z in zones if z.GetLayer()==layer);q=z.GetFilledPolysList(layer);tot=good=0
 for a,e in zip(pp['points'],pp['points'][1:]):
  n=math.ceil(math.dist(a,e)/.01)
  for i in range(n+1):
   point=[a[j]+(e[j]-a[j])*i/n for j in range(2)];tot+=1;good+=bool(q.Contains(v(point)))
 projection.append({'name':pp['name'],'reference':b.GetLayerName(layer),'sample_count':tot,'covered_samples':good,'coverage_fraction':good/tot})
stacktext=S.read_text().split('(stackup',1)[1].split('(copper_finish',1)[0];st=[{'layer':m[0],'thickness_mm':float(m[1])} for m in re.findall(r'\(layer "([^"]+)"\s+\(type "[^"]+"\)\s+\(thickness ([0-9.]+)\)',stacktext) if m[0].endswith('.Cu') or m[0].startswith('dielectric')]
zpos={};depth=0
for r in st:
 if r['layer'].endswith('.Cu'):zpos[r['layer']]=depth+r['thickness_mm']/2
 depth+=r['thickness_mm']
res={'evidence_class':'NEW read-only recomputation against exact recovered batch35; not restored historical receipts','source':str(S),'source_sha256':H,'native_version':k.GetBuildVersion(),'review_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'parts':parts,'existing_groups':groupdata,'C18_to_U10_existing_endpoint_path':inputpath,'C18_serial_track_chain':serial,'C19_to_U10_GND_existing_endpoint_path':groundpath,'historical_waypoint_parameters':paths,'waypoint_provenance':'Explicit authored earlier conversation. Original complete proposal JSON absent; these subsets must not be treated as accepted complete transactions.','GND_ports':ports,'U7_retained_track_via_direct_contact':direct,'U7_pad_center_to_via_projection_route_mm':sum(ts[u].GetLength()/1e6 for u in groups['U7_ground'][:3])+.216,'U7_via_lateral_centerline_offset_mm':.141,'shield_spokes':spokes,'hypothetical_EN_cut_source_items':[desc(ts[u]) for u in EN],'hypothetical_removed_U10_item_uuids':sorted(remove),'scoped_candidate_checks':checks,'stored_projection_samples':projection,'source_stack':st,'copper_center_z_mm':zpos,'limits':['No board mutation, save, refill, DRC, route search or heavy solver.','Stored fill only. No prediction of final refill topology.','Existing endpoint path length is not impedance or transient qualification.','No complete USB proposed transaction was reconstructed or validated.']}
assert hashlib.sha256(S.read_bytes()).hexdigest()==H
(D/'fresh-batch35-geometry.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps({'source_sha256':H,'U10_output_planar_mm':groupdata['U10_output']['planar_length_mm'],'U10_input_planar_mm':groupdata['U10_input']['planar_length_mm'],'C18_serial_track_sum_mm':serial['planar_track_length_sum_mm'],'C19_ground_mm':groundpath.get('planar_length_mm'),'U7_via_direct':direct,'projection':projection,'candidate_min_gaps':[(r['name'],r['near_foreign_copper'][0]['gap_mm']) for r in checks]},indent=2))
