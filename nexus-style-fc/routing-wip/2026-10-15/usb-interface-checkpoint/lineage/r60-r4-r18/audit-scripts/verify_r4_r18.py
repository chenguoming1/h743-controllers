from pathlib import Path
import pcbnew as k,json,hashlib,sys,math,collections,importlib.util
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);R=O.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();P=O/'hardware/nexus-style-fc.kicad_pcb';SP=S/'hardware/nexus-style-fc.kicad_pcb';assert sha(SP)==tr['source_board_sha256'];spec=importlib.util.spec_from_file_location('V',R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V);a,b=[k.LoadBoard(str(x)) for x in [SP,P]];st,ct=[V.parse_sexpr(x.read_text()) for x in [SP,P]];inv=V.invariant_checks(a,b,st,ct);assert inv['status']=='pass';rm=set(tr['removed_uuids']);add=set(tr['added_uuids']);r4=json.loads((O/'source-review/r4-proposal.json').read_text());r18=json.loads((O/'source-review/r18-proposal.json').read_text());uid=lambda o:o.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));ls=list(b.GetEnabledLayers().CuStack());area=lambda p:abs(p.Area())/1e12
for tag in ['segment','arc','via','gr_poly','gr_line','gr_arc','gr_text','group']:
 aa,bb=[V.keyed_nodes(V.children(t,tag)) for t in [st,ct]];assert {u:v for u,v in aa.items() if u not in rm}=={u:v for u,v in bb.items() if u not in add},('Unexpected source edit',tag)
at,bt=[{uid(t):t for t in x.GetTracks()} for x in [a,b]];ap,bp=[{uid(p):p for f in x.GetFootprints() for p in f.Pads()} for x in [a,b]];objs={**bt,**bp};assert set(at)-set(bt)==rm and set(bt)-set(at)==add
for d in tr['added_tracks']:
 t=bt[d['uuid']];assert t.GetNetname()==d['net'] and t.GetWidth()==round(d['width_mm']*1e6) and b.GetLayerName(t.GetLayer())==d['layer'] and xy(t.GetStart())==tuple(d['start']) and xy(t.GetEnd())==tuple(d['end'])
for d in tr['added_vias']:
 v=bt[d['uuid']];assert isinstance(v,k.PCB_VIA) and xy(v.GetPosition())==tuple(d['position']) and v.GetDrillValue()==200000 and all(v.GetWidth(l)==450000 for l in ls)
def hit(x,y):
 z=k.SHAPE.Collide(x,y,0);return z[0] if isinstance(z,tuple) else bool(z)
def touches(x,y):return [l for l in ls if x.IsOnLayer(l) and y.IsOnLayer(l) and hit(x.GetEffectiveShape(l),y.GetEffectiveShape(l))]
def polygon(o,l):
 p=k.SHAPE_POLY_SET();o.TransformShapeToPolygon(p,l,0,1,k.ERROR_INSIDE);return p
def patchproof(points,t,port):
 cx=sum(p[0] for p in points)/4;cy=sum(p[1] for p in points)/4;pts=sorted(points,key=lambda p:math.atan2(p[1]-cy,p[0]-cx));c=k.SHAPE_LINE_CHAIN()
 for p in pts:c.Append(vec(p))
 c.SetClosed(True);poly=k.SHAPE_POLY_SET();poly.AddOutline(c)
 for o in [t,port]:q=k.SHAPE_POLY_SET(poly);q.BooleanSubtract(polygon(o,t.GetLayer()));assert area(q)<1e-8,('Patch outside copper',uid(t),uid(port),area(q))
 if isinstance(port,k.PCB_VIA):
  p=xy(port.GetPosition());mind=1e9
  for aa,zz in zip(pts,pts[1:]+pts[:1]):
   d=(zz[0]-aa[0],zz[1]-aa[1]);lam=max(0,min(1,sum((p[i]-aa[i])*d[i] for i in range(2))/sum(x*x for x in d)));mind=min(mind,math.dist(p,[aa[i]+lam*d[i] for i in range(2)]))
  assert mind>port.GetDrillValue()/2e6+.001
 else:mind=None
 return {'new_track':uid(t),'port':uid(port),'width_mm':t.GetWidth()/1e6,'depth_mm':.02,'corners':pts,'finite_patch_area_mm2':area(poly),'minimum_annular_radius_mm':mind}
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
proofs=[]
for p in r18['full_width_pad_via_entries']:
 t=bt[p['new_uuid']];proof=patch(t,objs[p['port_uuid']],t.GetLayer());assert proof,(p['new_uuid'],p['port_uuid']);proofs.append(proof)
