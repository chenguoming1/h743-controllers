from pathlib import Path
import pcbnew as k,json,hashlib,shutil,sys,uuid
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');S=R/'routing-continuation/r61-six-clearances';O=R/'routing-continuation/r62-input-cap-star';F=Path('/workspace/scratch/8a35c1f26232/nexus-c27-parallel-successor');Q=R/'r61-cap-star-study/atomic-proposal.json';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert not O.exists();assert sha(Q)=='1b3fe4992369b702493961750834c0411f6015c15bbdf8991359a482cd88d123';j=json.loads(Q.read_text());plan=j['atomic_plan'];P=S/'hardware/nexus-style-fc.kicad_pcb';assert sha(P)==j['source_sha256']=='5a51610cc1569958442f97407e11533b646b1e0d8997d86356b8968dce50487e'
for line in (F/'final-manifest.sha256').read_text().splitlines():
 h,p=line.split(None,1);assert sha(F/p)==h,(p,'frozen source drift')
shutil.copytree(S/'hardware',O/'hardware');shutil.copytree(F/'work/nexus-style-fc/tools',O/'tools',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(F/'work/nexus-style-fc/hardware/library',O/'hardware/library',dirs_exist_ok=True);shutil.copy2(F/'work/nexus-style-fc/hardware/nexus-style-fc.kicad_sch',O/'hardware/nexus-style-fc.kicad_sch');assert sha(O/'hardware/nexus-style-fc.kicad_sch')=='7a133c241ba24a688d2d2490ae423ff74d26f57cf6578f871cc757093584de42';assert sha(O/'hardware/nexus-style-fc.kicad_pro')==sha(S/'hardware/nexus-style-fc.kicad_pro');assert sha(O/'hardware/nexus-style-fc.kicad_dru')==sha(S/'hardware/nexus-style-fc.kicad_dru')
O.joinpath('rollback').mkdir();shutil.copy2(P,O/'rollback/nexus-style-fc.kicad_pcb');shutil.copy2(S/'hardware/nexus-style-fc.kicad_sch',O/'rollback/nexus-style-fc.kicad_sch');shutil.copy2(Q,O/'atomic-proposal.json');shutil.copytree(F/'evidence',O/'source-schematic-evidence');
for n in ['final-manifest.sha256','validation.json','compatibility.json','native-placement-proof.json','HANDOFF.txt','selected-part-metadata.json']:shutil.copy2(F/n,O/'source-schematic-evidence'/n)
shutil.copy2(R/'current-main-binding-14.json',O/'current-main-binding.json');shutil.copy2(F/'preview/connected.net',O/'source-final-netlist.xml');shutil.copy2(F/'preview/erc.json',O/'source-native-erc.json')
b=k.LoadBoard(str(P));uid=lambda o:o.m_Uuid.AsString();xy=lambda p:[p.x/1e6,p.y/1e6];vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));ts={uid(t):t for t in b.GetTracks()};fps={f.GetReference():f for f in b.GetFootprints()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};nets={n.GetNetname():n for _,n in b.GetNetsByNetcode().items()};records={x['uuid']:x for x in j['candidate_geometry']['removed_records']}
# Guard every source donor against native geometry before any board mutation.
for u,d in records.items():
 o=ts.get(u) or ps.get(u);assert o is not None and o.GetNetname()==d['net'],('source identity mismatch',u)
 if d['kind']=='track':assert not isinstance(o,k.PCB_VIA) and xy(o.GetStart())==d['start'] and xy(o.GetEnd())==d['end'] and o.GetWidth()==round(d['width']*1e6) and [b.GetLayerName(o.GetLayer())]==d['layers']
 elif d['kind']=='via':assert isinstance(o,k.PCB_VIA) and xy(o.GetPosition())==d['at'] and o.GetWidth(k.F_Cu)==round(d['size']*1e6) and o.GetDrillValue()==round(d['drill']*1e6)
 elif d['kind']=='pad':assert xy(o.GetPosition())==d['at'] and xy(o.GetSize())==d['size'] and o.GetShape()==d['shape']
 else:raise AssertionError(d)
