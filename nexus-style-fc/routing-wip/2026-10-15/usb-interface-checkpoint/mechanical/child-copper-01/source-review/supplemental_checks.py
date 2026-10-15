"""Read-only supplemental full-board edge and full-width terminal-cap receipts."""
from pathlib import Path
import runpy, json, hashlib
HERE=Path(__file__).resolve().parent
v=runpy.run_path(str(HERE/'verify_geometry.py'))
s=v['s'];one=v['one'];uid=v['uid'];xy=v['xy'];C=v['C'];B=v['B'];P=v['P']
edges=v['edges'];new_ids={x['uuid'] for r in P['routes'] for x in r['replacement_segments']}
checks=[]
for n in s.find(C,'segment'):
    a,b=xy(n,'start'),xy(n,'end');radius=float(one(n,'width')[1])/2
    distances=[(v['segarc'](a,b,e) if e[0]=='gr_arc' else v['segseg'](a,b,xy(e,'start'),xy(e,'end')))-radius for e in edges]
    idx=min(range(len(distances)),key=distances.__getitem__)
    assert distances[idx]>=.254-1e-8,(uid(n),distances[idx])
    checks.append({'uuid':uid(n),'net':v['txt'](n,'net'),'replacement':uid(n) in new_ids,'edge_clearance_mm':distances[idx],'nearest_edge_uuid':uid(edges[idx])})
terminals=[]
for r in P['routes']:
    t=r['terminal_port'];pad=v['byid'][t['pad_uuid']];endpoint=tuple(r['replacement_segments'][-1]['end']);radius=r['original_width_mm']/2
    xmin,ymin,xmax,ymax=pad['rect']
    margins=[endpoint[0]-xmin-radius,xmax-endpoint[0]-radius,endpoint[1]-ymin-radius,ymax-endpoint[1]-radius]
    assert min(margins)>0 and v['length'](v['sub'](endpoint,pad['c']))<1e-8
    terminals.append({'net':r['net'],'reference':t['reference'],'pad_uuid':t['pad_uuid'],'endpoint':endpoint,'width_mm':radius*2,'entire_round_end_cap_inside_pad':True,'minimum_cap_to_pad_boundary_mm':min(margins),'left_right_bottom_top_margins_mm':margins})
source_path=Path(P['source']['path']);report_path=source_path.parents[2]/'child-native-drc.json'
drc=json.loads(report_path.read_text());reported_donors={item['uuid'] for n in drc['violations'] if n['type']=='copper_edge_clearance' for item in n['items'] if item['description'].startswith('Track ')}
assert reported_donors==v['donors']
assert hashlib.sha256(source_path.read_bytes()).hexdigest()==P['source']['sha256']
report={'status':'Static read-only supplemental screen; requires native refill and DRC','source_sha256':P['source']['sha256'],'initial_native_report_sha256':hashlib.sha256(report_path.read_bytes()).hexdigest(),'all_12_native_track_edge_errors_bound_to_exact_six_donors':True,'full_board_segment_count':len(checks),'minimum_all_segment_edge_mm':min(q['edge_clearance_mm'] for q in checks),'all_segments':checks,'terminal_round_cap_containment':terminals,'source_unchanged':True}
(HERE/'supplemental-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('minimum_all_segment_edge_mm','full_board_segment_count','terminal_round_cap_containment','source_unchanged')},indent=2))
