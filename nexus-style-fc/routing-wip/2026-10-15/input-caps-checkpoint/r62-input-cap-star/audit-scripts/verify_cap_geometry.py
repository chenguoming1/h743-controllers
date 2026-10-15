from pathlib import Path
import pcbnew as k,json,hashlib,sys,math,collections,importlib.util
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();P=O/'hardware/nexus-style-fc.kicad_pcb';SP=S/'hardware/nexus-style-fc.kicad_pcb';assert sha(SP)==tr['source_board_sha256'];spec=importlib.util.spec_from_file_location('V',R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
a,b=[k.LoadBoard(str(p)) for p in [SP,P]];ls=list(b.GetEnabledLayers().CuStack());uid=lambda o:o.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));removed=set(tr['removed_uuids']);moved={r['uuid'] for r in tr['moved_vias']};defs={r['uuid']:r for r in tr['added_primitives']};added=set(defs);changedpads={p['uuid'] for f in tr['footprint_changes'] for p in f['pads']};changed=removed|moved|changedpads;new=added|moved|changedpads
at={uid(x):x for x in a.GetTracks()};bt={uid(x):x for x in b.GetTracks()};ap={uid(p):p for f in a.GetFootprints() for p in f.Pads()};bp={uid(p):p for f in b.GetFootprints() for p in f.Pads()};ao={**at,**ap};objs={**bt,**bp}
def hit(a,b,c=0):
 z=k.SHAPE.Collide(a,b,c);return z[0] if isinstance(z,tuple) else bool(z)
def polygon(o,l):
 p=k.SHAPE_POLY_SET();o.TransformShapeToPolygon(p,l,0,1,k.ERROR_INSIDE);return p
def area(o):return abs(o.Area())/1e12
shapes={(u,l):o.GetEffectiveShape(l) for u,o in objs.items() for l in ls if o.IsOnLayer(l)}
def touches(u,w):return [l for l in ls if (u,l) in shapes and (w,l) in shapes and objs[u].GetBoundingBox().Intersects(objs[w].GetBoundingBox()) and hit(shapes[u,l],shapes[w,l])]
assert set(at)-set(bt)==removed and set(bt)-set(at)==added
for u,r in defs.items():
 o=objs[u];assert o.GetNetname()==r['net']
 if r['kind']=='segment':assert o.GetWidth()==round(r['width']*1e6) and b.GetLayerName(o.GetLayer())==r['layer'] and xy(o.GetStart())==tuple(round(x,6) for x in r['start']) and xy(o.GetEnd())==tuple(round(x,6) for x in r['end'])
 else:assert o.GetDrillValue()==200000 and o.GetWidth(k.F_Cu)==450000 and xy(o.GetPosition())==tuple(round(x,6) for x in r['at']) and o.GetFrontTentingMode()==k.TENTING_MODE_TENTED and o.GetBackTentingMode()==k.TENTING_MODE_TENTED
for r in tr['moved_vias']:
 x,y=at[r['uuid']],bt[r['uuid']];assert x.GetNetname()==y.GetNetname() and xy(y.GetPosition())==tuple(r['to']) and x.GetWidth(k.F_Cu)==y.GetWidth(k.F_Cu)==450000 and x.GetDrillValue()==y.GetDrillValue()==200000 and x.GetFrontTentingMode()==y.GetFrontTentingMode() and x.GetBackTentingMode()==y.GetBackTentingMode()
# Independent source contact inventory includes changed pads and moved vias.
conn=a.GetConnectivity();seen=set();retained=0;ports=collections.defaultdict(set);oldadj={u:set() for u in ao};portpairs=[]
for u,t in at.items():
 for q in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)):
  w=uid(q);q=ao[w];pair=tuple(sorted([u,w]));layers=[l for l in ls if t.IsOnLayer(l) and q.IsOnLayer(l) and hit(t.GetEffectiveShape(l),q.GetEffectiveShape(l))]
  if u==w or pair in seen or not layers or t.GetNetname()!=q.GetNetname():continue
  seen.add(pair);oldadj[u].add(w);oldadj[w].add(u)
  if u not in changed and w not in changed:assert touches(u,w),('retained contact lost',pair);retained+=1
  if u in changed and w not in changed:ports[t.GetNetname()].add(w);portpairs.append({'changed':u,'port':w})
  if w in changed and u not in changed:ports[t.GetNetname()].add(u);portpairs.append({'changed':w,'port':u})
def walk(adj,seed,removed=set()):
 seen={seed};todo=[seed]
 while todo:
  u=todo.pop()
  for w in adj[u]-seen-removed:seen.add(w);todo.append(w)
 return seen
