"""Exact saved physical-ground projection of the complete PORT_B/SWDIO transaction."""
import pathlib,json,hashlib,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[2];S=R/'ordinary-routing/candidate50';D=H/'candidate03';T=R/'repo/f722-heli/layout-revision/signal-review/native';sys.path.insert(0,str(T))
from check_signal_geometry import poly,centerline,copper_entries
from check_critical_reference import ground_geometry,REFERENCE
from shapely.geometry import Point,mapping
from shapely.ops import unary_union
read=lambda f:json.loads(pathlib.Path(f).read_text());sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
n=read(D/'f722-heli.native.json');old=read(S/'f722-heli.native.json');prov=read(D/'construction-provenance.json');h=sha(D/'f722-heli.kicad_pcb');assert n['board_sha256']==h==prov['board_sha256'];_,zones,physical,drills=ground_geometry(n,copper_entries(n));_,_,oldphysical,_=ground_geometry(old,copper_entries(old))
changed={o['uuid']for o in prov['added_records']}|{p['after']['uuid']for p in prov['changed_track_records']};oldby={o['uuid']:o for o in old['objects']};nets=['PORT_B_TX_MCU','PORT_B_RX_MCU','PORT_B_TX_EXT','PORT_B_RX_EXT','PORT_A_TX_EXT','PORT_A_RX_EXT','SWDIO'];rows=[]
for net in nets:
 vias=[o for o in n['objects']if o['net']==net and o['kind']=='via'];windows=unary_union([Point(o['xy']).buffer(o['width']/2+.127+.01,quad_segs=96)for o in vias])
 for o in n['objects']:
  if o['net']!=net or o['kind']!='track':continue
  layer=next(iter(o['copper']));ref=REFERENCE[layer];line=centerline(o);cu=poly(o['copper'][layer]);miss=line.difference(physical[ref]);wm=cu.difference(physical[ref]);outside=miss.difference(windows);wo=wm.difference(windows)
  row=dict(uuid=o['uuid'],net=net,layer=layer,reference_layer=ref,new_or_changed=o['uuid']in changed,length_mm=line.length,centerline_missing_mm=miss.length,width_missing_mm2=wm.area,centerline_outside_own_via_windows_mm=outside.length,width_outside_own_via_windows_mm2=wo.area,outside_centerline_empty=outside.is_empty,outside_width_empty=wo.is_empty,actual_centerline_missing_geometry=mapping(miss),actual_width_missing_geometry=mapping(wm),own_via_windows=[dict(uuid=v['uuid'],xy=v['xy'],radius_mm=v['width']/2+.127+.01)for v in vias])
  if not row['new_or_changed']:
   prev=oldby[o['uuid']];assert {k:v for k,v in prev.items()if k!='net_code'}=={k:v for k,v in o.items()if k!='net_code'};oldgap=cu.difference(oldphysical[ref]);row['source_saved_width_gap_mm2']=oldgap.area;row['unchanged_source_gap_exact']=oldgap.equals(wm)
  rows.append(row)
by={net:dict(track_count=sum(r['net']==net for r in rows),total_track_length_mm=sum(r['length_mm']for r in rows if r['net']==net),outside_own_windows_centerline_mm=sum(r['centerline_outside_own_via_windows_mm']for r in rows if r['net']==net),outside_own_windows_width_mm2=sum(r['width_outside_own_via_windows_mm2']for r in rows if r['net']==net),new_changed_tracks_all_reference_outside_own_windows_empty=all(r['outside_centerline_empty']and r['outside_width_empty']for r in rows if r['net']==net and r['new_or_changed']))for net in nets}
out=dict(schema='f722-PORT-B-SWDIO-local-return-projection/v1',board_sha256=h,source_board_sha256=old['board_sha256'],native_sha256=sha(D/'f722-heli.native.json'),script_sha256=sha(pathlib.Path(__file__)),construction_provenance_sha256=sha(D/'construction-provenance.json'),full_native_footprint_transform_proof_sha256=sha(D/'native-coordinated-integration.json'),summary=by,tracks=rows,all_new_or_changed_tracks_reference_complete_outside_explicit_own_via_windows=all(v['new_changed_tracks_all_reference_outside_own_windows_empty']for v in by.values()),own_via_window_formula='actual via radius + 0.127mm clearance + 2*0.005mm native-design polygon allowance',dc_connectivity_separate_from_ac_return=True,AC_signal_integrity_or_EMC_qualification=False,numerical_power_qualification=False,limits=['Exact saved-plane projection only. Actual gaps and own-via windows are retained; no contour normalization or numerical tolerance erases them.','No transient return-current extraction, crosstalk, EMI, manufacturing-tolerance or flight qualification is claimed.'])
(D/'new-route-reference-review.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(board_sha256=h,summary=by,passed=out['all_new_or_changed_tracks_reference_complete_outside_explicit_own_via_windows']),indent=2))
