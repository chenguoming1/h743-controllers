from pathlib import Path
import pcbnew as k,json,hashlib,math
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'cc1-corridor-study';P=R/'routing-continuation/r48-local-bends/hardware/nexus-style-fc.kicad_pcb';h=hashlib.sha256(P.read_bytes()).hexdigest();assert h=='5ec240f46778b220b3980aac72444912dac88bbf8f317ee0c6964f97786457e8';b=k.LoadBoard(str(P));uid=lambda x:x.m_Uuid.AsString();xy=lambda p:[p.x/1e6,p.y/1e6];vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));ts={uid(t):t for t in b.GetTracks()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};ls=list(b.GetEnabledLayers().CuStack());names={t.GetNetname():t.GetNetCode() for t in ts.values()}
routes=[
 {'name':'VBUS_B','net':'VBUS','layer':'B.Cu','width_mm':.25,'removed_uuids':['99225004-71df-472c-a636-31c4d4f90c81','1041702b-f11f-443e-83fd-e7628c387764','f1780670-fab9-4c76-b168-8ffad174f78f','111d6d78-35f7-43e9-bb45-7f463c95ccc8','10212bc9-bf61-4ebf-a749-bca715b0e270','a9f3382e-e35f-4097-b4e8-1ff2d71efe36','98b44a51-558b-4634-8c4f-03e51fa04fb5','2b34d42a-27dd-4222-8cdd-c7b731bd59c3','01c9aeac-0b5e-4edc-9e69-50f250fee4b1'],'points':[[103.966,127.98],[105,129.05],[106.15,129.05],[106.15,128.6],[106.35,128.54],[107.4,128.54],[108.4,128.7]]},
 {'name':'CC1_F','net':'CC1','layer':'F.Cu','width_mm':.127,'removed_uuids':['3cc2f313-8525-498e-80e3-fa2529bb350b','247f34a1-9b65-4aac-9eaa-bb4f1d9b7b17'],'points':[[107.65,128.95],[107.63,128.059],[107.28,127.35]]},
 {'name':'CC1_B','net':'CC1','layer':'B.Cu','width_mm':.127,'removed_uuids':['3a8e37fc-1106-47bf-a1a5-48c52f76ae62','b7ed187c-18f4-4de1-ba4e-68cbed972901'],'points':[[106.88,130.1],[106.5,130.65]]},
 {'name':'CC1_In3','net':'CC1','layer':'In3.Cu','width_mm':.127,'removed_uuids':[],'points':[[106.5,130.65],[107.12,130.05],[107.12,128.3],[107.28,127.35]]},
 {'name':'VBUS_C_F','net':'VBUS_C','layer':'F.Cu','width_mm':.25,'removed_uuids':['5c1abafd-ffe0-46c1-8fe1-f96dfc420ca1'],'points':[[106.2,130.128858],[107.15,130.143]]},
 {'name':'VBUS_C_In2','net':'VBUS_C','layer':'In2.Cu','width_mm':.25,'removed_uuids':['b5798389-4ade-4017-83fa-fd463ab9f830'],'points':[[107.732,128.645],[106.2,130.128858]]},
 {'name':'R20_GND_B','net':'GND','layer':'B.Cu','width_mm':.127,'removed_uuids':['691fb65c-c517-45a3-9aa5-29750be42f1d','11661c69-1217-4f81-8e5f-2f80c58ba687','326c9173-8532-473d-b0c1-739f8ebb727d'],'points':[[106.88,129.08],[105.95,129.55]]}
]
moves=[{'uuid':'470695eb-4bba-40ff-86e5-1ae479293bbf','net':'CC1','to':[107.28,127.35]},{'uuid':'448d3407-3e9b-4d32-a791-106cb8074ddf','net':'VBUS_C','to':[106.2,130.128858]},{'uuid':'c27d2d45-e833-42bd-ad22-d9ecb563eb6c','net':'GND','to':[106.67,128.04]}];newvias=[{'name':'CC1_R20_via','net':'CC1','to':[106.5,130.65]},{'name':'R20_GND_via','net':'GND','to':[105.95,129.55]}];rm={u for r in routes for u in r['removed_uuids']};mv={v['uuid'] for v in moves};new=[]
for r in routes:
 for i,(a,z) in enumerate(zip(r['points'],r['points'][1:])):
  q=k.PCB_TRACK(b);q.SetStart(vec(a));q.SetEnd(vec(z));q.SetWidth(round(r['width_mm']*1e6));q.SetLayer(b.GetLayerID(r['layer']));q.SetNetCode(names[r['net']]);new.append((f'{r["name"]}:{i}',q))
for r in moves+newvias:
 q=k.PCB_VIA(b);q.SetPosition(vec(r['to']));q.SetWidth(450000);q.SetDrill(200000);q.SetLayerPair(k.F_Cu,k.B_Cu);q.SetViaType(k.VIATYPE_THROUGH);q.SetNetCode(names[r['net']]);new.append((r.get('uuid',r.get('name')),q))
def col(a,z,c=0):
 v=a.Collide(z,c);return v[0] if isinstance(v,tuple) else bool(v)
ret=[(u,t) for u,t in {**ts,**ps}.items() if u not in rm|mv];hits=[]
# Protect the actual inherited upper-left EP south-spoke gap rectangle, including its .200 mm zone clearance.
chain=k.SHAPE_LINE_CHAIN()
for p in [(105.875,128.2),(106.125,128.2),(106.125,128.4),(105.875,128.4)]:chain.Append(vec(p))
chain.SetClosed(True);guard=k.SHAPE_POLY_SET();guard.AddOutline(chain)
obstacles=[(w,q.GetEffectiveShape(k.B_Cu)) for w,q in ret+new if q.IsOnLayer(k.B_Cu) and q.GetNetname()!='VBUS']
def clear(a,z):
 q=k.PCB_TRACK(b);q.SetStart(vec(a));q.SetEnd(vec(z));q.SetWidth(250000);q.SetLayer(k.B_Cu);s=q.GetEffectiveShape(k.B_Cu)
 if col(s,guard,200002):return False
 return not any(col(s,o,127002) for w,o in obstacles)
a=[105,129.05];z=[107.4,128.54];L=[];Q=[]
for x in [106.05+i*.025 for i in range(19)]:
 for y in [128.65+i*.025 for i in range(17)]:
  p=[round(x,6),round(y,6)]
  if clear(a,p):L.append(p)
for x in [106.4+i*.025 for i in range(17)]:
 for y in [128.5+i*.025 for i in range(7)]:
  p=[round(x,6),round(y,6)]
  if clear(p,z):Q.append(p)
solutions=[]
for p,q in sorted([(p,q) for p in L for q in Q],key=lambda v:math.dist(a,v[0])+math.dist(v[0],v[1])+math.dist(v[1],z)):
 if clear(p,q):
  solutions.append({'points':[a,p,q,z],'length_mm':math.dist(a,p)+math.dist(p,q)+math.dist(q,z)})
  if len(solutions)>=5:break
out={'source_board_sha256':h,'starting_points':len(L),'ending_points':len(Q),'solutions':solutions,'protected_spoke_rectangle_mm':[[105.875,128.2],[106.125,128.2],[106.125,128.4],[105.875,128.4]],'spoke_zone_clearance_mm':.200002,'ordinary_clearance_mm':.127002};(O/'spoke-preserving-bend-search.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
