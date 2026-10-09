#!/usr/bin/env python3
"""Regression evidence for degenerate horizontal/vertical closure bounding boxes."""
import hashlib,json,pathlib
from shapely.geometry import LineString,box
HERE=pathlib.Path(__file__).resolve().parent
fixtures=[
 {'name':'SBUS_LV_vertical_native_pad_centers','centers':[[20.5,9.7875],[20.5,11.24]],'path':[[20.5,10.45],[20.5,11.045]]},
 {'name':'horizontal_transpose_control','centers':[[9.7875,20.5],[11.24,20.5]],'path':[[10.45,20.5],[11.045,20.5]]},
]
results=[]
for f in fixtures:
 x0,y0,x1,y1=LineString(f['centers']).bounds
 old=box(x0,y0,x1,y1).buffer(1.25,join_style='mitre')
 # Exact four-bound expansion used by screen.py; no buffer of a degenerate polygon.
 fixed=box(x0-1.25,y0-1.25,x1+1.25,y1+1.25)
 path=LineString(f['path'])
 assert fixed.is_valid and fixed.covers(path)
 assert fixed.covers(LineString(f['centers']))
 assert abs(fixed.area-(x1-x0+2.5)*(y1-y0+2.5))<1e-9
 results.append(f|{'legacy_buffer_covers_path':old.covers(path),'legacy_buffer_bounds':old.bounds,'legacy_buffer_area':old.area,'explicit_bounds_covers_path':fixed.covers(path),'explicit_bounds_area':fixed.area,'passed':True})
assert results[0]['legacy_buffer_covers_path'] is False
source=(HERE/'screen.py').read_bytes()
assert b'roi=box(x0-1.25,y0-1.25,x1+1.25,y1+1.25)' in source
receipt={'screen_sha256':hashlib.sha256(source).hexdigest(),'control_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'regression':'Buffering a zero-width bounding Polygon produces a triangle and silently excludes a valid vertical path. Expand all four bounds numerically before creating the Polygon.','cases':results,'all_passed':True}
(HERE/'bbox-control.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'all_passed':True,'control_receipt_sha256':hashlib.sha256((HERE/'bbox-control.json').read_bytes()).hexdigest(),'cases':results}))
