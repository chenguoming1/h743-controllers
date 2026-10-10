"""Resolve the isolated DSM courtyard conflict with an explicit local feed revision."""
import copy,hashlib,json,shutil,sys,uuid
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'native-tools'))
from export_native_copper import export
SOURCE=ROOT/'candidate40';ORIGIN=ROOT/'candidate39';OUT=ROOT/'candidate41'
PROPOSAL=ROOT/'tests/dsm-core-feed40/proposal40.json'
SOURCE_SHA='ea6c41fef86c1f66dbf6e2ce24b58858313c5c83f2a518e53385d48aad734ed5'
PROPOSAL_SHA='dc45f5a2a23862168917af3b18617e0c498ce4e28c824faa8afc7cd7736faadf'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
read=lambda f:json.loads(Path(f).read_text())
write=lambda f,v:Path(f).write_text(json.dumps(v,indent=2)+'\n')
nm=lambda v:round(v*1e6)
assert sha(PROPOSAL)==PROPOSAL_SHA
proposal=read(PROPOSAL);native=read(SOURCE/'f722-heli.native.json');route_map=read(SOURCE/'f722-heli.logical-route-map.json')
assert sha(SOURCE/'f722-heli.kicad_pcb')==native['board_sha256']==route_map['board_sha256']==proposal['source_board_sha256']==SOURCE_SHA
assert sha(SOURCE/'f722-heli.native.json')==proposal['source_native_sha256']
assert read(PROPOSAL.with_name('result.json'))['all_selected_checks_pass']
before={o['uuid']:o for o in native['objects']}; remove=set(proposal['remove_track_uuids'])
assert len(remove)==5 and all(before[u]['kind']=='track' for u in remove)
assert sorted(before[u]['net'] for u in remove)==['+3V3_CORE','+3V3_CORE','DSM_ILIM','DSM_RX_EXT','GND']
assert not OUT.exists();OUT.mkdir()
for row in read(ORIGIN/'project-input-preservation.json')['files']:
    src=SOURCE/row['path'];dst=OUT/row['path'];assert sha(src)==row['sha256'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
b=p.LoadBoard(str(SOURCE/'f722-heli.kicad_pcb'));tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
for u in sorted(remove):b.Remove(tracks[u])
fp={f.GetReference():f for f in b.GetFootprints()};moves={row['ref']:row for row in proposal['move_footprints']}
assert set(moves)=={'R38','R70','C70'}
for ref,row in moves.items():
    f=fp[ref];v=row['after_pose'];assert f.GetPosition()==p.VECTOR2I(*map(nm,row['before_pose'][:2])) and f.GetOrientationDegrees()==v[2] and f.GetLayerName()==v[3]
    f.SetPosition(p.VECTOR2I(*map(nm,v[:2])))
mapping={u:v for u,v in route_map['logical_route_map'].items() if u not in remove};added=[];held=[]
for label,row in proposal['add_paths'].items():
    for i,(a,z) in enumerate(zip(row['points'],row['points'][1:])):
        item=p.PCB_TRACK(b);item.SetStart(p.VECTOR2I(*map(nm,a)));item.SetEnd(p.VECTOR2I(*map(nm,z)));item.SetLayer(b.GetLayerID(row['layer']));item.SetWidth(nm(row['width']));item.SetNet(b.FindNet(row['net']))
        u=str(uuid.uuid5(uuid.NAMESPACE_URL,SOURCE_SHA+'/'+PROPOSAL_SHA+'/'+label+'/'+str(i)));item.SetUuid(p.KIID(u));b.Add(item);held.append(item);added.append(u)
        if row['net']=='DSM_RX_EXT':mapping[u]='DSM_RX_EXT'
assert len(added)==9 and not proposal['add_vias']
output=OUT/'f722-heli.kicad_pcb';p.SaveBoard(str(output),b)
b=p.LoadBoard(str(output));sm=p.GetSettingsManager();assert sm.LoadProject(str(OUT/'f722-heli.kicad_pro'));b.SetProject(sm.GetProject(str(OUT/'f722-heli.kicad_pro')));b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(output),b)
after=export(output);current={o['uuid']:o for o in after['objects']};changed={u for u in before.keys()&current.keys() if before[u]!=current[u]}
assert set(before)-set(current)==remove and set(current)-set(before)==set(added)
assert len(changed)==6 and {before[u].get('ref') for u in changed}==set(moves)
def move_point(x,ref):
    c=moves[ref];return [round(x[i]+c['after_pose'][i]-c['before_pose'][i],6) for i in range(2)]
