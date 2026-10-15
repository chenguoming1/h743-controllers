from pathlib import Path
import pcbnew as k,json,hashlib,sys,math
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();uid=lambda x:x.m_Uuid.AsString();vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));xy=lambda p:[p.x/1e6,p.y/1e6];rows=[];boards=[];fills=[]
def poly(t,l):
 p=k.SHAPE_POLY_SET();t.TransformShapeToPolygon(p,l,0,50,k.ERROR_OUTSIDE);return p
def area(p):return abs(p.Area())/1e12
def circle(c,r):
 p=k.SHAPE_POLY_SET();q=k.SHAPE_LINE_CHAIN()
 for i in range(1024):a=2*math.pi*i/1024;q.Append(vec([c[0]+r*math.cos(a),c[1]+r*math.sin(a)]))
 q.SetClosed(True);p.AddOutline(q);return p
for tag,D,ids in [('before',S,tr['routes'][0]['removed_uuids']),('after',O,tr['routes'][0]['new_uuids'])]:
 b=k.LoadBoard(str(D/'hardware/nexus-style-fc.kicad_pcb'));boards.append(b);ts={uid(t):t for t in b.GetTracks()};gs={}
 for l in [k.In1_Cu,k.In4_Cu]:
  g=k.SHAPE_POLY_SET()
  for z in b.Zones():
   if not z.GetIsRuleArea() and z.IsOnLayer(l) and z.GetNetname()=='GND':g.BooleanAdd(z.GetFilledPolysList(l))
  gs[l]=g
 fills.append(gs);t=ts[ids[0]];p=poly(t,t.GetLayer());rec={'role':tag,'board_sha256':sha(D/'hardware/nexus-style-fc.kicad_pcb'),'track_uuid':ids[0],'length_mm':t.GetLength()/1e6,'measurements':[]}
 for l,g in gs.items():
  miss=k.SHAPE_POLY_SET(p);miss.BooleanSubtract(g);nonport=k.SHAPE_POLY_SET(p);regions=[]
  for u in tr['routes'][0]['expected_external_ports']:
   q=ts[u]
   if isinstance(q,k.PCB_VIA):r=q.GetWidth(l)/2e6+.2;nonport.BooleanSubtract(circle(xy(q.GetPosition()),r));regions.append({'via':u,'radius_mm':r,'basis':'Existing same-net via land plus 0.200 mm zone gap; excluded only from explicit non-port projection measure'})
  nm=k.SHAPE_POLY_SET(nonport);nm.BooleanSubtract(g);rec['measurements'].append({'reference_layer':b.GetLayerName(l),'full_width_copper_area_mm2':area(p),'uncovered_area_mm2':area(miss),'coverage_fraction':1-area(miss)/area(p),'non_port_copper_area_mm2':area(nonport),'non_port_uncovered_area_mm2':area(nm),'via_transition_regions':regions})
 rows.append(rec)
for l in [k.In1_Cu,k.In4_Cu]:
 a=k.SHAPE_POLY_SET(fills[0][l]);a.BooleanSubtract(fills[1][l]);b=k.SHAPE_POLY_SET(fills[1][l]);b.BooleanSubtract(fills[0][l]);assert area(a)<1e-10 and area(b)<1e-10
for a,b in zip(rows[0]['measurements'],rows[1]['measurements']):assert b['non_port_uncovered_area_mm2']<=a['non_port_uncovered_area_mm2']+1e-8,(a,b)
out={'status':'PASS: main In1/In4 ground polygons exactly preserved; no increased uncovered route area outside the explicitly excluded existing via transition','source_board_sha256':tr['source_board_sha256'],'candidate_board_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'measurements':rows,'main_In1_In4_ground_fill_exact':True,'qualification':'Same-layer RPM contact correction only; projected ground coverage is geometric evidence, not return impedance or signal-integrity qualification.'};(O/'rpm-return-proof.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
