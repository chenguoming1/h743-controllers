"""Hash-bound manufacturing, endpoint and layer checks for a local packet."""
import argparse,hashlib,json,math
from pathlib import Path
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('board',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();a.board=a.board.resolve();b=p.LoadBoard(str(a.board));sm=p.GetSettingsManager();sm.LoadProject(str(a.board.with_suffix('.kicad_pro')));b.SetProject(sm.GetProject(str(a.board.with_suffix('.kicad_pro'))));b.SynchronizeNetsAndNetClasses(False);tracks=list(b.GetTracks());vias=[t for t in tracks if isinstance(t,p.PCB_VIA)];pads=list(b.GetPads());holes=[];mask=[];faults=[]
def uid(x):return x.m_Uuid.AsString()
def label(x):return x.GetParentFootprint().GetReference()+'.'+x.GetNumber()
for pd in pads:
 if pd.GetDrillSize().x or pd.GetDrillSize().y:holes.append((label(pd),pd.GetEffectiveHoleShape()))
 if pd.GetAttribute()==p.PAD_ATTRIB_SMD:
  for l in[p.F_Mask,p.B_Mask]:
   if pd.IsOnLayer(l):q=p.SHAPE_POLY_SET();pd.TransformShapeToPolygon(q,l,pd.GetSolderMaskExpansion(l),10,p.ERROR_OUTSIDE);mask.append((label(pd),l,q))
for v in vias:
 h=v.GetEffectiveHoleShape()
 if v.GetDrillValue()!=200000 or v.GetWidth(p.F_Cu)!=450000:faults.append(dict(type='via-size',via=uid(v)))
 if v.GetFrontTentingMode()!=p.TENTING_MODE_TENTED or v.GetBackTentingMode()!=p.TENTING_MODE_TENTED:faults.append(dict(type='via-not-tented',via=uid(v)))
 for name,l,q in mask:
  if p.SHAPE.Collide(h,q,199999):faults.append(dict(type='drill-mask',via=uid(v),pad=name,layer=b.GetLayerName(l)))
 for name,q in holes:
  if p.SHAPE.Collide(h,q,249999):faults.append(dict(type='hole-gap',via=uid(v),other=name))
 holes.append((uid(v),h))
for t in tracks:
 if isinstance(t,p.PCB_VIA):continue
 if t.GetWidth()<127000:faults.append(dict(type='width',track=uid(t)))
 if t.GetLayer()in[p.In1_Cu,p.In4_Cu]and t.GetNetname()!='GND':faults.append(dict(type='plane-signal-track',track=uid(t)))
b.BuildConnectivity();cn=b.GetConnectivity();fixed_refs={'U1','U2','Y1','R9','R16','FB1','FB2','R3','D3','D4','D5','D6','R14','R15','J1'}|{'C'+str(i)for i in range(1,10)}|{'C11','C12','C13','C18','C19'};fullnets=['HSE_IN','HSE_OUT','HSE_XTAL_OUT','VCAP','VCAP_CAP','IMU_CS','IMU_INT','IMU_MISO','IMU_MOSI','IMU_SCK','USB_N','USB_P','USB_CC1','USB_CC2','+3V3_ANALOG','+3V3_IMU'];connect=[]
for net in fullnets:
 ps=[x for x in pads if x.GetNetname()==net];reached={uid(x)for x in cn.GetConnectedItems(ps[0])}|{uid(ps[0])};connect.append(dict(net=net,complete=all(uid(x)in reached for x in ps),pads=[label(x)for x in ps],unreached=[label(x)for x in ps if uid(x)not in reached]))
ground=[]
for x in pads:
 if x.GetNetname()!='GND'or x.GetParentFootprint().GetReference()not in fixed_refs:continue
 connected=list(cn.GetConnectedItems(x));ground.append(dict(pad=label(x),connected_to_ground_plane=any(isinstance(y,p.ZONE)and y.GetNetname()=='GND'for y in connected),connected_ground_vias=[uid(y)for y in connected if isinstance(y,p.PCB_VIA)]))
planes=[]
for z in b.Zones():
 if z.GetIsRuleArea():continue
 for l in z.GetLayerSet().Seq():
  q=z.GetFilledPolysList(l);planes.append(dict(uuid=uid(z),net=z.GetNetname(),layer=b.GetLayerName(l),outlines=q.OutlineCount(),holes=sum(q.HoleCount(i)for i in range(q.OutlineCount()))))
report=dict(board_sha256=hashlib.sha256(a.board.read_bytes()).hexdigest(),layers=[b.GetLayerName(l)for l in b.GetEnabledLayers().CuStack()],tracks=len(tracks)-len(vias),vias=len(vias),mask_openings=len(mask),faults=faults,fullnet_connectivity=connect,critical_ground_returns=ground,ground_planes=planes,limits='Subset copper audit only. Global power/protection routes and physical system validation remain separate.')
a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(faults=len(faults),incomplete_nets=[r['net']for r in connect if not r['complete']],missing_ground=[r['pad']for r in ground if not r['connected_to_ground_plane']],planes=planes),indent=2));raise SystemExit(bool(faults))
