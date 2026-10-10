"""In-memory KiCad primitives for selected DSM portals; no board is saved/refilled."""
import sys,pathlib,json,hashlib,uuid
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT/'native-tools'));import export_native_copper as e
p=e.p;board=ROOT/'candidate43/f722-heli.kicad_pcb';expected='1ee7174a578dffe4d5ef3ae8b39d8dc88f28b80395539263a65f23be234c21e6';assert hashlib.sha256(board.read_bytes()).hexdigest()==expected
b=p.LoadBoard(str(board));net=b.FindNet('DSM_RX_MCU');nm=lambda x:round(x*1e6)
paths={'MCU':[[26.634999,15.05],[25.65,15.094],[24.9,14.89055],[24.5,13.3]],'R71':[[34.8,17.29],[36.1,18.6]]};new=[];roles={}
for label,path in paths.items():
 for i,(a,z) in enumerate(zip(path,path[1:])):
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*map(nm,a)));t.SetEnd(p.VECTOR2I(*map(nm,z)));t.SetWidth(127000);t.SetLayer(p.B_Cu);t.SetNet(net);t.SetUuid(p.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL,expected+'/DSM-portals/'+label+'/'+str(i)))));b.Add(t);new.append(t);roles[t.m_Uuid.AsString()]=label+'/'+str(i)
 v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(*map(nm,path[-1])));v.SetWidth(450000);v.SetDrill(200000);v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetFrontTentingMode(p.TENTING_MODE_TENTED);v.SetBackTentingMode(p.TENTING_MODE_TENTED);v.SetNet(net);v.SetUuid(p.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL,expected+'/DSM-portals/'+label+'/via'))));b.Add(v);new.append(v);roles[v.m_Uuid.AsString()]=label+'/via'
rows=[];layers=list(b.GetEnabledLayers().CuStack())
for a in new:
 via=isinstance(a,p.PCB_VIA);q={'uuid':a.m_Uuid.AsString(),'role':roles[a.m_Uuid.AsString()],'kind':'via'if via else'track','net':a.GetNetname(),'start':e.xy(a.GetStart()),'end':e.xy(a.GetEnd()),'width':(a.GetWidth(a.TopLayer())if via else a.GetWidth())/1e6,'copper':{},'drill':e.drill(a)if via else None,'plated':via,'mask':{}}
 if via:q.update(xy=e.xy(a.GetPosition()),via_type=a.GetViaType(),top_layer=b.GetLayerName(a.TopLayer()),bottom_layer=b.GetLayerName(a.BottomLayer()),tented={b.GetLayerName(l):a.IsTented(l)for l in[p.F_Mask,p.B_Mask]})
 q['barrel_layers']=[b.GetLayerName(l)for l in layers if a.IsOnLayer(l)]if via else[]
 for l in layers:
  if a.IsOnLayer(l):q['copper'][b.GetLayerName(l)]=e.shape_polygons(a,l)
 rows.append(q)
r={'schema':'f722-native-in-memory-DSM-portals/v1','board_sha256':expected,'script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'native_version':p.Version(),'maximum_polygon_error_mm':e.ERROR_IU/1e6,'paths':paths,'objects':rows,'source_unchanged':hashlib.sha256(board.read_bytes()).hexdigest()==expected,'board_saved':False,'zone_refilled':False};(H/'selected-portals-native.json').write_text(json.dumps(r,indent=2)+'\n');print(len(rows))
