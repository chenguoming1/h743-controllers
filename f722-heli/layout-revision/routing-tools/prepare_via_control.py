"""Choose native-bound ordinary-via clearance fixtures, without editing a PCB."""
import argparse
import json
from pathlib import Path
from shapely.geometry import Polygon, Point, box
from shapely import unary_union, STRtree

def geom(polygons):
    return unary_union([Polygon(p['outer'], p.get('holes', [])) for p in polygons])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    m=json.loads(a.model.read_text());n=json.loads(Path(m['physical_native']).read_text());logical='FLASH_CS'
    assert m['aliases'][logical]=='FLASH_CS'
    reference=set(m['regenerable_reference_zones']);assert len(reference)==2
    assert not any(g['label']==uid+':fill' for uid in reference for g in m['guards'])
    assert not {'In1.Cu','In4.Cu'} & set(m['routable_layers'])
    native_refs=[geom(z['filled'][l]) for z in n['zones'] if z['uuid'] in reference for l in z['layers']]
    all_guards=[g for g in m['guards'] if g['kind']=='via' or logical not in g['owners']]
    shapes=[geom(g['polygons']) for g in all_guards];tree=STRtree(shapes);clear=[]
    for yi in range(2,49):
        for xi in range(2,81):
            xy=[xi*.5,yi*.5];p=Point(xy)
            if not all(g.contains(p.buffer(.6)) for g in native_refs):continue
            candidates=tree.query(box(xy[0]-.4,xy[1]-.4,xy[0]+.4,xy[1]+.4))
            if any(shapes[i].distance(p)<.225+all_guards[i]['clearance']+.0001 for i in candidates):continue
            clear.append(xy)
            if len(clear)==3:break
        if len(clear)==3:break
    assert clear,'No independently clear through-via fixture found'
    objects=n['objects'];same=next(o for o in objects if o['kind']=='pad' and o['net']=='FLASH_CS' and o['smd']);foreign=next(o for o in objects if o['kind']=='pad' and o['net'] not in {'','FLASH_CS'} and o['smd']);track=next(o for o in objects if o['kind']=='track' and o['net']!='FLASH_CS');hole=next(o for o in objects if o['kind']=='via')
    cases=[{'label':'empty_reference_plane_'+str(i+1),'xy':xy,'allowed':True} for i,xy in enumerate(clear)]
    cases += [{'label':'foreign_pad','native_uuid':foreign['uuid'],'xy':foreign['xy'],'allowed':False},
              {'label':'foreign_fixed_track','native_uuid':track['uuid'],'xy':[(a+b)/2 for a,b in zip(track['start'],track['end'])],'allowed':False},
              {'label':'existing_drill','native_uuid':hole['uuid'],'xy':hole['xy'],'allowed':False},
              {'label':'same_net_smt_mask','native_uuid':same['uuid'],'xy':same['xy'],'allowed':False}]
    out={'board_sha256':m['board_sha256'],'logical_net':logical,'reference_zone_ids':sorted(reference),'cases':cases,'point_selection':'Native reference-fill interior and actual guard geometry; no board mutation','reference_fill_obstacles_absent':True,'reference_signal_layers_disabled':True}
    a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))

if __name__=='__main__':main()
