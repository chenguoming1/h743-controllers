"""Independent native audit of the narrowly approved EN-only PCB correction.
Run with official KiCad 10 pcbnew Python. This never saves either board.
"""
from pathlib import Path
import argparse, collections, copy, hashlib, importlib.util, json, math
import pcbnew as k
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('candidate',type=Path);p.add_argument('transaction',type=Path);p.add_argument('output',type=Path);p.add_argument('--validator',type=Path,required=True);p.add_argument('--ledger',type=Path,default=Path(__file__).with_name('repair-lane-recovery.json'));args=p.parse_args()
spec=importlib.util.spec_from_file_location('validator',args.validator);V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();uid=lambda x:x.m_Uuid.AsString();xy=lambda x:(x.x/1e6,x.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));shape=lambda x,l:x.GetEffectiveShape(l)
def collide(a,b):
 r=a.Collide(b,0)
 return r[0] if isinstance(r,tuple) else bool(r)
tr=json.loads(args.transaction.read_text());ledger=json.loads(args.ledger.read_text());delta=tr['approved_pin_delta'];pid=delta['pad_uuid'];nc=delta['new_net'];before_hash=sha(args.source);candidate_hash=sha(args.candidate);assert before_hash==tr['source_sha256'];removed={z['uuid'] for z in tr['removed_terminal_tracks']};assert removed==set(ledger['authorized_en_delta']['removed_terminal_track_uuids']) and len(removed)==10
assert k.Version().startswith('10.'),k.Version()
a,b=[k.LoadBoard(str(x)) for x in [args.source,args.candidate]];layers=list(b.GetEnabledLayers().CuStack());ats={uid(t):t for t in a.GetTracks()};bts={uid(t):t for t in b.GetTracks()};ap={uid(q):q for f in a.GetFootprints() for q in f.Pads()};bp={uid(q):q for f in b.GetFootprints() for q in f.Pads()}
assert set(ats)-set(bts)==removed and not set(bts)-set(ats);assert set(ap)==set(bp)
assert ap[pid].GetNetname()=='VSYS' and bp[pid].GetNetname()==nc and bp[pid].GetParentFootprint().GetReference()=='U10' and bp[pid].GetNumber()=='3'
for u,q in ap.items():assert q.GetNetname()==bp[u].GetNetname() or u==pid
for u,t in ats.items():
 if u in removed:
  assert not isinstance(t,k.PCB_VIA) and t.GetNetname()=='VSYS' and t.GetLayer()==k.F_Cu
  continue
 def props(x):
  via=isinstance(x,k.PCB_VIA)
  return (x.GetClass(),xy(x.GetStart()),xy(x.GetEnd()),x.GetNetname(),tuple(l for l in layers if x.IsOnLayer(l)),tuple(x.GetWidth(l) for l in layers if x.IsOnLayer(l)) if via else x.GetWidth(),x.GetDrillValue() if via else None,x.IsLocked(),(x.GetFrontTentingMode(),x.GetBackTentingMode()) if via else None)
 assert props(t)==props(bts[u]),('Retained conductor changed',u)
btree,ctree=[V.parse_sexpr(x.read_text()) for x in [args.source,args.candidate]]
# Preserve the complete source definition of every retained conductor, including
# arc control points and via padstack attributes beyond the native summary above.
for kind in ['segment','arc','via']:
 aa=V.keyed_nodes(V.children(btree,kind));bb=V.keyed_nodes(V.children(ctree,kind))
 assert {u:z for u,z in aa.items() if u not in removed}==bb,('Retained full copper definition changed',kind)
norm=copy.deepcopy(ctree);found=[]
expected_metadata={'footprint_reference':'U10','footprint_uuid':'2adce67c-e374-4481-bd09-c981604a7cf8','property':'Description','property_uuid':'8e515ed0-f0e8-479a-863f-d8d7ef5b838d','old_value':'3V3 sensor LDO, 30 V input','new_value':'3V3 sensor LDO, 30 V input; EN intentionally floating (internal pull-up), never tied to VSYS'}
md=tr.get('approved_metadata_delta');assert md and all(md.get(key)==value for key,value in expected_metadata.items())
metadata_found=[]
for fp in V.children(norm,'footprint'):
 if V.source_uuid(fp)!=expected_metadata['footprint_uuid']:continue
 for prop in V.children(fp,'property'):
  if V.atom(prop[1])=='Description':
   assert V.source_uuid(prop)==expected_metadata['property_uuid'] and V.atom(prop[2])==expected_metadata['new_value'];prop[2]=('string',expected_metadata['old_value']);metadata_found.append(expected_metadata['property_uuid'])
