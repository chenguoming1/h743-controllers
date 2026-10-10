"""Finite native pad/annular proofs for two DSM portal proposals, no board claim."""
import copy,hashlib,json,pathlib,sys
from shapely.geometry import Point,LineString
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[str(ROOT/'dsm40-audits'),str(ROOT/'dsm41-audits')]
from audit_dsm40_entries_return import geom,pad_entry,join_entry
from audit_dsm41_entries_return import via_entry
import native43_geometry as G
P=json.loads((H/'selected-portals-native.json').read_text());assert P['board_sha256']==G.EXPECTED and P['source_unchanged'] and not P['board_saved']
by={o['role']:o for o in P['objects']};pads={o['key']:o for o in G.N['objects']if o['kind']=='pad'}
pad=[pad_entry(by['MCU/0'],pads['U1.43'],'B.Cu','start'),pad_entry(by['R71/0'],pads['R71.2'],'B.Cu','start')]
joins=[join_entry(by['MCU/'+str(i)],by['MCU/'+str(i+1)],'B.Cu',.127)for i in[0,1]]
annular=[via_entry(by['MCU/2'],by['MCU/via'],'B.Cu',G.N),via_entry(by['R71/0'],by['R71/via'],'B.Cu',G.N)]
T,V,_=G.obstacles('DSM_RX_MCU','B.Cu');clear=[]
for role in ['MCU','R71']:
 tr=G.check(LineString(P['paths'][role]),T,True);vr=G.check(Point(P['paths'][role][-1]),V,True)
 clear.append(dict(role=role,track_minimum_excess_mm=tr[0]['extra_clearance_mm'],via_minimum_excess_mm=vr[0]['extra_clearance_mm'],track_constraints=len(T),via_constraints=len(V),nearest_track=tr[:6],nearest_via=vr[:6],passed=tr[0]['extra_clearance_mm']>=G.ERROR and vr[0]['extra_clearance_mm']>=G.ERROR))
controls=[];t=copy.deepcopy(by['MCU/0']);t['width']=.4;controls.append(dict(name='oversize_U1_entry',rejected=not pad_entry(t,pads['U1.43'],'B.Cu','start')['passed']))
for role,last in [('MCU','2'),('R71','0')]:
 v=copy.deepcopy(by[role+'/via']);v['drill']['outside']=v['copper']['B.Cu'];controls.append(dict(name=role+'_drill_only_annulus',rejected=not via_entry(by[role+'/'+last],v,'B.Cu',G.N)['passed']))
ref=json.loads((ROOT/'candidate43/reference-snapshot/critical-reference.json').read_text());screen=[]
for role in ['MCU','R71']:
 xy=by[role+'/via']['xy'];hole=Point(xy).buffer(.352,quad_segs=256);hits=[]
 for t in ref['tracks']:
  line=LineString([t['start_mm'],t['end_mm']]);area=line.buffer(t['width_mm']/2,quad_segs=64).intersection(hole).area
  if area>0:hits.append(dict(net=t['net'],track=t['track_uuid'],width_overlap_mm2=area,centerline_overlap_mm=line.intersection(hole).length))
 screen.append(dict(role=role,via_xy_mm=xy,nominal_cut_radius_mm=.352,projected_critical_hits=hits))
gates=dict(finite_pad_entries=all(z['passed']for z in pad),full_width_joins=all(z['passed']for z in joins),finite_actual_annular_entries=all(z['passed']for z in annular),source_clearance=all(z['passed']for z in clear),negative_controls=all(z['rejected']for z in controls))
r=dict(schema='f722-source43-proposed-DSM-portal-entry-proof/v1',board_sha256=G.EXPECTED,native_sha256=hashlib.sha256(G.SOURCE.read_bytes()).hexdigest(),proposal_native_sha256=hashlib.sha256((H/'selected-portals-native.json').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),gates=gates,passed=all(gates.values()),pad_entries=pad,joins=joins,annular_entries=annular,clearances=clear,negative_controls=controls,preinsertion_reference_screen=screen,limits=['No complete DSM tree or board adoption claimed.','The nominal circle screen is preliminary and does not replace native refill/drill-aware comparison including both BARO trees.','No source copper/poses/board saved; numerical power and fabrication qualification not established.'])
(H/'selected-portals-entry-proof.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'gates':gates,'reference_hits':sum(len(s['projected_critical_hits'])for s in screen)}))
