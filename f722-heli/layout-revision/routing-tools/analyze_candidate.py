"""Summarize actual native ordinary connectivity and routed copper for review.

This is a measurement report, not electrical/timing/EMC qualification.
"""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'native-tools'))
from check_protection_paths import make_graph

def pad_groups(objects):
    return [sorted({v['object']['uuid'] for v in group if v['object']['kind']=='pad'})
            for group in make_graph(objects)
            if any(v['object']['kind']=='pad' for v in group)]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model',type=Path,required=True);ap.add_argument('--native',type=Path,required=True);ap.add_argument('--logical-map',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    m=json.loads(a.model.read_text());n=json.loads(a.native.read_text());handoff=json.loads(a.logical_map.read_text());assert handoff['board_sha256']==n['board_sha256'];route_map=handoff['logical_route_map'];objects=n['objects'];by_uuid={o['uuid']:o for o in objects};rows=[]
    for net in m['ordinary_nets']:
        subset=[o for o in objects if o['net']==net];groups=pad_groups(subset);by_layer=defaultdict(float);vias=[]
        for o in subset:
            if o['kind']=='track':by_layer[next(iter(o['copper']))]+=math.dist(o['start'],o['end'])
            elif o['kind']=='via':vias.append(o['uuid'])
        rows.append({'net':net,'connected':len(groups)==1,'pad_groups':[[by_uuid[uid]['key'] for uid in group] for group in groups],'native_open_connections':max(0,len(groups)-1),'track_length_mm_by_layer':dict(sorted(by_layer.items())),'total_track_length_mm':sum(by_layer.values()),'via_count':len(vias)})
    logical=[]
    for alias,physical in sorted(m['aliases'].items()):
        if physical not in m['ordinary_nets']:continue
        pad_ids={c['uuid'] for c in m['contacts'] if c['net']==alias}
        subset=[o for o in objects if o['uuid'] in pad_ids or (o['kind']!='pad' and route_map.get(o['uuid'])==alias)]
        groups=pad_groups(subset);logical.append({'logical_net':alias,'physical_net':physical,'connected':len(groups)==1,'pad_groups':[[by_uuid[uid]['key'] for uid in group] for group in groups],'open_connections':max(0,len(groups)-1)})
    out={'source_board_sha256':m['board_sha256'],'candidate_board_sha256':n['board_sha256'],'native_sha256':hashlib.sha256(a.native.read_bytes()).hexdigest(),'model_sha256':hashlib.sha256(a.model.read_bytes()).hexdigest(),'physical_ordinary_nets':len(rows),'connected_physical_ordinary_nets':sum(r['connected'] for r in rows),'native_ordinary_open_connections':sum(r['native_open_connections'] for r in rows),'logical_branches':len(logical),'connected_logical_branches':sum(r['connected'] for r in logical),'logical_open_connections':sum(r['open_connections'] for r in logical),'new_ordinary_objects':len(route_map),'physical_nets':rows,'logical_nets':logical,'i2c_geometry':[r for r in rows if r['net'] in {'BARO_SCL','BARO_SDA'}],'limits':'Trace lengths and via counts are measurements only. I2C capacitance, edge rate, reference continuity and electrical timing require their separate material/component models and checks.'}
    a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in {'physical_nets','logical_nets','limits'}}))

if __name__=='__main__':main()