assert metadata_found==[expected_metadata['property_uuid']]

for fp in V.children(norm,'footprint'):
 for pad in V.children(fp,'pad'):
  if V.source_uuid(pad)==pid:
   nets=V.children(pad,'net');assert len(nets)==1 and V.atom(nets[0][-1])==nc;nets[0][-1]=('string','VSYS');found.append(pid)
assert found==[pid];inv=V.invariant_checks(a,b,btree,norm);af,bf=V.native_footprints(a),V.native_footprints(b)
for f in bf.values():
 for q in f['pads']:
  if q['uuid']==pid:assert q['net']==nc;q['net']='VSYS'
inv['checks']['footprint_and_pad_native_geometry']=V.compare('Native geometry except exact approved U10.3 net field',af,bf)
an=sorted(n.GetNetname() for _,n in a.GetNetsByNetcode().items());bn=sorted(n.GetNetname() for _,n in b.GetNetsByNetcode().items());assert nc not in an and bn==sorted(an+[nc]);inv['checks']['net_names']=V.compare('Net names except exact new singleton EN net',an,[n for n in bn if n!=nc]);assert all(z['status']=='pass' for z in inv['checks'].values()),inv;inv['status']='pass';inv['approved_exception']=delta;inv['exact_metadata_parity_exception']=expected_metadata
# Every original direct physical contact where both items remain must survive.
seen=set();retained=[];deleted=[];ports=set();conn=a.GetConnectivity()
for u,t in ats.items():
 for z in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)):
  w=uid(z);q=ats.get(w) or ap.get(w);key=tuple(sorted([u,w]));ls=[l for l in layers if t.IsOnLayer(l) and q.IsOnLayer(l) and collide(shape(t,l),shape(q,l))]
  if u==w or key in seen or not ls:continue
  seen.add(key)
  if u in removed or w in removed:
   deleted.append(key)
   for inside,outside in [(u,w),(w,u)]:
    if inside in removed and outside not in removed:ports.add(outside)
  else:
   nq=bts.get(w) or bp.get(w);assert any(collide(shape(bts[u],l),shape(nq,l)) for l in ls),('Lost retained contact',key);retained.append(key)
expected_ports=set(ledger['authorized_en_delta']['external_retained_ports'])|{pid};assert ports==expected_ports,(ports,expected_ports)
assert not any(t.GetNetname()==nc for t in bts.values());assert [u for u,q in bp.items() if q.GetNetname()==nc]==[pid]
# A positive-area full-width entry patch beyond the drill at the retained source junction.
via=bts['ce0c83ec-dabe-41bb-a4f2-460dd49ca91c'];center=xy(via.GetPosition());annular=[]
for tu in ['54aabec8-33dc-4725-92db-c353e1612ad5','372f5df5-cbd1-44bd-bc7c-c369fcd0e6f9']:
 t=bts[tu];l=t.GetLayer();aa,cc=xy(t.GetStart()),xy(t.GetEnd());length=math.dist(aa,cc);dr=((cc[0]-aa[0])/length,(cc[1]-aa[1])/length);normal=(-dr[1],dr[0]);rad=t.GetWidth()/2e6;proj=sum((center[i]-aa[i])*dr[i] for i in range(2));off=abs(sum((center[i]-aa[i])*normal[i] for i in range(2)));proof=None
 for q in [max(.01,min(length-.01,proj+d)) for d in [.12,-.12,.14,-.14,.16,-.16,.18,-.18]]+[j*length/100 for j in range(1,100)]:
  if not .01<=q<=length-.01:continue
  corners=[(aa[0]+(q+side*.01)*dr[0]+cross*rad*normal[0],aa[1]+(q+side*.01)*dr[1]+cross*rad*normal[1]) for side in [-1,1] for cross in [-1,1]];distance=math.hypot(max(abs(proj-q)-.01,0),max(off-rad,0))
  if distance>=via.GetDrillValue()/2e6+.001 and all(collide(shape(via,l),vec(c)) for c in corners):proof={'track':tu,'via':uid(via),'layer':b.GetLayerName(l),'full_width_mm':2*rad,'axial_depth_mm':.02,'minimum_distance_from_drill_center_mm':distance,'corners':corners};break
 assert proof,('Retained junction full-width entry unproved',tu);annular.append(proof)
