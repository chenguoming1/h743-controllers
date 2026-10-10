"""Bind and jointly screen the complete source43 DSM tree and declared BEC bend."""
import json,pathlib,hashlib,math
from shapely.geometry import Point,LineString
import native43_geometry as G
H=pathlib.Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
B=H.parent/'dsm-r38-transition43';proof=json.loads((B/'joint-escape-proof.json').read_text());assert proof['board_sha256']==G.EXPECTED and proof['all_geometry_checks_pass']
rows=[]
def path(label,layer,pts,net='DSM_RX_MCU',width=.127):rows.append(dict(label=label,net=net,layer=layer,width_mm=width,points_mm=pts))
path('MCU_escape','B.Cu',[[26.634999,15.05],[25.65,15.094],[24.9,14.89055],[24.5,13.3]])
path('R71_escape','B.Cu',[[34.8,17.29],[36.1,18.6]])
path('R38_escape','B.Cu',[[18.11,23.46],[18.45,23.8],[18.45,24.095]])
main=json.loads((H/'inner-bridge-guarded-proposal.json').read_text())['paths'][0]['points'];assert main[:2]==[[24.5,13.3],[25.9,14.4]]
main.insert(1,[25.2,13.85]);path('MCU_to_R71','In2.Cu',main)
branch=json.loads((H/'R38-four-layer-branch-proposal.json').read_text())['paths'];path('R38_to_bridge1',branch[0]['layer'],branch[0]['points']);path('bridge1_to_bridge2',branch[1]['layer'],branch[1]['points']);path('bridge2_to_joint','In2.Cu',[[21.2,13.2],[21.9,13.3],[23.9,14.1],[25.2,13.85]])
path('BEC_reconstruction','In3.Cu',[[15.021874,20.464544],[17.7,23.7],[17.7,24.8],[24.147805,24.648486]],'+5V_BEC',.6)
removed=['38e0887e-ae81-480f-82c7-f32e7ea12c27','cad1419a-e60e-4274-b9ad-78e419772ee4'];before=G.OBJECTS;G.OBJECTS=[o for o in before if o[0]['uuid']not in removed]
# Add the new BEC copper to the signal checks; source BEC endpoints remain explicit.
bec=rows[-1]
for i,(a,b)in enumerate(zip(bec['points_mm'],bec['points_mm'][1:])):G.OBJECTS.append(({'uuid':'proposed_BEC_'+str(i),'kind':'track','net':'+5V_BEC'},{'In3.Cu':LineString([a,b]).buffer(.3,quad_segs=256)},{},None))
checks=[]
for r in rows:
 T,V,_=G.obstacles(r['net'],r['layer']);half=r['width_mm']/2
 # Geometry helper uses the signal halfwidth; explicitly rescale center offsets for BEC.
 if half!=G.HALF:
  T=[dict(o,required_center_distance_mm=o['required_center_distance_mm']-G.HALF+half,moving_radius_mm=half)for o in T]
 rr=G.check(LineString(r['points_mm']),T,True);checks.append(dict(label=r['label'],passed=rr[0]['extra_clearance_mm']>=G.ERROR,minimum_excess_mm=rr[0]['extra_clearance_mm'],length_mm=LineString(r['points_mm']).length,witnesses=rr[:6]))
vias=[]
for label,xy in [('MCU',[24.5,13.3]),('R71',[36.1,18.6]),('R38',[18.45,24.095]),('bridge1',[12.7,20.9]),('bridge2',[21.2,13.2])]:
 _,V,_=G.obstacles('DSM_RX_MCU','B.Cu');rr=G.check(Point(xy),V,True);vias.append(dict(label=label,net='DSM_RX_MCU',xy_mm=xy,diameter_mm=.45,drill_mm=.2,tented_both_faces=True,passed=rr[0]['extra_clearance_mm']>=G.ERROR,minimum_excess_mm=rr[0]['extra_clearance_mm'],witnesses=rr[:6]))
mutual=[]
for i,v in enumerate(vias):
 for w in vias[i+1:]:mutual.append(dict(kind='new_drill_gap',a=v['label'],b=w['label'],gap_mm=math.dist(v['xy_mm'],w['xy_mm'])-.2,passed=math.dist(v['xy_mm'],w['xy_mm'])-.2>=.25))
for r in rows[:-1]:
 if r['layer']=='In3.Cu':
  gap=LineString(r['points_mm']).distance(LineString(bec['points_mm']))-.0635-.3;mutual.append(dict(kind='new_signal_to_BEC',a=r['label'],b=bec['label'],gap_mm=gap,passed=gap>=.127+G.ERROR))
# Every nonadjacent same-layer signal centerline may meet only at its exact declared endpoint.
segs=[]
for r in rows[:-1]:
 for i,(a,b)in enumerate(zip(r['points_mm'],r['points_mm'][1:])):segs.append((r['label']+'/'+str(i),r['layer'],a,b,LineString([a,b])))
unexpected=[]
for i,(name,l,a,b,g)in enumerate(segs):
 for nam2,lay,c,d,h in segs[i+1:]:
  if l!=lay:continue
  contact=g.buffer(.0635,quad_segs=64).intersection(h.buffer(.0635,quad_segs=64))
  common=set(map(tuple,[a,b]))&set(map(tuple,[c,d]))
  if not contact.is_empty and not common:unexpected.append(dict(a=name,b=nam2,overlap_mm2=contact.area,centerline_intersection=g.intersection(h).wkt))
r=dict(schema='f722-complete-DSM-source43-joint-proposal/v1',source_board_sha256=G.EXPECTED,source_native_sha256=sha(G.SOURCE),script_sha256=sha(__file__),input_sha256={str(p.relative_to(G.ROOT)):sha(p)for p in[B/'joint-escape-proof.json',B/'bec-connected-pad-groups.json',H/'selected-portals-entry-proof.json',H/'inner-bridge-guarded-proposal.json',H/'R38-four-layer-branch-proposal.json']},remove_copper_uuids=removed,footprint_changes=[],paths=rows,vias=vias,checks=checks,mutual_checks=mutual,unexpected_same_net_contacts=unexpected,all_nominal_geometry_passed=all(x['passed']for x in checks+vias+mutual)and not unexpected,native_refill_and_gates_pending=True,numerical_power_applicable=False,scope='Complete proposed three-pad DSM tree; no board constructed/adopted. Only two declared BEC tracks replaced; all existing DSM_EXT, BARO, critical copper, masks and poses retained. Native finite entries, topology, refill/process/reference/support/actual-cut gates remain mandatory.')
(H/'complete-tree-proposal.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['all_nominal_geometry_passed'],'checks':[(x['label'],x['passed'],x['minimum_excess_mm'])for x in checks],'unexpected_contacts':unexpected,'vias':[(v['label'],v['minimum_excess_mm'])for v in vias]},indent=2))
