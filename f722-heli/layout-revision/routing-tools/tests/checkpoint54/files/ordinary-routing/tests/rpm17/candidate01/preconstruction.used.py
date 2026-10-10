"""Full exact native source plus explicit reservations; no undeclared removal base."""
import routing_context15 as c
from shapely.geometry import Point,LineString
import json,math
P=c.H/'complete-layer-proposal.json';q=c.read(P);assert q['complete']and q['source_board_sha256']==c.n['board_sha256']and q['removed_source_ids']==[];rows=[]
for r in q['routes']:
 obs=c.obstacles(r['layer'],r['layer']=='B.Cu'and r['name']!='MCU-B');z=c.s.check(LineString(r['points']),obs);rows.append(dict(kind='path',name=r['name'],passed=z[0]['extra_clearance_mm']>=.00001,nearest=z[:3]))
for i,v in enumerate(q['vias']):
 obs=c.s.obstacles(c.net,'In2.Cu')[1]
 for o in c.source:obs.append(dict(object=o.get('key',o['uuid']),layers=['B.Cu'],category='retained_source_clamp_bypass_guard',geometry=c.s.geom(o['copper']['B.Cu']),required_center_distance_mm=.352))
 z=c.s.check(Point(v['xy']),obs);other=[dict(name=b['name'],drill_edge_gap_mm=math.dist(v['xy'],b['xy'])-.2)for j,b in enumerate(q['vias'])if j!=i];rows.append(dict(kind='via',name=v['name'],passed=z[0]['extra_clearance_mm']>=.00001 and all(b['drill_edge_gap_mm']>=.25 for b in other),nearest=z[:3],other_via_drill_gaps=other))
out=dict(schema='f722-additive-RPM-full-source-screen/v1',source_board_sha256=c.n['board_sha256'],source_native_sha256=c.sha(c.D/'f722-heli.native.json'),proposal_sha256=c.sha(P),script_sha256=c.sha(c.H/'preconstruction.py'),context_sha256=c.sha(c.H/'routing_context15.py'),native_source_objects_retained=len(c.n['objects']),removed_source_ids=[],saved_peer_portals=c.reservations,checks=rows,passed=all(r['passed']for r in rows),scope='Every proposed path/via checked against full exact native15 and declared peer portals; target via/trace guards also exclude retained R39 upstream branch to preserve actual clamp cut.')
(c.H/'preconstruction-screen.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(passed=out['passed'],checks=rows),indent=2));assert out['passed']