nets=sorted({objs[u].GetNetname() for u in new});graphs={};components={};preserved=[]
for net in nets:
 ids=[u for u,o in objs.items() if o.GetNetname()==net];adj={u:set() for u in ids}
 for i,u in enumerate(ids):
  for w in ids[:i]:
   if touches(u,w):adj[u].add(w);adj[w].add(u)
 graphs[net]=adj;seeds={u for u in new if objs[u].GetNetname()==net};unseen=set(seeds);cc=[]
 while unseen:
  seed=next(iter(unseen));reach=walk(adj,seed);cc.append({'modified_objects':sorted(seeds&reach),'external_ports':sorted(ports[net]&reach),'object_count':len(reach)});unseen-=reach
 assert ports[net]<=set().union(*(set(c['external_ports']) for c in cc)),('Unconnected replacement external port',net)
 if net!='GND':assert len(cc)==1,(net,'multiple replacement components')
 components[net]=cc
 checked=set()
 for u in changed&ao.keys():
  if ao[u].GetNetname()!=net or u in checked:continue
  old=walk(oldadj,u);checked|=old;ret=old-changed
  if ret:
   reach=walk(adj,next(iter(ret)));assert ret<=reach,('original explicit component split',net,sorted(ret-reach));preserved.append({'net':net,'original_modified_members':sorted(old&changed),'retained_members':sorted(ret),'all_remain_explicitly_connected':True})
 print(net,'components',len(cc),'ports',len(ports[net]),flush=True)
# Full-width finite pad/annular entry, with a whole-land proof for the .500 mm VX feed.
def patch(t,p,l):
 if isinstance(t,k.PCB_ARC):return None
 aa,zz=xy(t.GetStart()),xy(t.GetEnd());length=math.dist(aa,zz)
 if length<1e-8:return None
 dr=((zz[0]-aa[0])/length,(zz[1]-aa[1])/length);n=(-dr[1],dr[0]);rad=t.GetWidth()/2e6;cen=xy(p.GetPosition());proj=sum((cen[i]-aa[i])*dr[i] for i in range(2));off=abs(sum((cen[i]-aa[i])*n[i] for i in range(2)))
 if isinstance(p,k.PCB_VIA) and t.GetWidth()>=p.GetWidth(l):
  # Exact centered endpoint and a conductor at least as wide as the via land cover the complete land disk.
  if cen in [aa,zz] and rad>=p.GetWidth(l)/2e6:return {'track':uid(t),'port':uid(p),'layer':b.GetLayerName(l),'kind':'entire via land disk contained in centered round-ended conductor','track_width_mm':rad*2,'land_diameter_mm':p.GetWidth(l)/1e6,'drill_mm':p.GetDrillValue()/1e6,'via_ampacity_qualification':'open'}
 for q in [proj+d for d in [0,.11,-.11,.13,-.13,.15,-.15,.18,-.18]]+[i*length/200 for i in range(1,200)]:
  if not .01<=q<=length-.01:continue
  corners=[(aa[0]+(q+s*.01)*dr[0]+c*rad*n[0],aa[1]+(q+s*.01)*dr[1]+c*rad*n[1]) for s in [-1,1] for c in [-1,1]]
  if not all(hit(p.GetEffectiveShape(l),vec(pt)) for pt in corners):continue
  dist=math.hypot(max(abs(proj-q)-.01,0),max(off-rad,0))
  if isinstance(p,k.PCB_VIA) and dist<p.GetDrillValue()/2e6+.001:continue
  return {'track':uid(t),'port':uid(p),'layer':b.GetLayerName(l),'width_mm':rad*2,'depth_mm':.02,'corners':corners}
 return None
def istrack(o):return isinstance(o,k.PCB_TRACK) and not isinstance(o,(k.PCB_VIA,k.PCB_ARC))
def edgeproof(u,w):
 p,t=objs[u],objs[w]
 if istrack(p) and isinstance(t,(k.PAD,k.PCB_VIA)):return patch(p,t,p.GetLayer())
 if istrack(t) and isinstance(p,(k.PAD,k.PCB_VIA)):return patch(t,p,t.GetLayer())
 if istrack(p) and istrack(t):
  common={xy(p.GetStart()),xy(p.GetEnd())}&{xy(t.GetStart()),xy(t.GetEnd())}
  if common:return {'tracks':[u,w],'exact_shared_centerline_endpoints':sorted(common),'widths_mm':[p.GetWidth()/1e6,t.GetWidth()/1e6]}
 return None
