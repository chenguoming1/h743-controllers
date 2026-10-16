"""Read-only, trace-only saved-board proof; deliberately does not save/refill/DRC."""
import sys,math,json,hashlib,heapq
from pathlib import Path
sys.path.insert(0,'/workspace/shared/nexus-main-placement-fix/scripts')
from router import k,xy,vec,col
ROOT=Path('/workspace/shared/nexus-main-placement-fix')
P=ROOT/'stage36/hardware/nexus-style-fc.kicad_pcb'
OUT=ROOT/'stage36/verification/adc-local'
EXPECTED='bed37199e8d62b8135a27b9e182f8e8f584f1a9fb722cb6efb5d4c87b2a320b8'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P)==EXPECTED
b=k.LoadBoard(str(P));source=k.LoadBoard(str(ROOT/'stage33/hardware/nexus-style-fc.kicad_pcb'))
fs={f.GetReference():f for f in b.GetFootprints()};sf={f.GetReference():f for f in source.GetFootprints()}
tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
ls=[k.F_Cu,k.B_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu]
pad=lambda r,n:next(p for p in fs[r].Pads() if p.GetNumber()==str(n))
node=lambda p,l:(l,round(p[0],6),round(p[1],6))
def graph(net):
 g={}
 def edge(a,z,w,uid,kind):g.setdefault(a,[]).append((z,w,uid,kind));g.setdefault(z,[]).append((a,w,uid,kind))
 for t in b.GetTracks():
  if t.GetNetname()!=net:continue
  uid=t.m_Uuid.AsString()
  if t.GetClass()=='PCB_VIA':
   pp=xy(t.GetPosition());layers=[l for l in ls if t.IsOnLayer(l)]
   for i,l in enumerate(layers):
    for m in layers[i+1:]:edge(node(pp,l),node(pp,m),0,uid,'via')
  elif t.GetClass()=='PCB_TRACK':
   a,z=xy(t.GetStart()),xy(t.GetEnd());edge(node(a,t.GetLayer()),node(z,t.GetLayer()),math.dist(a,z),uid,'track')
 return g

def route(net,a,z):
 g=graph(net);q=[(0,a)];dist={a:0};prev={}
 while q:
  d,n=heapq.heappop(q)
  if d!=dist[n]:continue
  if n==z:break
  for m,w,uid,kind in g.get(n,[]):
   nd=d+w
   if nd<dist.get(m,1e99):dist[m]=nd;prev[m]=(n,w,uid,kind);heapq.heappush(q,(nd,m))
 assert z in dist,(net,a,z)
 edges=[];n=z
 while n!=a:
  old,w,uid,kind=prev[n];edges.append({'kind':kind,'uuid':uid,'layer_from':b.GetLayerName(old[0]),'layer_to':b.GetLayerName(n[0]),'start_mm':list(old[1:]),'end_mm':list(n[1:]),'length_mm':w});n=old
 edges.reverse()
 return {'net':net,'centerline_length_mm':dist[z],'via_count':len({e['uuid'] for e in edges if e['kind']=='via'}),'edges':edges}

results={'source_pcb':str(P),'sha256_before':EXPECTED,'method':'Exact saved trace endpoints and zero-length via layer transitions; centerline lengths between pad centers. No zone connectivity assumed.','routes':{}}
for key,net,ra,na,rz,nz in [('C29_to_U1_9','VX_SENSE','C29',1,'U1',9),('C30_to_U1_10','5V_SENSE','C30',1,'U1',10),('C29_to_R16_2','VX_SENSE','C29',1,'R16',2),('R16_2_to_R17_1','VX_SENSE','R16',2,'R17',1),('C29_to_R17_1','VX_SENSE','C29',1,'R17',1)]:
 pa,pz=pad(ra,na),pad(rz,nz);results['routes'][key]=route(net,node(xy(pa.GetPosition()),fs[ra].GetLayer()),node(xy(pz.GetPosition()),fs[rz].GetLayer()))