assert len(plan['remove_track_uuids'])==26 and len(plan['remove_via_uuids'])==6 and len(plan['tracks'])==66
for u in plan['remove_track_uuids']:b.Remove(ts[u])
# Replace only C27's approved footprint, add C31, and move only D5 by its exact approved delta.
sys.path.insert(0,str(O/'tools'));import design
parts={p['ref']:p for p in design.get_main_parts()};changes={f['ref']:f for f in plan['footprint_changes']};newids={}
for ref in ['C27','C31']:
 d=changes[ref];assert 'CL21A226MAYNNNE' in d['part'] and 'C602037' in d['part'];part=parts[ref];assert part['value']=='22uF' and part['lcsc']=='C602037' and part['fp']=='NexusFC:C_0805_2012Metric_Samsung_CL21_MinLand';old=fps.get(ref);path=old.GetPath() if old else k.KIID_PATH('/6d2e40fc-44c0-5b6f-881e-79300ab30b81')
 if old:b.Remove(old)
 f=k.FootprintLoad(str(O/'hardware/library/NexusFC.pretty'),'C_0805_2012Metric_Samsung_CL21_MinLand');assert f;f.SetFPID(k.LIB_ID('NexusFC','C_0805_2012Metric_Samsung_CL21_MinLand'));f.SetReference(ref);f.SetValue(part['value']);f.SetField('LCSC',part['lcsc']);f.GetField('LCSC').SetVisible(False);f.SetField('Description',part['note']);f.GetField('Description').SetVisible(False);f.SetPath(path);f.SetUuid(k.KIID(d['uuid']));b.Add(f);f.SetPosition(vec(d['at']));f.Flip(f.GetPosition(),k.FLIP_DIRECTION_LEFT_RIGHT);f.SetOrientationDegrees(d['angle']);f.Reference().SetLayer(k.B_Fab);f.Reference().SetTextSize(vec([.5,.5]));f.Reference().SetTextThickness(80000)
 pd={p['ref'].split('.')[-1]:p for p in d['pads']}
 for pad in f.Pads():
  n=pad.GetNumber();r=pd[n];pad.SetUuid(k.KIID(r['uuid']));assert uid(pad)==r['uuid'];pad.SetNet(nets[part['pins'][n]]);assert xy(pad.GetPosition())==r['at'] and xy(pad.GetSize())==r['size'] and pad.GetShape()==k.PAD_SHAPE_RECT and pad.IsOnLayer(k.B_Cu)
 newids[ref]={'footprint':uid(f),'path':str(f.GetPath().AsString()),'pads':{p.GetNumber():uid(p) for p in f.Pads()}}
d=changes['D5'];f=fps['D5'];assert uid(f)==d['uuid'] and xy(f.GetPosition())==[102.28,125.78] and f.GetOrientationDegrees()==180;f.SetPosition(vec(d['at']));assert xy(f.GetPosition())==[102.28,126.18] and f.GetLayer()==k.B_Cu
for p in f.Pads():r=next(x for x in d['pads'] if x['uuid']==uid(p));assert xy(p.GetPosition())==r['at'] and xy(p.GetSize())==r['size'] and p.GetNetname()==r['net']
added=[];moved=[]
for r in plan['tracks']:
 t=k.PCB_TRACK(b);t.SetStart(vec(r['start']));t.SetEnd(vec(r['end']));t.SetWidth(round(r['width_mm']*1e6));t.SetLayer(b.GetLayerID(r['layer']));t.SetNet(nets[r['net']]);t.SetUuid(k.KIID(r['uuid']));b.Add(t);added.append({'kind':'segment','uuid':r['uuid'],'net':r['net'],'layer':r['layer'],'width':r['width_mm'],'start':r['start'],'end':r['end'],'proposal_id':r['id']})
for r in plan['vias']:
 u=r['uuid']
 if u in ts:
  v=ts[u];assert u in plan['remove_via_uuids'] and v.GetNetname()==r['net'];old=xy(v.GetPosition());front,back=v.GetFrontTentingMode(),v.GetBackTentingMode();v.SetPosition(vec(r['at']));assert (v.GetFrontTentingMode(),v.GetBackTentingMode())==(front,back);moved.append({'uuid':u,'net':r['net'],'from':old,'to':r['at'],'size_mm':.45,'drill_mm':.20,'front_tenting_mode':front,'back_tenting_mode':back,'proposal_id':r['id']})
 else:
  v=k.PCB_VIA(b);v.SetPosition(vec(r['at']));v.SetWidth(450000);v.SetDrill(200000);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(nets[r['net']]);v.SetFrontTentingMode(k.TENTING_MODE_TENTED);v.SetBackTentingMode(k.TENTING_MODE_TENTED);v.SetUuid(k.KIID(u));b.Add(v);added.append({'kind':'via','uuid':u,'net':r['net'],'at':r['at'],'diameter':.45,'drill':.20,'explicit_tenting':'front/back','proposal_id':r['id']})
assert len(moved)==6 and sum(x['kind']=='via' for x in added)==5;OP=O/'hardware/nexus-style-fc.kicad_pcb';k.SaveBoard(str(OP),b)
tr={'status':'Atomic approved C27/C31/D5 and complete routing trial; native acceptance pending','source_directory':str(S),'source_board_sha256':sha(P),'source_schematic_sha256':sha(S/'hardware/nexus-style-fc.kicad_sch'),'candidate_schematic_sha256':sha(O/'hardware/nexus-style-fc.kicad_sch'),'source_proposal_sha256':sha(Q),'source_records':records,'removed_uuids':plan['remove_track_uuids'],'moved_vias':moved,'added_primitives':added,'footprint_changes':plan['footprint_changes'],'instance_uuid_mapping':newids,'retained_taper_primitives':json.loads((S/'transaction.json').read_text())['retained_taper_primitives'],'approved_scope':'Only C27 replaced/relocated with approved 22uF25V custom0805; one C31 same part added on VSYS/GND; only D5 moved 0.400mm south; full donor transaction retains all other parts/pads/nets/stack/outline/rules and exact USB. No blanket invariant exception.','stopping_bound':'One complete atomic transaction from sealed source. Reject any unplanned source/net/geometry delta, new clearance/open/parity regression, lost full-width port, unproved actual ground return or new pasted-hole contact. Native geometry is not production/impedance/thermal qualification.'};(O/'transaction.json').write_text(json.dumps(tr,indent=2)+'\n');print(json.dumps({'pre_refill_pcb_sha256':sha(OP),'removed_tracks':26,'new_segments':66,'moved_vias':6,'added_vias':5,'schema_sha256':tr['candidate_schematic_sha256'],'parts':newids}))
