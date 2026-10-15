from pathlib import Path
import pcbnew as k,json,sys,math,hashlib
S=Path(sys.argv[1]).resolve();O=Path(sys.argv[2]).resolve();OUTDIR=Path(sys.argv[3]).resolve();OUTDIR.mkdir(exist_ok=True,parents=True);tr=json.loads((S/'transaction.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();uid=lambda x:x.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6))
assert sha(S/'hardware/nexus-style-fc.kicad_pcb')=='dcc05684e414cb291761e02b97c2e27fa118dae4cf9363598499972c7e5b3d2a'
def clone(p):return k.SHAPE_POLY_SET(p)
def rectangle(points):
 p=k.SHAPE_POLY_SET();c=k.SHAPE_LINE_CHAIN()
 for q in points:c.Append(vec(q))
 c.SetClosed(True);p.AddOutline(c);return p
def missing(p,g):
 c=clone(p);c.BooleanSubtract(g);return abs(c.Area())/1e12
def inter(p,g):
 c=clone(p);c.BooleanIntersection(g);return c
def patch(v,g):
 c=xy(v.GetPosition());rad=v.GetWidth(k.F_Cu)/2e6;drill=v.GetDrillValue()/2e6
 for angle in range(0,360,15):
  a=math.radians(angle);d=(math.cos(a),math.sin(a));n=(-d[1],d[0]);pts=[(c[0]+(.15+ax*.01)*d[0]+ny*.0635*n[0],c[1]+(.15+ax*.01)*d[1]+ny*.0635*n[1]) for ax,ny in [(-1,-1),(1,-1),(1,1),(-1,1)]]
  assert all(drill+.001<math.dist(c,p)<rad for p in pts)
  if missing(rectangle(pts),g)<1e-10:return {'angle_deg':angle,'full_annular_patch_width_mm':.127,'depth_mm':.02,'corners':pts}
 return None
boards={};fills={};measures={};spokeshapes={}
for label,D in [('before',S),('after',O)]:
 P=D/'hardware/nexus-style-fc.kicad_pcb';b=k.LoadBoard(str(P));ts={uid(t):t for t in b.GetTracks()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};ground={}
 for lay in b.GetEnabledLayers().CuStack():
  p=k.SHAPE_POLY_SET()
  for z in b.Zones():
   if not z.GetIsRuleArea() and z.IsOnLayer(lay) and z.GetNetname()=='GND':p.BooleanAdd(z.GetFilledPolysList(lay))
  ground[b.GetLayerName(lay)]=p
 eps=[p for p in ps.values() if p.GetParentFootprint().GetReference()=='J6' and p.GetNumber()=='EP'];assert len(eps)==4;sm=[]
 for p in eps:
  cen=xy(p.GetPosition());sx,sy=[x/2 for x in xy(p.GetSize())]
  for name,d,edge in [('east',(1,0),sx),('west',(-1,0),sx),('south',(0,1),sy),('north',(0,-1),sy)]:
   n=(-d[1],d[0]);corners=[(cen[0]+(edge+a)*d[0]+w*n[0],cen[1]+(edge+a)*d[1]+w*n[1]) for a,w in [(0,-.125),(.2,-.125),(.2,.125),(0,.125)]];rect=rectangle(corners)
   for lay,g in ground.items():
    shape=inter(rect,g);key=(uid(p),name,lay);spokeshapes[label,key]=shape;sm.append({'pad':uid(p),'position':cen,'direction':name,'layer':lay,'gap_rectangle_corners':corners,'actual_GND_area_in_0_250_mm_spoke_gap_mm2':abs(shape.Area())/1e12})
 records=[];targets=['c27d2d45-e833-42bd-ad22-d9ecb563eb6c']
 # U7's independently retained local GND via is source-bound by exact geometry.
 u7=[u for u,t in ts.items() if isinstance(t,k.PCB_VIA) and t.GetNetname()=='GND' and uid(t)=='c189d3e3-eabe-4e49-804a-4f0944dcadfe' and xy(t.GetPosition())==((106.775,125.975) if label=='before' else (107.375,125.975))];assert len(u7)==1;targets+=u7
 if True:targets.append(next(x['uuid'] for x in tr['new_vias'] if x['name']=='R20_GND_via'))
 for lay in ['In1.Cu','In4.Cu']:
  g=ground[lay];largest=max(range(g.OutlineCount()),key=lambda i:abs(g.UnitSet(i).Area()));component=g.UnitSet(largest);contacts=[]
  for u in targets:
   proof=patch(ts[u],component);assert proof,(label,lay,u);contacts.append({'via':u,'position':xy(ts[u].GetPosition()),'finite_annular_contact':proof})
  epcontacts=[]
  for p in eps:
   dirs=[]
   for name in ['east','west','south','north']:
    q=spokeshapes[label,(uid(p),name,lay)]
    if abs(q.Area())>1e6 and missing(q,component)<1e-10:dirs.append(name)
   assert dirs,(label,lay,uid(p));epcontacts.append({'pad':uid(p),'gap_spokes_in_same_actual_component':dirs})
  records.append({'layer':lay,'component_index':largest,'component_area_mm2':abs(component.Area())/1e12,'via_contacts':contacts,'shield_contacts':epcontacts})
 boards[label]=(b,ts,ps);fills[label]=ground;measures[label]={'board_sha256':sha(P),'all_shield_spoke_gap_measurements':sm,'same_actual_main_plane_component_contacts':records}
loss=[]
for key in [k for l,k in spokeshapes if l=='before']:
 old,new=spokeshapes['before',key],spokeshapes['after',key];lost=missing(old,new)
 if lost>1e-9:loss.append({'pad':key[0],'direction':key[1],'layer':key[2],'lost_spoke_GND_area_mm2':lost,'before_area_mm2':abs(old.Area())/1e12,'after_area_mm2':abs(new.Area())/1e12})
planechange=[]
for lay in ['In1.Cu','In4.Cu']:
 a,b=fills['before'][lay],fills['after'][lay];planechange.append({'layer':lay,'removed_GND_area_mm2':missing(a,b),'added_GND_area_mm2':missing(b,a)})
a,at,ap=boards['before'];b,bt,bp=boards['after'];groute=next(r for r in tr['routes'] if r['name']=='R20_GND_B')
for u in groute['new_uuids']+['f3b26300-209a-441a-b917-158227e4afba']:
 assert u in at
 assert u in bt and at[u].GetNetname()==bt[u].GetNetname() and at[u].GetStart()==bt[u].GetStart() and at[u].GetEnd()==bt[u].GetEnd() and at[u].GetWidth()==bt[u].GetWidth() and at[u].GetLayer()==bt[u].GetLayer()
lens={'retained_R20_pad_to_GND_via_B_Cu_track_sum_before_mm':sum(at[u].GetLength()/1e6 for u in groute['new_uuids']),'retained_R20_pad_to_GND_via_B_Cu_track_sum_after_mm':sum(bt[u].GetLength()/1e6 for u in groute['new_uuids']),'qualification':'Finite actual-plane contacts rechecked after the U10 refill; no return inductance claim.'}
# The direct shield-to-U7 branch is retained byte-for-byte by the independent transaction audit.
assert measures['before']['board_sha256']==sha(S/'hardware/nexus-style-fc.kicad_pcb');out={'status':'PASS' if not loss else 'FAIL: an inherited shield spoke lost filled copper','source_board_sha256':measures['before']['board_sha256'],'candidate_board_sha256':measures['after']['board_sha256'],'all_existing_shield_spoke_copper_preserved':not loss,'lost_spoke_copper':loss,'main_plane_cut_changes':planechange,'R20_return_comparison':lens,'measurements':measures,'qualification':'Finite source-bound copper topology, not ESD or USB system qualification. The 0.250 mm thermal-gap rectangles compare actual stored filled copper on all enabled copper layers; unchanged definitions alone are not used as proof.'};(OUTDIR/'cc1-return-continuity.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['status','lost_spoke_copper','main_plane_cut_changes','R20_return_comparison']},indent=2));assert not loss
