"""Construct the complete coordinated I2C proposal directly on accepted41."""
import hashlib,json,shutil,sys,uuid
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'native-tools'))
from export_native_copper import export
S=ROOT/'candidate41';O=ROOT/'candidate39';ST=ROOT/'i2c-native-stage39-complete-trunks';D=ROOT/'candidate42'
P=ROOT/'tests/i2c-candidate39-portc/small-cap-portal-screen.json'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
read=lambda f:json.loads(Path(f).read_text())
write=lambda f,v:Path(f).write_text(json.dumps(v,indent=2)+'\n')
source,origin,stage=map(lambda d:read(d/'f722-heli.native.json'),[S,O,ST])
h=sha(S/'f722-heli.kicad_pcb');assert h==source['board_sha256']=='539d9547eb8c4d5984481293ae10cee34355ee838dff11ab43b00cca270ceae2'
assert origin['board_sha256']==sha(O/'f722-heli.kicad_pcb')=='246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7'
assert stage['board_sha256']==sha(ST/'f722-heli.kicad_pcb')=='9ae53da77feffb86dee58502ff0c482a6f1da6ecd33e6a6e3b1e05cfbe0a18c2'
proposal=read(P);assert proposal['complete_selected_geometry_pass'] and proposal['source_board_sha256']==stage['board_sha256']
orig={o['uuid']:o for o in origin['objects']};before={o['uuid']:o for o in source['objects']};st={o['uuid']:o for o in stage['objects']}
restored=set(proposal['restored_PORT_C_source39_uuids']);replaced=set(proposal['removed_SCL_uuids'])
removed=(set(orig)-set(st))-restored
assert len(removed)==7 and all(before[u]==orig[u]for u in removed)
assert all(before[u]==orig[u]for u in restored)
staged_changes={u for u in orig.keys()&st.keys()if orig[u]!=st[u]}
assert {orig[u].get('key')for u in staged_changes}=={'R7.1','R7.2','R8.1','R8.2'}
accepted_changes=(set(orig)-set(before))|{u for u in orig.keys()&before.keys()if orig[u]!=before[u]}
assert not accepted_changes.intersection(removed|staged_changes)
from_stage=(set(st)-set(orig))-replaced
assert len(from_stage)==36 and not from_stage.intersection(before)
assert all(st[u]['kind']in{'track','via'}for u in from_stage)
assert not D.exists();D.mkdir()
for row in read(S/'project-input-preservation.json')['files']:
    src=S/row['path'];dst=D/row['path'];assert sha(src)==row['sha256'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
b=p.LoadBoard(str(S/'f722-heli.kicad_pcb'));held=[];tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
for u in sorted(removed):b.Remove(tracks[u])
nm=lambda n:round(n*1e6)
added=[];mapping=dict(read(S/'f722-heli.logical-route-map.json')['logical_route_map'])
for u in removed:mapping.pop(u,None)
stage_map=read(ST/'f722-heli.logical-route-map.json')['logical_route_map']
def add_record(o):
    if o['kind']=='track':
        t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*map(nm,o['start'])));t.SetEnd(p.VECTOR2I(*map(nm,o['end'])));t.SetWidth(nm(o['width']));assert len(o['copper'])==1;t.SetLayer(b.GetLayerID(next(iter(o['copper']))))
    else:
        assert o['kind']=='via'and o['width']==.45 and o['drill']['width']==.2
        t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(*map(nm,o['xy'])));t.SetWidth(450000);t.SetDrill(200000);t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED)
    t.SetNet(b.FindNet(o['net']));t.SetUuid(p.KIID(o['uuid']));b.Add(t);held.append(t);added.append(o['uuid'])
    if o['net'].startswith('BARO_'):mapping[o['uuid']]=o['net']
