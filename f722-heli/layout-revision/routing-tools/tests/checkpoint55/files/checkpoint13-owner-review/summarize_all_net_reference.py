"""Compact the exact all-net inspection without turning projection facts into qualification."""
import hashlib,json,sys
from pathlib import Path
from shapely.geometry import LineString,Polygon
R=Path(__file__).resolve().parents[1];D=Path(__file__).resolve().parent
N=R/'repo/f722-heli/layout-revision/signal-review/native';sys.path.insert(0,str(N))
from check_signal_geometry import copper_entries,pieces
from check_critical_reference import ground_geometry
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
bp=D/'all-net-before/critical-reference.json';ap=D/'all-net-after/critical-reference.json'
b=read(bp);a=read(ap);c=read(D/'all-net-comparison.json')
changed={'ADC_BUS','ADC_DIV_MID','DSM_RX_MCU','FLASH_HOLD_N','FLASH_WP_N','LED_GREEN_K','PORT_A_RX_MCU'}
bg=read(D/'all-net-before/native-geometry.json');ag=read(D/'all-net-after/native-geometry.json')
assert b['board_sha256']==c['before_board_sha256']==bg['board_sha256']
assert a['board_sha256']==c['after_board_sha256']==ag['board_sha256']
unmodified=sorted(set(a['nets'])-changed)
for n in unmodified:
 assert {o['uuid']:o for o in bg['objects'] if o['net']==n}=={o['uuid']:o for o in ag['objects'] if o['net']==n},n
plane_components={}
for label,g in [('before',bg),('after',ag)]:
 _,_,physical,_=ground_geometry(g,copper_entries(g))
 plane_components[label]={l:{'polygon_components':len(pieces(s,'Polygon')),'physical_area_mm2':s.area,'valid':s.is_valid} for l,s in physical.items()}
wedges=[]
for row in a['tracks']:
 if row['net'] not in changed:continue
 for kind in ('drill_void_outside_own_window','saved_void_or_edge_outside_own_window'):
  for v in row['trace_width_missing_by_class'][kind]:
   shape=Polygon(v['outer_mm'],v.get('holes_mm',[]));line=LineString([row['start_mm'],row['end_mm']])
   wedges.append({'net':row['net'],'track_uuid':row['track_uuid'],'signal_layer':row['signal_layer'],'reference_layer':row['reference_layer'],'width_mm':row['width_mm'],'class':kind,**v,'minimum_distance_to_own_centerline_mm':shape.distance(line),'saved_holes':[a['saved_holes'][row['reference_layer']][i] for i in v['saved_hole_indices']]})
outside_changes={}
for n in unmodified:
 d={f:{k:a['nets'][n][f][k]-b['nets'][n][f][k] for k in ('drill_void_outside_own_window','saved_void_or_edge_outside_own_window')} for f in ('physical_missing_centerline_mm_by_class','physical_missing_trace_width_mm2_by_class')}
 if any(v for q in d.values() for v in q.values()):outside_changes[n]=d
paths=[bp,ap,D/'all-net-before/native-geometry.json',D/'all-net-after/native-geometry.json',D/'all-net-before/native-signals.json',D/'all-net-after/native-signals.json',D/'all-net-comparison.json',D/'all-routed-net-targets.json',D/'inspect_selected_reference.py',Path(__file__)]
r={'schema':'f722-all-routed-net-reference-owner-summary/v1','before_board_sha256':b['board_sha256'],'board_sha256':a['board_sha256'],'target_count':len(a['nets']),'unchanged_routed_net_count':len(unmodified),'unchanged_routed_net_native_objects_exact':True,'changed_signal_nets':sorted(changed),'changed_net_before_after':{n:{'before':b['nets'][n],'after':a['nets'][n]} for n in sorted(changed)},'unchanged_net_numeric_deltas_retained':{n:d for n,d in c['net_numeric_deltas_after_minus_before'].items() if n in unmodified and any(d.values())},'unchanged_net_outside_window_class_total_deltas_retained':outside_changes,'changed_signal_width_regions_outside_own_windows':wedges,'changed_signal_transitions':[v for v in a['transitions'] if v['net'] in changed],'plane_components':plane_components,'ground_ties':{'accepted':len(a['GND_ties']['accepted']),'rejected':len(a['GND_ties']['rejected'])},'whole_plane_changes':c['ground_fill_changes'],'unsupported_tracks':a['unsupported_tracks'],'source_hashes':{str(p.relative_to(R)):sha(p) for p in paths},'qualification':False,'scope':'Exact saved-fill/drill projection and existing ground-tie geometry only. Every nonzero result retained. Plane connectivity does not establish current capacity or AC return impedance. Fresh numerical power/VCAP, signal loading, ADC noise and physical qualification remain separate.'}
(D/'all-net-reference-summary.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'targets':len(a['nets']),'unchanged_native_nets':len(unmodified),'plane_components':plane_components,'changed_width_regions':len(wedges),'minimum_wedge_centerline_distance_mm':min(v['minimum_distance_to_own_centerline_mm'] for v in wedges)}))