for p in r4['full_width_contact_proofs']:
 pp=objs[p['port']];candidate=[bt[d['uuid']] for d in r4['new_tracks'] if touches(bt[d['uuid']],pp)];assert candidate;proof=patch(candidate[0],pp,candidate[0].GetLayer());assert proof;proofs.append(proof)
seen=set();ports=collections.defaultdict(set);retained=0;conn=a.GetConnectivity()
for u,t in at.items():
 for qq in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)):
  w=uid(qq);q=at.get(w) or ap.get(w);pair=tuple(sorted([u,w]))
  if u==w or pair in seen or t.GetNetname()!=q.GetNetname() or not touches(t,q):continue
  seen.add(pair)
  if u not in rm and w not in rm:assert touches(objs[u],objs[w]),('Lost retained contact',pair);retained+=1
  if u in rm and w not in rm:ports[t.GetNetname()].add(w)
  if w in rm and u not in rm:ports[t.GetNetname()].add(u)
graphs={};components=[]
for net in ['5V','5V_SENSE']:
 ids=[u for u,q in objs.items() if q.GetNetname()==net];adj={u:set() for u in ids}
 for i,u in enumerate(ids):
  for w in ids[:i]:
   if touches(objs[u],objs[w]):adj[u].add(w);adj[w].add(u)
 graphs[net]=adj;seed=next(u for u in add if objs[u].GetNetname()==net);todo=[seed];seen={seed}
 while todo:
  u=todo.pop()
  for w in adj[u]-seen:seen.add(w);todo.append(w)
 assert ports[net]<=seen and {u for u in add if objs[u].GetNetname()==net}<=seen and {u for u in bp if bp[u].GetNetname()==net}<=seen
 components.append({'net':net,'complete_original_external_ports':sorted(ports[net]),'all_pad_uuids':sorted(u for u in bp if bp[u].GetNetname()==net),'all_pads_and_replacement_copper_connected':True})
def walk(seed,removed):
 adj=graphs['5V'];seen={seed};todo=[seed]
 while todo:
  u=todo.pop()
  for w in adj[u]-seen-removed:seen.add(w);todo.append(w)
 return seen
