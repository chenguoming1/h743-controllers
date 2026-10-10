"""Recheck every A and complete NRST item against the immutable native B candidate."""
import ext_planner50 as e
import json,hashlib,pathlib
from shapely.geometry import Point,LineString
m=e.m;H=e.H;S=H.parent/'port-b48/candidate03';read=lambda f:json.loads(pathlib.Path(f).read_text());sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
n=read(S/'f722-heli.native.json');expected='fb8eb611cfb14b221bb3b0da208ef32a64fb378e886a8281e846872537bfb8d3';assert sha(S/'f722-heli.kicad_pcb')==n['board_sha256']==expected
p=read(H/'return-corrected-route-plan.json');assert p['all_surface_branches_found']and p['all_trunks_found'];nrst=e.nrst
old={o['uuid']:o for o in n['objects']};removed={o['uuid']for o in n['objects']if o['kind']=='track'and o['net']=='PORT_A_TX_EXT'and o['uuid']!='9f826ebf-8e2b-485e-a412-abb3d6d5c389'};assert len(removed)==5
for o in nrst['removed_source_records']:assert o['uuid']in old and old[o['uuid']]['net']=='NRST';removed.add(o['uuid'])
m.N=n;m.EXPECTED=expected;m.OUTLINE=m.geom(n['outline_with_npth']['polygons']);e.BASE[:]=[(o,{l:m.geom(ps)for l,ps in o['copper'].items()},{l:m.geom(v['polygons'])for l,v in o.get('mask',{}).items()}if o.get('smd')else{},m.geom(o['drill']['outside'])if o.get('drill')else None)for o in n['objects']if o['uuid']not in removed];e.KEY={o['key']:o for o,c,ms,d in e.BASE if o['kind']=='pad'};e.RESERVED[:]=[q for q in e.RESERVED if q[0]['uuid'].startswith('nrst-reserved')];e.ROUTES[:]=p['routes'];e.VIAS[:]=p['vias'];checks=[]
sb=read(H.parent/'sbus-nrst49/complete-sbus-native19-proposal01.json')
for i,r in enumerate(sb['selected_routes']):e.RESERVED.append((dict(uuid='complete-SBUS-track-'+str(i),net=r['net'],kind='track'),{r['layer']:LineString(r['points']).buffer(r.get('width',r.get('width_mm',.127))/2,quad_segs=128)},{},None))
for i,v in enumerate(sb['vias']):e.RESERVED.append((dict(uuid='complete-SBUS-via-'+str(i),net=v['net'],kind='via',barrel_layers=m.N['copper_layers']),{l:Point(v['xy']).buffer(.225,quad_segs=128)for l in m.N['copper_layers']},{},Point(v['xy']).buffer(.1,quad_segs=128)))
for r in e.ROUTES:
 branch=next(k for k,b in e.BRANCH.items()if b['logical']==r['logical_net']);e.install(branch);rr=m.check(LineString(r['points']),e.a.obs(r['logical_net'],r['layer'])[0],True);checks.append(dict(kind='trace',name=r['name'],minimum=rr[0],violations=[q for q in rr if q['extra_clearance_mm']<m.ERROR]))
for i,v in enumerate(e.VIAS):
 branch=next(k for k,b in e.BRANCH.items()if b['logical']==v['logical_net']);e.install(branch);rr=m.check(Point(v['xy']),[q for q in e.a.obs(v['logical_net'],'F.Cu')[1]if q['uuid']!='new-via-'+str(i)],True);checks.append(dict(kind='via',via=v,minimum=rr[0],violations=[q for q in rr if q['extra_clearance_mm']<m.ERROR]))
e.install('RX0')
for i,r in enumerate(nrst['selected_paths']):
 if r['net']!='NRST':continue
 rr=m.check(LineString(r['points']),e.a.obs(r['net'],r['layer'])[0],True);checks.append(dict(kind='NRST-SBUS-transition-trace',index=i,minimum=rr[0],violations=[q for q in rr if q['extra_clearance_mm']<m.ERROR]))
for i,v in enumerate(nrst['vias']):
 if v['net']!='NRST':continue
 rr=m.check(Point(v['xy']),[q for q in e.a.obs(v['net'],'F.Cu')[1]if q['uuid']!='nrst-reserved-via-'+str(i)],True);checks.append(dict(kind='NRST-SBUS-transition-via',index=i,minimum=rr[0],violations=[q for q in rr if q['extra_clearance_mm']<m.ERROR]))
out=dict(schema='f722-complete-PORT-A-EXT-and-NRST-proposal/v1',source_board_sha256=expected,source_native_sha256=sha(S/'f722-heli.native.json'),accepted50_source_sha256='cbb9a1f0b43dc612718baf1277302c9ac0767474cc7fa13f5d8c0a2428f2b787',source_dir=str(S),routes=p['routes']+[dict(net=r['net'],logical_net=r['net'],layer=r['layer'],points=r['points'],width=r['width_mm'],name='nrst-transition-'+str(i))for i,r in enumerate(nrst['selected_paths'])if r['net']=='NRST'],vias=p['vias']+[dict(net=v['net'],logical_net=v['net'],xy=v['xy'])for v in nrst['vias']if v['net']=='NRST'],removed_source_ids=sorted(removed),allowed_changed_nets=['PORT_A_RX_EXT','PORT_A_TX_EXT','NRST'],all_surface_branches_found=True,all_trunks_found=True,placement_changes={},route_source_sha256=sha(H/'return-corrected-route-plan.json'),NRST_source_sha256=sha(H.parent/'sbus-nrst49/transition-proposal-v2.json'))
proposal=H/'ext-return-corrected-proposal.json';proposal.write_text(json.dumps(out,indent=2)+'\n');screen=dict(source_board_sha256=expected,proposal_sha256=sha(proposal),passed=all(not r['violations']for r in checks),checks=checks,source_unchanged=sha(S/'f722-heli.kicad_pcb')==expected);(H/'ext-return-corrected-screen.json').write_text(json.dumps(screen,indent=2)+'\n');print(json.dumps(dict(passed=screen['passed'],violations=[r for r in checks if r['violations']],track_segments=sum(len(r['points'])-1 for r in out['routes']),vias=len(out['vias']),removed=len(removed)),indent=2))
