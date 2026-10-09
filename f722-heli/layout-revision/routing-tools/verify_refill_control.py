"""Verify loaded native signal-via antipads and complete GND pad topology."""
import argparse
import json
import sys
from pathlib import Path
from shapely.geometry import Polygon
from shapely import unary_union
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'native-tools'))
from check_protection_paths import make_graph

def geom(ps):
    return unary_union([Polygon(p['outer'],p.get('holes',[])) for p in ps])

def ground_groups(n):
    objects=[o for o in n['objects'] if o['net']=='GND']
    objects += [{'uuid':z['uuid'],'kind':'zone','net':z['net'],'copper':z['filled'],'drill':None,'plated':False} for z in n['zones'] if not z['rule'] and z['net']=='GND']
    return sorted(sorted({v['object']['uuid']+':'+v['layer'] for v in group if v['object']['kind']=='pad'}) for group in make_graph(objects))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--result',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    before=json.loads(a.source.read_text());after=json.loads(a.result.read_text());old_ids={o['uuid'] for o in before['objects']};added=[o for o in after['objects'] if o['uuid'] not in old_ids]
    vias=[o for o in added if o['kind']=='via'];assert len(vias)==1 and vias[0]['net']=='FLASH_CS';via=vias[0];assert all(o['net']=='FLASH_CS' for o in added)
    old_groups=ground_groups(before);new_groups=ground_groups(after);assert old_groups==new_groups
    native={o['uuid']:o for o in after['objects']};assert all(native[o['uuid']]==o for o in before['objects']);checks=[]
    for z in after['zones']:
        if z['rule'] or z['net']!='GND' or not set(z['layers'])<={'In1.Cu','In4.Cu'}:continue
        old=next(x for x in before['zones'] if x['uuid']==z['uuid'])
        assert {k:v for k,v in z.items() if k not in {'filled','fill_representation'}}=={k:v for k,v in old.items() if k not in {'filled','fill_representation'}}
        for layer,ps in z['filled'].items():
            current=geom(ps);previous=geom(old['filled'][layer]);gap=current.distance(geom(via['copper'][layer]));before_holes=sum(len(p['holes']) for p in old['filled'][layer]);after_holes=sum(len(p['holes']) for p in ps)
            assert gap>=.127 and len(ps)==len(old['filled'][layer]) and after_holes==before_holes+1
            assert current.difference(previous).area==0
            checks.append({'layer':layer,'source_holes':before_holes,'output_holes':after_holes,'via_copper_to_plane_gap_mm':gap,'added_copper_area_mm2':0,'removed_copper_area_mm2':previous.difference(current).area})
    assert len(checks)==2
    out={'passed':True,'control_only':True,'route_solver_used':False,'source_sha256':before['board_sha256'],'output_sha256':after['board_sha256'],'native_signal_net_preserved':'FLASH_CS','source_objects_preserved':len(before['objects']),'ground_native_pad_partitions_preserved':True,'ground_graph_components_before':len(old_groups),'ground_graph_components_after':len(new_groups),'reference_planes':checks}
    a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))

if __name__=='__main__':main()