results['routes']['DSM_repaired_branch']=route('DSM_TX',node((108.775,123.675),k.B_Cu),node((116.715,117.985),k.In2_Cu))
# Exact pad-center contacts prove retained endpoint joins, independent of zones.
results['pad_contacts']={}
for r,n in [('C29',1),('C30',1),('R16',2),('R17',1)]:
 p=pad(r,n);pos=xy(p.GetPosition());items=[]
 for t in b.GetTracks():
  if t.GetNetname()==p.GetNetname() and t.GetClass()=='PCB_TRACK' and t.IsOnLayer(fs[r].GetLayer()) and min(math.dist(pos,xy(t.GetStart())),math.dist(pos,xy(t.GetEnd())))<1e-8:items.append(t.m_Uuid.AsString())
 assert items
 results['pad_contacts'][r+'.'+str(n)]={'net':p.GetNetname(),'position_mm':pos,'surface':fs[r].GetLayerName(),'exact_center_endpoint_track_uuids':items}
# Repurposed via: exact track center contacts on B and In2, six-layer foreign-net and paste-margin checks.
v=tracks['143f6a86-dfad-4a4b-8c52-59e7a5c3ed89'];vp=xy(v.GetPosition());assert v.GetNetname()=='DSM_TX' and vp==(110.590858,121.956)
contacts=[];violations=[];pad_contacts=[]
for t in b.GetTracks():
 if t.GetClass()=='PCB_TRACK' and t.GetNetname()=='DSM_TX' and min(math.dist(vp,xy(t.GetStart())),math.dist(vp,xy(t.GetEnd())))<1e-8:contacts.append({'uuid':t.m_Uuid.AsString(),'layer':t.GetLayerName()})
for l in ls:
 for o in list(b.GetTracks())+[p for f in fs.values() for p in f.Pads()]:
  if o.GetNetname()!='DSM_TX' and o.IsOnLayer(l) and col(v.GetEffectiveShape(l),o.GetEffectiveShape(l),127002):violations.append({'layer':b.GetLayerName(l),'uuid':o.m_Uuid.AsString(),'net':o.GetNetname()})
for f in fs.values():
 for p in f.Pads():
  for l in [k.F_Cu,k.B_Cu]:
   if p.IsOnLayer(l) and col(v.GetEffectiveShape(l),p.GetEffectiveShape(l),100002):pad_contacts.append({'reference':f.GetReference(),'pad':p.GetNumber(),'surface':b.GetLayerName(l)})
assert not violations and not pad_contacts
assert {x['layer'] for x in contacts}=={'B.Cu','In2.Cu'}
results['DSM_via']={'uuid':v.m_Uuid.AsString(),'net':v.GetNetname(),'position_mm':vp,'center_contacts':contacts,'foreign_copper_clearance_0_127002mm_violations':violations,'either_surface_pad_margin_0_100002mm_violations':pad_contacts,'old_via_ea2fcd32_absent':'ea2fcd32-612d-4f7b-abd5-da944fe7b111' not in tracks,'retained_GND_stitch_net':tracks['a352772a-8c87-46bf-877b-6fd610aab36c'].GetNetname()}
# Poses and their complete pin coordinates/nets are compared with the original accepted topology.
results['preserved_poses']={}
for r in ['C10','C12','Y1']:
 def desc(f):return {'uuid':f.m_Uuid.AsString(),'position_mm':xy(f.GetPosition()),'orientation_degrees':f.GetOrientationDegrees(),'layer':f.GetLayerName(),'pads':sorted([(p.GetNumber(),p.GetNetname(),xy(p.GetPosition())) for p in f.Pads()])}
 got,old=desc(fs[r]),desc(sf[r]);assert got==old;results['preserved_poses'][r]=got