portproofs=[]
for net,ps in ports.items():
 adj=graphs[net]
 for u in ps:
  todo=[(u,[u],[])];seen={u};found=None
  while todo and not found:
   w,path,proofs=todo.pop(0)
   if w in new and len(path)>1:found={'port':u,'full_width_donor_path':path,'proofs':proofs};break
   for q in adj[w]-seen:
    proof=edgeproof(w,q)
    if proof:seen.add(q);todo.append((q,path+[q],proofs+[proof]))
  assert found,('unproved full-width external port',net,u);portproofs.append(found)
# Every new/moved routed via has a finite full-width entry on each incident track layer.
viaproofs=[]
for u in added|moved:
 v=objs[u]
 if not isinstance(v,k.PCB_VIA):continue
 adj=graphs[v.GetNetname()][u];layers={objs[w].GetLayer() for w in adj if istrack(objs[w])};entries=[]
 for l in layers:
  pp=[patch(objs[w],v,l) for w in adj if istrack(objs[w]) and objs[w].GetLayer()==l];pp=[p for p in pp if p];assert pp,('unproved via layer entry',u,b.GetLayerName(l));entries.append(pp[0])
 viaproofs.append({'via':u,'position':xy(v.GetPosition()),'net':v.GetNetname(),'entries':entries,'plane_only':not layers})
# All six approved footprint pads have a full-width direct track entry.
padproofs=[]
for u in changedpads:
 p=bp[u];adj=graphs[p.GetNetname()][u];pp=[patch(objs[w],p,objs[w].GetLayer()) for w in adj if istrack(objs[w])];pp=[x for x in pp if x];assert pp,('unproved approved pad entry',u);padproofs.append({'pad':u,'ref':p.GetParentFootprint().GetReference(),'pin':p.GetNumber(),'entries':pp})
# Exact physical U14 EN leaf branch cuts, without internal chip assumptions.
byname={r['proposal_id']:r['uuid'] for r in tr['added_primitives']};adj=graphs['VSYS'];en='458d23a2-b619-40f2-b619-5da363e64873';vin='d7d3757a-6321-4e24-a8d8-1bf790be155c';cap='3ecf1160-7bc3-402f-ae25-25272cc371da';cuts=[]
for role,isolated,other in [('EN_B',en,vin),('EN_inner',en,vin),('VIN_B',vin,en),('VIN_F',vin,en)]:
 rm={u for n,u in byname.items() if n.startswith(role+'/')};reach=walk(adj,isolated,rm);assert cap not in reach and other in walk(adj,cap,rm);expected={isolated}
 if role=='EN_inner':expected|={u for n,u in byname.items() if n.startswith('EN_B/') or n=='EN_via'}
 if role=='VIN_F':expected|={u for n,u in byname.items() if n.startswith('VIN_B/') or n=='VIN_via'}
 assert reach==expected,(role,reach,expected);cuts.append({'role':role,'removed':sorted(rm),'isolated_component':sorted(reach),'other_port_reaches_C27':True})
pa,pb=V.drill_paste_contacts(a),V.drill_paste_contacts(b);old={(r['via_uuid'],r['pad_uuid']) for r in pa};now={(r['via_uuid'],r['pad_uuid']) for r in pb};assert not now-old,('new pasted holes',now-old)
power=V.power_width_preservation(a,b);assert power['status']=='pass',power
pid='5f922c73-82b6-4073-8e98-d520c70499ca';p=bp[pid];assert p.GetNetname()=='unconnected-(U10-EN-Pad3)';contacts=[]
for l in ls:
 if not p.IsOnLayer(l):continue
 for u,o in objs.items():
  if u!=pid and o.IsOnLayer(l) and hit(p.GetEffectiveShape(l),o.GetEffectiveShape(l)):contacts.append(u)
 for z in b.Zones():
  if z.IsOnLayer(l) and not z.GetIsRuleArea() and hit(p.GetEffectiveShape(l),z.GetFilledPolysList(l)):contacts.append(uid(z))
assert not contacts
out={'status':'PASS complete source-bound cap-star geometry and physical ports; return/CAM qualification separate','source_sha256':sha(SP),'candidate_sha256':sha(P),'retained_direct_contacts':retained,'original_affected_component_preservation':preserved,'external_contact_inventory':portpairs,'replacement_components':components,'full_width_external_ports':portproofs,'new_moved_via_entries':viaproofs,'approved_pad_entries':padproofs,'U14_EN_VIN_branch_cut_proof':cuts,'power_width_preservation':power,'pasted_before':V.contact_summary(pa),'pasted_after':V.contact_summary(pb),'paste_contacts_after':pb,'new_pasted_contacts':[],'U10_EN_isolated':True};(O/'geometry-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['status','candidate_sha256','retained_direct_contacts','pasted_after']}))