stubs=[]
for u in ['96b12e5e-968d-4500-97cd-2fe832e967c6','f526e6a3-c8c8-473d-81cb-48d54ae7aaaa']:
 t=bts[u];radius=max(math.dist(center,xy(t.GetStart())),math.dist(center,xy(t.GetEnd())))+t.GetWidth()/2e6;assert radius<=via.GetWidth(k.F_Cu)/2e6;stubs.append({'track':u,'maximum_occupied_radius_mm':radius,'via_radius_mm':via.GetWidth(k.F_Cu)/2e6,'entire_stub_inside_retained_via':True})
def en_contacts():
 contacts=[];pad=bp[pid]
 for l in layers:
  if not pad.IsOnLayer(l):continue
  for u,obj in {**bts,**bp}.items():
   if u!=pid and obj.IsOnLayer(l) and collide(shape(pad,l),shape(obj,l)):contacts.append({'kind':'copper','uuid':u,'net':obj.GetNetname(),'layer':b.GetLayerName(l)})
  for z in b.Zones():
   if z.IsOnLayer(l) and not z.GetIsRuleArea() and collide(shape(pad,l),z.GetFilledPolysList(l)):contacts.append({'kind':'filled zone','uuid':uid(z),'net':z.GetNetname(),'layer':b.GetLayerName(l)})
 return contacts
stored_contacts=en_contacts();assert not stored_contacts,stored_contacts
assert k.ZONE_FILLER(b).Fill(b.Zones()) is not False
refilled_contacts=en_contacts();assert not refilled_contacts,refilled_contacts
floor_before=V.power_width_preservation(a,a);floor_after=V.power_width_preservation(a,b)
for net,rec in floor_after['per_net'].items():
 old=floor_before['per_net'][net];assert not rec['candidate_missing_baseline_routes'];assert {x['uuid'] for x in rec['below_floor']}<={x['uuid'] for x in old['below_floor']}
 if old['baseline_minimum_mm'] is not None:assert rec['candidate_minimum_mm']>=old['baseline_minimum_mm']
assert set(floor_after['failing_nets'])<=set(floor_before['failing_nets'])
pa,pb=V.drill_paste_contacts(a),V.drill_paste_contacts(b);assert pa==pb;assert sha(args.source)==before_hash and sha(args.candidate)==candidate_hash
out={'status':'PASS: exact EN-only geometry and physical-isolation audit; source-bound final ERC/DRC required separately','source_sha256':before_hash,'candidate_sha256':candidate_hash,'approved_pin_delta':delta,'approved_metadata_delta':expected_metadata,'removed_terminal_tracks':tr['removed_terminal_tracks'],'removed_direct_contact_pairs':deleted,'retained_direct_contacts_preserved':len(retained),'external_cut_ports':sorted(ports),'cut_junction_full_width_entries':annular,'retained_via_contained_stubs':stubs,'en_conductive_contacts_stored_fill':stored_contacts,'en_conductive_contacts_independent_refill':refilled_contacts,'en_net_track_or_via_count':0,'invariants_with_exact_single_pin_exception':inv,'all_retained_copper_properties_exact':True,'baseline_absolute_F722_power_floor':floor_before,'candidate_absolute_F722_power_floor':floor_after,'no_inherited_width_regression':True,'pasted_vias_unchanged':V.contact_summary(pb),'input_source_bytes_unchanged':True,'qualification':'EN correction only. Existing routing/clearance/width findings and power, return, regulator loop, effective capacitor, USB, pasted-via and fabrication gates remain open.'};args.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({n:out[n] for n in ['status','candidate_sha256','retained_direct_contacts_preserved','en_conductive_contacts_stored_fill','en_conductive_contacts_independent_refill']}))