preserve=['22fed353-00d8-46ef-8e79-214d038508b6','81d2d709-ca26-458a-8ff5-186965268676','98f62710-a2ac-4c71-be26-d321136dd89e','9f9826d5-4082-440f-aed3-04e7137e75ae','aca49794-88d4-4009-9ff8-6f8d11613c61','bc8de5db-c205-4ab3-a414-5900c8c6d4ec','c5f165cb-4a7b-426e-990c-77b7e4641e16','da1a158d-e1b5-4410-996d-0449f08b5394','fed846f1-114f-4743-92de-be26f7426347','b54eb5dd-041a-5cef-84af-0d2b43e9656e','b3bcbf59-1c89-5cf2-b4dc-6f5eb5687b30']
st={t.m_Uuid.AsString():t for t in source.GetTracks()}
def desc_t(t):return (t.GetNetname(),t.GetLayer(),xy(t.GetStart()),xy(t.GetEnd()),t.GetWidth())
unchanged=[];modified=[]
for uid in preserve:
 assert uid in tracks
 if desc_t(tracks[uid])==desc_t(st[uid]):unchanged.append(uid)
 else:
  assert uid=='b3bcbf59-1c89-5cf2-b4dc-6f5eb5687b30'
  assert desc_t(tracks[uid])==('GND',k.B_Cu,(111.77,118.65),(111.775,119.6),127000)
  modified.append({'uuid':uid,'before':desc_t(st[uid]),'after':desc_t(tracks[uid]),'purpose':'Extends the existing MCU ground branch to the new C29 quiet-ground via.'})
results['preserved_ground_track_uuids']=unchanged
results['modified_MCU_ground_branch']=modified
quiet=[t for t in b.GetTracks() if t.GetClass()=='PCB_VIA' and xy(t.GetPosition())==(111.775,119.6)]
assert len(quiet)==1 and quiet[0].GetNetname()=='GND'
results['new_C29_ground_via']={'uuid':quiet[0].m_Uuid.AsString(),'net':'GND','position_mm':(111.775,119.6),'existing_MCU_branch_terminates_at_via_center':True}
results['routes']['C29_ground_to_local_stitch']=route('GND',node(xy(pad('C29',2).GetPosition()),k.F_Cu),node((111.775,119.6),k.F_Cu))
results['routes']['U1_12_to_C29_ground_stitch']=route('GND',node(xy(pad('U1',12).GetPosition()),k.B_Cu),node((111.775,119.6),k.B_Cu))
results['DSM_via']['net_via_count_before']=sum(t.GetClass()=='PCB_VIA' and t.GetNetname()=='DSM_TX' for t in source.GetTracks())
results['DSM_via']['net_via_count_after']=sum(t.GetClass()=='PCB_VIA' and t.GetNetname()=='DSM_TX' for t in b.GetTracks())
assert results['DSM_via']['net_via_count_before']==results['DSM_via']['net_via_count_after']
# B-side endpoint tree from retained GND stitch, reaching original C10/C12/Y1.2.
g=graph('GND');start=node((110.375,122.525),k.B_Cu);seen={start};todo=[start]
while todo:
 n=todo.pop()
 for m,w,uid,kind in g.get(n,[]):
  if m not in seen:seen.add(m);todo.append(m)
results['ground_tree_pad_contacts']={}
for r,num in [('C10',2),('C12',2),('Y1',2),('C25',2)]:
 p=pad(r,num);hit=[n for n in seen if n[0]==k.B_Cu and col(p.GetEffectiveShape(k.B_Cu),k.SHAPE_CIRCLE(vec(n[1:]),1),0)];assert hit
 results['ground_tree_pad_contacts'][r+'.'+str(num)]={'reachable_by_explicit_copper_from_GND_110_375_122_525':True,'contact_points_mm':[list(n[1:]) for n in hit]}
results['scope_note']='Ground-fill/reference-plane proof belongs to the separate auditor. Native 0 errors/0 opens/0 parity was supplied by the parent and is not rerun here. Y1.4 pad pose is unchanged; its separate zone-grounding assessment belongs to the ground-fill auditor. This proof targets the Y1.2 explicit-copper tree.'
results['sha256_after']=sha(P);assert results['sha256_after']==EXPECTED
(OUT/'saved-board-proof.json').write_text(json.dumps(results,indent=2)+'\n')
for key,r in results['routes'].items():print(key,round(r['centerline_length_mm'],6),'mm',r['via_count'],'via(s)')
print('DSM six-layer/pad checks PASS; C10/C12/Y1 poses and explicit ground tree PASS; source unchanged')
