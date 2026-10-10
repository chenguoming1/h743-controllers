"""Remove two SDA copper-only junctions with explicitly screened local paths."""
import copy,hashlib,json,shutil,sys,uuid
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'native-tools'))
from export_native_copper import export
S=ROOT/'candidate42';BASE=ROOT/'candidate41';D=ROOT/'candidate43';TEST=ROOT/'tests/i2c-candidate39-portc'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
read=lambda f:json.loads(Path(f).read_text())
write=lambda f,v:Path(f).write_text(json.dumps(v,indent=2)+'\n')
h=sha(S/'f722-heli.kicad_pcb');assert h=='eac130eb32389c82b2bae274e2c50b73675c79d442cfc8441956369b4cdf3304'
native=read(S/'f722-heli.native.json');assert native['board_sha256']==h
q=read(TEST/'SDA-dogleg-length42-screen.json');r=read(TEST/'SDA-all-short-junctions42.json')
assert q['source_board_sha256']==r['source_board_sha256']==h
inner=next(x for x in q['variants']if x['dogleg_length_mm']==.20);outer=r['In3_variants'][1]
assert inner['pass']and outer['pass']
paths=[{'layer':'In2.Cu','points_mm':inner['points_mm']},{'layer':'In3.Cu','points_mm':outer['points_mm'][1:]}]
remove={'2578d0a8-b03a-528e-899c-7a4772e6863d','d4418002-ec9f-544c-a180-99922f9c0fb6','618cf52e-35a2-50e7-843e-8c813287d492','8621c688-e902-5ddb-862c-78fe1c331c34','78220cf2-1141-507f-8587-a2691fa82e46'}
before={o['uuid']:o for o in native['objects']};assert all(before[u]['kind']=='track'and before[u]['net']=='BARO_SDA'and before[u]['width']==.127 for u in remove)
assert not D.exists();D.mkdir()
for row in read(BASE/'project-input-preservation.json')['files']:
    src=S/row['path'];dst=D/row['path'];assert sha(src)==row['sha256'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
b=p.LoadBoard(str(S/'f722-heli.kicad_pcb'));oldtracks={t.m_Uuid.AsString():t for t in b.GetTracks()};held=[];added=[]
for u in remove:b.Remove(oldtracks[u])
nm=lambda n:round(n*1e6)
for j,path in enumerate(paths):
    for i,(a,z)in enumerate(zip(path['points_mm'],path['points_mm'][1:])):
        t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*map(nm,a)));t.SetEnd(p.VECTOR2I(*map(nm,z)));t.SetWidth(127000);t.SetLayer(b.GetLayerID(path['layer']));t.SetNet(b.FindNet('BARO_SDA'));u=str(uuid.uuid5(uuid.NAMESPACE_URL,h+'/'+sha(TEST/'SDA-all-short-junctions42.json')+f'/SDA/{j}/{i}'));t.SetUuid(p.KIID(u));b.Add(t);held.append(t);added.append(u)
assert len(added)==5
out=D/'f722-heli.kicad_pcb';p.SaveBoard(str(out),b)
b=p.LoadBoard(str(out));sm=p.GetSettingsManager();assert sm.LoadProject(str(D/'f722-heli.kicad_pro'));b.SetProject(sm.GetProject(str(D/'f722-heli.kicad_pro')));b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(out),b)
after=export(out);now={o['uuid']:o for o in after['objects']};assert set(before)-set(now)==remove and set(now)-set(before)==set(added)
assert all(now[u]==o for u,o in before.items()if u not in remove)
assert all(native[k]==after[k]for k in ['footprints','edge_cuts','outline_with_npth','copper_layers'])
zone=lambda z:{k:v for k,v in z.items()if k not in {'filled','fill_representation'}}
assert list(map(zone,native['zones']))==list(map(zone,after['zones']))
(D/'f722-heli.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n')
lm=read(S/'f722-heli.logical-route-map.json')['logical_route_map'];lm={u:v for u,v in lm.items()if u not in remove};lm.update({u:'BARO_SDA'for u in added})
write(D/'f722-heli.logical-route-map.json',{'schema':'f722-logical-route-map/v1','board_sha256':sha(out),'source_sha256':h,'logical_route_map':lm})
write(D/'fixed-explicit-native-ids.json',sorted((set(read(S/'fixed-explicit-native-ids.json'))-remove)|set(added)))
shutil.copy2(S/'poses-native.json',D/'poses-native.json')
receipt=copy.deepcopy(read(S/'construction-provenance.json'));receipt['schema']='f722-complete-I2C-topology-corrected-native-construction/v1';receipt['board_sha256']=sha(out);receipt['construction_source_board_sha256']=h;receipt['source42_construction_receipt_sha256']=sha(S/'construction-provenance.json');receipt['source42_constructor_sha256']=receipt['constructor_sha256'];receipt['constructor_sha256']=sha(__file__)
origin={o['uuid']:o for o in read(BASE/'f722-heli.native.json')['objects']}
receipt['added_candidate_records']=[now[u]for u in sorted(set(now)-set(origin))];assert len(receipt['added_candidate_records'])==41
receipt['topology_cleanup']={'before_topology_refusal_sha256':sha(S/'i2c-geometry-review.json'),'before_direct_entry_and_support_audit_sha256':sha(S/'i2c-entry-support-audit.json'),'screen_inputs':{f.name:sha(f)for f in [TEST/'SDA-dogleg-length42-screen.json',TEST/'SDA-all-short-junctions42.json']},'removed_stage_records':[before[u]for u in sorted(remove)],'added_stage_records':[now[u]for u in added],'paths':paths,'unchanged_stage_objects':len(before)-5,'poses_vias_power_objects_exact_to42':True,'note':'In2 vertical dogleg is0.20mm; In3 horizontal is0.15mm followed by an explicit non-octilinear straight line into the existing via. Native track/clearance rules are unchanged.'}
receipt['status']='complete_geometry_constructed_topology_and_native_revalidation_pending'
write(D/'construction-provenance.json',receipt)
for f in [Path(__file__),TEST/'SDA-dogleg-length42-screen.json',TEST/'SDA-all-short-junctions42.json']:shutil.copy2(f,D/f.name)
print(json.dumps({'board_sha256':sha(out),'source42_removed':5,'source42_added':5,'source41_removed':len(receipt['removed_source_records']),'source41_added':41,'poses_vias_power_objects_exact_to42':True}))