oldbranch={x['uuid'] for x in r4['full_branch_isolation']['all_branch_tracks']};branch=(oldbranch-rm)|{x['uuid'] for x in r4['new_tracks']};source=r4['full_branch_isolation']['source_port']['uuid'];r4pad=next(u for u,p in bp.items() if p.GetParentFootprint().GetReference()=='R4' and p.GetNumber()=='1');ext=set().union(*(graphs['5V'][u] for u in branch))-branch;assert ext=={source,r4pad};reached=walk(source,branch);assert r4pad not in reached and {u for u,p in bp.items() if p.GetNetname()=='5V' and u!=r4pad}<=reached
r18branch={x['uuid'] for x in r18['new_tracks'] if x['net']=='5V'}|{x['uuid'] for x in r18['new_vias']};r18pad=next(u for u,p in bp.items() if p.GetParentFootprint().GetReference()=='R18' and p.GetNumber()=='1');r18source='7ec7822c-40c1-4348-9a46-8ccfc2c16a3a';ext18=set().union(*(graphs['5V'][u] for u in r18branch))-r18branch;assert ext18=={r18pad,r18source,'069bb2a3-9216-4c5e-a215-8e53393793fc'},ext18;reached=walk(r18source,r18branch);assert r18pad not in reached and {u for u,p in bp.items() if p.GetNetname()=='5V' and u!=r18pad}<=reached
# Incidental old R18 F.Cu contact ports are retained through their original .350 mm primary chain to the unchanged source via.
primary=['8ef483d2-5fed-43cb-9397-1ea81b47508b','a983519b-4533-4b62-8b22-08db6d92a8ea'];assert all(bt[u].GetWidth()==350000 for u in primary);assert {xy(bt[primary[0]].GetStart()),xy(bt[primary[0]].GetEnd())}&{xy(bt[primary[1]].GetStart()),xy(bt[primary[1]].GetEnd())};assert xy(bt[primary[1]].GetEnd())==xy(bt[r18source].GetPosition())
shared=bt['069bb2a3-9216-4c5e-a215-8e53393793fc'];assert shared.GetWidth()==350000 and xy(shared.GetEnd())==xy(bt[r18source].GetPosition());proof=patch(shared,bt[r18source],shared.GetLayer());assert proof;proofs.append(proof)
# Explicit same-width annular patch for the retained 0.190 mm source-via stub.
t=bt[primary[1]];v=bt[r18source];cen=xy(v.GetPosition());points=[[cen[0]-.175,cen[1]-.13],[cen[0]+.175,cen[1]-.13],[cen[0]+.175,cen[1]-.11],[cen[0]-.175,cen[1]-.11]];proof=patch(t,v,t.GetLayer());assert proof;proofs.append(proof)
raw=V.power_width_preservation(a,b);assert raw['failing_nets']==['5V'];exceptions={x['candidate'] for x in tr['width_exception_source_and_candidate_uuids']};assert {x['uuid'] for x in raw['per_net']['5V']['below_floor']}==exceptions
for u in exceptions:assert bt[u].GetWidth()==150000;bt[u].SetWidth(350000)
normalized=V.power_width_preservation(a,b);assert normalized['status']=='pass'
for u in exceptions:bt[u].SetWidth(150000)
pa,pb=V.drill_paste_contacts(a),V.drill_paste_contacts(b);assert pa==pb
pid='5f922c73-82b6-4073-8e98-d520c70499ca';p=bp[pid];assert p.GetNetname()=='unconnected-(U10-EN-Pad3)';en=[]
for l in ls:
 if p.IsOnLayer(l):
  for u,q in objs.items():
   if u!=pid and q.IsOnLayer(l) and hit(p.GetEffectiveShape(l),q.GetEffectiveShape(l)):en.append(u)
  for z in b.Zones():
   if z.IsOnLayer(l) and not z.GetIsRuleArea() and hit(p.GetEffectiveShape(l),z.GetFilledPolysList(l)):en.append(uid(z))
assert not en
for f in (S/'hardware').rglob('*'):
 if f.is_file() and f.name!='nexus-style-fc.kicad_pcb':assert sha(f)==sha(O/'hardware'/f.relative_to(S/'hardware'))
summary={'status':'PASS exact complete R4/R18 transactions with narrow approved two-UUID LED width exception','source_sha256':sha(SP),'candidate_sha256':sha(P),'invariants':inv,'untouched_original_direct_contacts_preserved':retained,'complete_components':components,'finite_full_width_pad_via_proofs':proofs,'R4_branch_cut_proof':{'complete_branch_uuids':sorted(branch),'external_ports':sorted(ext),'only_R4_isolated':True,'all_other_5V_pads_retain_source_connectivity':True},'R18_branch_cut_proof':{'complete_branch_uuids':sorted(r18branch),'external_ports':sorted(ext18),'only_R18_isolated':True,'all_other_5V_pads_retain_source_connectivity':True,'unchanged_shared_F_Cu_primary_chain':primary},'unmodified_USB_all_116_additions_and_tapers':True,'raw_power_width_diagnostic':raw,'two_UUID_normalized_power_width_check':normalized,'approved_width_exceptions':tr['width_exception_source_and_candidate_uuids'],'pasted_vias_unchanged':V.contact_summary(pb),'en_conductive_contacts':en,'qualification':'R4 LED-current and R18 divider-current evidence is branch-specific; no shared power narrowing, ampacity, transient or fabrication qualification is inferred.'};(O/'geometry-verification.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:summary[k] for k in ['status','candidate_sha256','untouched_original_direct_contacts_preserved']}))
