from pathlib import Path
import pcbnew as k,json,sys,math,hashlib
O=Path(sys.argv[1]).resolve();tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();uid=lambda x:x.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6))
def clone(p):return k.SHAPE_POLY_SET(p)
def rectangle(points):
 p=k.SHAPE_POLY_SET();c=k.SHAPE_LINE_CHAIN()
 for q in points:c.Append(vec(q))
 c.SetClosed(True);p.AddOutline(c);return p
def missing(p,g):
 c=clone(p);c.BooleanSubtract(g);return abs(c.Area())/1e12
def patch(v,g):
 c=xy(v.GetPosition())
 for angle in range(0,360,15):
  a=math.radians(angle);d=(math.cos(a),math.sin(a));n=(-d[1],d[0]);pts=[(c[0]+(.15+ax*.01)*d[0]+ny*.0635*n[0],c[1]+(.15+ax*.01)*d[1]+ny*.0635*n[1]) for ax,ny in [(-1,-1),(1,-1),(1,1),(-1,1)]]
  if missing(rectangle(pts),g)<1e-10:return {'angle_deg':angle,'full_annular_patch_width_mm':.127,'depth_mm':.02,'corners':pts}
 return None
measures={};fills={}
for label,D in [('before',S),('after',O)]:
 P=D/'hardware/nexus-style-fc.kicad_pcb';b=k.LoadBoard(str(P));ts={uid(t):t for t in b.GetTracks()};ground={}
 for lay in [k.In1_Cu,k.In4_Cu]:
  p=k.SHAPE_POLY_SET()
  for z in b.Zones():
   if not z.GetIsRuleArea() and z.IsOnLayer(lay) and z.GetNetname()=='GND':p.BooleanAdd(z.GetFilledPolysList(lay))
  ground[b.GetLayerName(lay)]=p
 contacts=[]
 for u in ['027ae86b-0641-49b1-8175-c1c1592ca7bc','053fc3aa-0617-43ec-a0e9-acfc5ea2e34f']:
  for lay,g in ground.items():
   matches=[]
   for i in range(g.OutlineCount()):
    c=g.UnitSet(i);p=patch(ts[u],c)
    if p:matches.append({'component_index':i,'component_area_mm2':abs(c.Area())/1e12,'proof':p})
   assert matches,(label,u,lay);contacts.append({'via':u,'layer':lay,'finite_actual_plane_contacts':matches})
 measures[label]={'board_sha256':sha(P),'ground_via_contacts':contacts};fills[label]=ground
same=[]
for lay in fills['before']:
 a,b=fills['before'][lay],fills['after'][lay];lost=missing(a,b);added=missing(b,a);assert lost<1e-10 and added<1e-10,(lay,lost,added);same.append({'layer':lay,'removed_GND_area_mm2':lost,'added_GND_area_mm2':added,'area_mm2':abs(a.Area())/1e12})
assert measures['before']['board_sha256']==tr['source_board_sha256'];out={'status':'PASS: the two existing GND vias retain finite full-width annular contacts to identical actual In1/In4 GND fill geometry after refill','same_ground_planes':same,'measurements':measures,'limitation':'Local finite copper/plane preservation only; no high-frequency return, power or system qualification claim.'};(O/'local-ground-return-proof.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