for u in sorted(from_stage):add_record(st[u])
for j,row in enumerate(proposal['routes']):
    route=row['selected'];assert route['pass']
    points=[[round(c,6)for c in xy]for xy in route['points_mm']]
    for i,(a,z)in enumerate(zip(points,points[1:])):
        dx,dy=abs(a[0]-z[0]),abs(a[1]-z[1]);assert min(dx,dy)<1e-9 or abs(dx-dy)<1e-8
        add_record({'kind':'track','uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,h+'/'+sha(P)+f'/SCL/{j}/{i}')),'net':'BARO_SCL','start':a,'end':z,'width':.127,'copper':{route['layer']:None}})
add_record({'kind':'via','uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,h+'/'+sha(P)+'/SCL/portal')),'net':'BARO_SCL','xy':proposal['portal_mm'],'width':.45,'drill':{'width':.2}})
assert len(added)==41
fps={f.GetReference():f for f in b.GetFootprints()}
poses=read(S/'poses-native.json')
r7=fps['R7'];assert poses['R7']==[23.5,21.6,90.0,'B.Cu'];r7.Flip(r7.GetPosition(),False);r7.SetOrientationDegrees(-90);r7.SetPosition(p.VECTOR2I(19369000,14373000));poses['R7']=[19.369,14.373,-90.0,'F.Cu']
for ref,xy in [('R8',[23.52,24.0]),('C69',[22.31,22.298])]:
    assert fps[ref].GetLayer()==p.B_Cu and fps[ref].GetOrientationDegrees()==90
    fps[ref].SetPosition(p.VECTOR2I(*map(nm,xy)));poses[ref]=xy+[90.0,'B.Cu']
out=D/'f722-heli.kicad_pcb';p.SaveBoard(str(out),b)
b=p.LoadBoard(str(out));sm=p.GetSettingsManager();assert sm.LoadProject(str(D/'f722-heli.kicad_pro'));b.SetProject(sm.GetProject(str(D/'f722-heli.kicad_pro')));b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(out),b)
after=export(out);now={o['uuid']:o for o in after['objects']}
assert set(before)-set(now)==removed and set(now)-set(before)==set(added)
changed={u for u in before.keys()&now.keys()if before[u]!=now[u]}
assert {before[u].get('key')for u in changed}=={'R7.1','R7.2','R8.1','R8.2','C69.1','C69.2'}
assert all(now[u]==st[u]for u in from_stage)
assert all(now[u]==before[u]for u in restored)
for u in changed:
    if now[u]['key'].startswith('R7.'):assert now[u]==st[u]
oldfp={f['uuid']:f for f in source['footprints']};newfp={f['uuid']:f for f in after['footprints']}
changed_fp={u for u in oldfp if oldfp[u]!=newfp[u]};assert {oldfp[u]['ref']for u in changed_fp}=={'R7','R8','C69'}
assert all(source[k]==after[k]for k in ['edge_cuts','outline_with_npth','copper_layers'])
zone=lambda z:{k:v for k,v in z.items()if k not in {'filled','fill_representation'}}
assert list(map(zone,source['zones']))==list(map(zone,after['zones']))
(D/'f722-heli.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n')
write(D/'f722-heli.logical-route-map.json',{'schema':'f722-logical-route-map/v1','board_sha256':sha(out),'source_sha256':h,'logical_route_map':mapping})
write(D/'fixed-explicit-native-ids.json',sorted((set(read(S/'fixed-explicit-native-ids.json'))-removed)|{u for u in added if now[u]['net'].startswith('BARO_')}))
write(D/'poses-native.json',poses)
receipt={'schema':'f722-complete-I2C-native-construction/v1','status':'complete_geometry_constructed_pending_native_and_electrical_gates','source_board_sha256':h,'hypothesis_origin_board_sha256':origin['board_sha256'],'staged_geometry_board_sha256':stage['board_sha256'],'board_sha256':sha(out),'constructor_sha256':sha(__file__),'final_portal_proposal_sha256':sha(P),'source_native_sha256':sha(S/'f722-heli.native.json'),'source_map_sha256':sha(S/'f722-heli.logical-route-map.json'),'stage_native_sha256':sha(ST/'f722-heli.native.json'),'accepted41_rebind':{'source41_changes_overlap_I2C_removals_or_prior_pose_changes':False,'all_restored_PORT_C_records_exact_to41':sorted(restored),'source41_DSM_transaction_preserved':True},'removed_source_records':[before[u]for u in sorted(removed)],'added_candidate_records':[now[u]for u in added],'changed_pad_records':[{'before':before[u],'after':now[u]}for u in sorted(changed)],'changed_footprint_records':[{'before':oldfp[u],'after':newfp[u]}for u in sorted(changed_fp)],'all_other_source_native_objects_exact':len(before)-len(removed)-len(changed),'numerical_power_VCAP_applicable':False,'intentional_I2C_reference_changes':True,'engine_routing_succeeded':False,'direct_engine_output':False,'adoption_claimed':False,'limits':'Complete nominal construction only. New R7 side transformation, R8/C69 translations, full-width/annular entries, actual clamp cuts, saved reference, RC/timing and fresh power require explicit review. Source39/40/41 and all intermediate proposals remain untouched.'}
write(D/'construction-provenance.json',receipt)
for f in [P,Path(__file__)]:shutil.copy2(f,D/f.name)
print(json.dumps({'board_sha256':receipt['board_sha256'],'removed':len(removed),'added':len(added),'translated_or_flipped_pads':len(changed),'changed_footprints':len(changed_fp),'unchanged':receipt['all_other_source_native_objects_exact']}))
