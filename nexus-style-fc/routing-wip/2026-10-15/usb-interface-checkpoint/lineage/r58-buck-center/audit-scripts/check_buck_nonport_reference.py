from pathlib import Path
import pcbnew as k,json,hashlib,sys,math
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();uid=lambda t:t.m_Uuid.AsString();xy=lambda p:[p.x/1e6,p.y/1e6];vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));boards=[];rows=[]
def area(p):return abs(p.Area())/1e12
def circle(c,r):
 p=k.SHAPE_POLY_SET();q=k.SHAPE_LINE_CHAIN()
 for i in range(1024):a=2*math.pi*i/1024;q.Append(vec([c[0]+r*math.cos(a),c[1]+r*math.sin(a)]))
 q.SetClosed(True);p.AddOutline(q);return p
for tag,D,key in [('before',S,'source'),('after',O,'replacement')]:
 b=k.LoadBoard(str(D/'hardware/nexus-style-fc.kicad_pcb'));boards.append(b);ts={uid(t):t for t in b.GetTracks()};gs={}
 for l in [k.In1_Cu,k.In4_Cu]:
  g=k.SHAPE_POLY_SET()
  for z in b.Zones():
   if not z.GetIsRuleArea() and z.IsOnLayer(l) and z.GetNetname()=='GND':g.BooleanAdd(z.GetFilledPolysList(l))
  gs[l]=g
 out=[]
 for i,r in enumerate(tr['replacements']):
  t=ts[r[key]['uuid']];p=k.SHAPE_POLY_SET();t.TransformShapeToPolygon(p,t.GetLayer(),0,50,k.ERROR_OUTSIDE);vias=[r['target_via']['uuid']]
  if i==2:vias.append('51a22cd5-55d6-4b2a-ab4e-1419692162c2')
  regions=[]
  for u in vias:
   v=ts[u];rad=v.GetWidth(k.F_Cu)/2e6+.2;p.BooleanSubtract(circle(xy(v.GetPosition()),rad));regions.append({'via':u,'center':xy(v.GetPosition()),'radius_mm':rad})
  refs=[k.In4_Cu] if t.GetLayer()==k.B_Cu else [k.In1_Cu,k.In4_Cu]
  for l in refs:
   missing=k.SHAPE_POLY_SET(p);missing.BooleanSubtract(gs[l]);out.append({'route':i,'layer':b.GetLayerName(t.GetLayer()),'reference':b.GetLayerName(l),'non_port_area_mm2':area(p),'uncovered_non_port_area_mm2':area(missing),'excluded_existing_via_transition_regions':regions})
 rows.append({'role':tag,'board_sha256':sha(D/'hardware/nexus-style-fc.kicad_pcb'),'measurements':out})
changes=[]
for a,b in zip(rows[0]['measurements'],rows[1]['measurements']):
 assert (a['route'],a['reference'])==(b['route'],b['reference']);changes.append({'route':a['route'],'reference':a['reference'],'before_uncovered_mm2':a['uncovered_non_port_area_mm2'],'after_uncovered_mm2':b['uncovered_non_port_area_mm2'],'delta_mm2':b['uncovered_non_port_area_mm2']-a['uncovered_non_port_area_mm2']})
out={'status':'Measured full-width reference outside the existing via-transition disks; raw coverage remains in thermal-power-return-proof.json','source_sha256':tr['source_board_sha256'],'candidate_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'measurements':rows,'non_port_changes':changes,'regions_basis':'Existing same-net via land radius plus the 0.200 mm stored zone gap; no new via or reference-plane opening. This explicit exclusion separates transition contact geometry from mid-span projection and does not establish return impedance.'};(O/'buck-nonport-reference.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(changes,indent=2))
