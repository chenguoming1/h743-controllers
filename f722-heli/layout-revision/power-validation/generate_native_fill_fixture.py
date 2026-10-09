#!/usr/bin/env python3
"""Generate a tiny saved-fill contour regression with KiCad's Python runtime.

No project board is loaded or saved. Only a synthetic polygon set is created.
"""
import argparse
import json
from pathlib import Path
import pcbnew as p
from exact_native_contours import native_filled_polygons, doubled_area


def snapshot(shape):
    def points(ring):
        return [[ring.CPoint(i).x,ring.CPoint(i).y] for i in range(ring.PointCount())]
    return [{'outer_nm':points(shape.Outline(i)),
             'holes_nm':[points(shape.Hole(i,h)) for h in range(shape.HoleCount(i))]}
            for i in range(shape.OutlineCount())]


def build_fixture():
    shape=p.SHAPE_POLY_SET()
    outer=shape.NewOutline()
    for x,y in [(0,0),(10,0),(10,10),(0,10)]:shape.Append(x*1000000,y*1000000,outer)
    for ring in [[(2,2),(2,4),(4,4),(4,2)],[(6,6),(6,8),(8,8),(8,6)]]:
        hole=shape.NewHole(outer)
        for x,y in ring:shape.Append(x*1000000,y*1000000,outer,hole)
    island=shape.NewOutline()
    for x,y in [(20,0),(21,0),(21,1),(20,1)]:shape.Append(x*1000000,y*1000000,island)
    before=snapshot(shape)
    explicit,explicit_receipts=native_filled_polygons(shape)
    assert snapshot(shape)==before
    fractured=p.SHAPE_POLY_SET(shape)
    fractured.Fracture()
    assert snapshot(shape)==before
    raw=snapshot(fractured)
    decoded,receipts=native_filled_polygons(fractured)
    assert snapshot(fractured)==raw
    assert shape.Area()==fractured.Area()==93000000000000
    assert sum(len(q['holes']) for q in decoded)==2 and len(decoded)==2
    assert sum(q['doubled_area_before_nm2'] for q in receipts)==186000000000000
    assert all(q['doubled_area_before_nm2']==q['doubled_area_after_nm2'] for q in receipts)
    assert all(q['maximum_coordinate_displacement_nm']==0 and q['boundary_edges_preserved_exactly'] for q in receipts)
    return {'schema':'synthetic-native-fill-fixture/v1','native_version':p.Version(),
            'source':'Synthetic SHAPE_POLY_SET; no project board loaded or saved',
            'expected_area_mm2':93,'expected_outlines':2,'expected_holes':2,
            'explicit_input':before,'explicit_output':explicit,'explicit_receipts':explicit_receipts,
            'fractured_input':raw,'decoded_output':decoded,'decoded_receipts':receipts,
            'input_objects_unchanged':True,'passed':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.suffix!='.json':raise SystemExit('Use a separate .json fixture output')
    result=build_fixture()
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['native_version','passed','expected_area_mm2','expected_outlines','expected_holes','input_objects_unchanged']}))


if __name__=='__main__':main()
