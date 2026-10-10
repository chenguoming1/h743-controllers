"""Check every proposed primitive against accepted50 minus only declared transaction removals."""
import inspect_pose49 as a,json,hashlib
from shapely.geometry import LineString,Point
m=a.m;H=a.HERE;R=H.parents[2];read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();S=R/'ordinary-routing/candidate50';q=read(H/'native-proposal50.json');n=read(S/'f722-heli.native.json');assert sha(S/'f722-heli.kicad_pcb')==n['board_sha256']==q['source_board_sha256'];assert sha(S/'f722-heli.native.json')==q['source_native_sha256']
old={o['uuid']:o for o in n['objects']};obj={k:o for k,o in old.items()if k not in q['remove_source_track_ids']}
bp=read(H/'pose-stage49c/f722-heli.native.json');up=read(H.parent/'port-a48/u14-stage-75/f722-heli.native.json')
for src,refs in [(bp,{'R33','TP1'}),(up,{'U14'})]:
 for o in src['objects']:
  if o.get('ref')in refs:assert o['uuid']in obj;obj[o['uuid']]=o
for o in q['native_replacement_tracks']:assert o['uuid']not in obj;obj[o['uuid']]=o
m.N=n;m.EXPECTED=n['board_sha256'];m.OBJECTS=[(o,{l:m.geom(ps)for l,ps in o['copper'].items()},{l:m.geom(v['polygons'])for l,v in o.get('mask',{}).items()}if o.get('smd')else{},m.geom(o['drill']['outside'])if o.get('drill')else None)for o in obj.values()]
checks=[];tracks=[dict(name=o['uuid'],net=o['net'],layer=next(iter(o['copper'])),points=[o['start'],o['end']],width=o['width'])for o in q['native_replacement_tracks']]+q['routes']
for r in q['routes']:
 for i,(s,e)in enumerate(zip(r['points'],r['points'][1:])):m.OBJECTS.append((dict(uuid='planned-'+r['name']+'-'+str(i),net=r['net'],kind='track'),{r['layer']:LineString([s,e]).buffer(r['width']/2,quad_segs=128)},{},None))
for v in q['vias']:m.OBJECTS.append((dict(uuid=v['name'],net=v['net'],kind='via',barrel_layers=n['copper_layers']),{l:Point(v['xy']).buffer(.225,quad_segs=128)for l in n['copper_layers']},{},Point(v['xy']).buffer(.1,quad_segs=128)))
for r in tracks:
 m.HALF=r['width']/2;rr=m.check(LineString(r['points']),a.obs(r['net'],r['layer'])[0],True);checks.append(dict(name=r['name'],width_mm=r['width'],net=r['net'],layer=r['layer'],minimum=rr[0],violations=[x for x in rr if x['extra_clearance_mm']<m.ERROR]))
m.HALF=.0635
for v in q['vias']:
 rr=[x for x in m.check(Point(v['xy']),a.obs(v['net'],'B.Cu')[1],True)if x['uuid']!=v['name']];checks.append(dict(name=v['name'],minimum=rr[0],violations=[x for x in rr if x['extra_clearance_mm']<m.ERROR]))
required={'bf4a973d-f08a-5bea-b144-3893a5deddf5','85211987-4dcf-5b08-8e10-7eeddef20113','cb68d33d-6a08-5af7-88b5-25ecbe71116a'};assert all(obj[k]==old[k]for k in required)
legacy=read(H/'candidate02/proposal.json');negative=[];m.HALF=.15
for o in legacy['native_replacement_tracks']:
 if o['net']=='+3V3_CORE' and 'In3.Cu'in o['copper']:
  rr=m.check(LineString([o['start'],o['end']]),a.obs('+3V3_CORE','In3.Cu')[0],True);negative.extend(x for x in rr if x['extra_clearance_mm']<m.ERROR and x['uuid']in required)
assert {x['uuid']for x in negative}==required
out=dict(source_board_sha256=n['board_sha256'],source_native_sha256=sha(S/'f722-heli.native.json'),proposal_sha256=sha(H/'native-proposal50.json'),passed=all(not x['violations']for x in checks),exact_declared_removals=q['remove_source_track_ids'],retained_ADC_SBUS_records_exact=True,retained_obstacle_uuid_regression=sorted(required),legacy_CORE_feed_rejected_against_all_three_retained_objects=True,legacy_CORE_negative_controls=negative,checks=checks,scope='All source50 copper is retained unless listed in the exact transaction; only declared native pad poses replace source pads. Every new/replaced track, including CORE support, is screened against that full base and mutually against every new foreign-net primitive.')
(H/'declared-transaction50-screen.json').write_text(json.dumps(out,indent=2));print(json.dumps({'passed':out['passed'],'track_paths_and_vias_checked':len(checks),'failures':[x for x in checks if x['violations']],'legacy_obstacles_rejected':sorted(required)},indent=2));assert out['passed']