def move_polys(pp,ref):return [dict(g,outer=[move_point(x,ref)for x in g['outer']],holes=[[move_point(x,ref)for x in hole]for hole in g.get('holes',[])]) for g in pp]
for u in changed:
    expected=copy.deepcopy(before[u]);ref=expected['ref'];expected['xy']=move_point(expected['xy'],ref)
    for key in ['copper','inside']:expected[key]={l:move_polys(pp,ref)for l,pp in expected[key].items()}
    expected['mask']={l:dict(m,polygons=move_polys(m['polygons'],ref))for l,m in expected['mask'].items()}
    assert current[u]==expected,('Unexpected changed pad record',u)
oldfp={f['uuid']:f for f in native['footprints']};newfp={f['uuid']:f for f in after['footprints']};changedfp={u for u in oldfp if oldfp[u]!=newfp[u]}
assert len(changedfp)==3 and {oldfp[u]['ref'] for u in changedfp}==set(moves)
for u in changedfp:
    expected=copy.deepcopy(oldfp[u]);ref=expected['ref'];expected['xy']=move_point(expected['xy'],ref)
    for g in expected['graphics']:
        assert g['shape']=='Line';g['start']=move_point(g['start'],ref);g['end']=move_point(g['end'],ref)
    assert newfp[u]==expected,('Unexpected changed footprint',ref)
assert all(native[k]==after[k] for k in ['edge_cuts','outline_with_npth','copper_layers'])
zone=lambda z:{k:v for k,v in z.items() if k not in {'filled','fill_representation'}}
assert list(map(zone,native['zones']))==list(map(zone,after['zones']))
(OUT/'f722-heli.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n')
write(OUT/'f722-heli.logical-route-map.json',{'schema':'f722-logical-route-map/v1','board_sha256':sha(output),'source_sha256':SOURCE_SHA,'logical_route_map':mapping})
write(OUT/'fixed-explicit-native-ids.json',sorted((set(read(SOURCE/'fixed-explicit-native-ids.json'))-remove)|{u for u in added if current[u]['net']=='DSM_RX_EXT'}))
poses=read(SOURCE/'poses-native.json')
for ref,row in moves.items():assert poses[ref]==row['before_pose'];poses[ref]=row['after_pose']
write(OUT/'poses-native.json',poses)
receipt={'schema':'f722-courtyard-clear-DSM-native-construction/v1','status':'complete_native_geometry_constructed_all_gates_and_fresh_power_pending','source_board_sha256':SOURCE_SHA,'accepted_origin_board_sha256':'246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7','board_sha256':sha(output),'constructor_sha256':sha(__file__),'proposal_sha256':PROPOSAL_SHA,'source_native_sha256':sha(SOURCE/'f722-heli.native.json'),'source_map_sha256':sha(SOURCE/'f722-heli.logical-route-map.json'),'removed_source_records':[before[u]for u in sorted(remove)],'added_records':[current[u]for u in added],'changed_pad_records':[{'before':before[u],'after':current[u]}for u in sorted(changed)],'changed_footprint_records':[{'before':oldfp[u],'after':newfp[u]}for u in sorted(changedfp)],'all_other_source_native_objects_exact':len(before)-len(remove)-len(changed),'power_width_revision_explicit':{'net':'+3V3_CORE','before_width_mm':.30,'after_width_mm':.25,'after_length_mm':proposal['add_paths']['CORE']['length_mm'],'fresh_DC_required':True},'numerical_power_VCAP_applicable':False,'direct_engine_output':False,'engine_routing_succeeded':False,'courtyard_exclusions_added':False,'DRC_severity_or_rules_changed':False,'adoption_claimed':False}
write(OUT/'construction-provenance.json',receipt)
for f in [PROPOSAL,PROPOSAL.with_name('result.json'),Path(__file__)]:shutil.copy2(f,OUT/f.name)
print(json.dumps({k:receipt[k]for k in ['board_sha256','status','all_other_source_native_objects_exact']}))
