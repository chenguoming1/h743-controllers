#!/usr/bin/env python3
"""Exact structured solver-input comparison. No mesh, repair, source transfer or solve."""
import argparse,json,hashlib
from pathlib import Path
from validate_static import sha256,stackup_centers
from copper_fem import Refused

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def compare(reference,other,reference_board,other_board,ledger):
    left=json.loads(Path(reference).read_text());right=json.loads(Path(other).read_text());case=json.loads(Path(ledger).read_text())
    for data,board in [(left,reference_board),(right,other_board)]:
        if data['board_sha256']!=sha256(board)or data['source_unchanged']is not True:raise Refused('Stale or changed native source')
        if data['schema']!='kicad-native-copper/v1'or data['units']!='mm':raise Refused('Unexpected native geometry schema/units')
    nets={n['net']for n in case['networks']};keys={key for n in case['networks']for spec in n['contacts'].values()for key in spec.get('pads',[spec.get('pad')])}
    def inputs(data,board):
        objects=sorted(data['objects'],key=lambda r:r['uuid'])
        return {'export_precision':{k:data[k]for k in ['units','maximum_polygon_error_mm','copper_error_location','pad_cut_error_location','native_version']},
         'copper_layers':data['copper_layers'],'outline_with_npth':data['outline_with_npth'],
         'stackup':stackup_centers(board,data['copper_layers']),
         'selected_net_objects':[r for r in objects if r.get('net')in nets],
         'selected_net_fills':sorted([r for r in data['zones']if not r['rule']and r.get('net')in nets],key=lambda r:r['uuid']),
         'all_physical_drills':[{'uuid':r['uuid'],'kind':r['kind'],'drill':r['drill'],'barrel_layers':r.get('barrel_layers'),'plated':r.get('plated')}for r in objects if r.get('drill')],
         'finite_port_pads':[r for r in objects if r['kind']=='pad'and r.get('key')in keys],
         'material_assumptions':case['material'],'contact_definitions':case['networks']}
    a=inputs(left,reference_board);b=inputs(right,other_board)
    rows={k:{'identical':a[k]==b[k],'reference_sha256':digest(a[k]),'compared_sha256':digest(b[k]),
       **({'reference_count':len(a[k]),'compared_count':len(b[k])}if isinstance(a[k],list)else{})}for k in a}
    changed={}
    for key in ['selected_net_objects','selected_net_fills','all_physical_drills','finite_port_pads']:
        aa={x['uuid']:x for x in a[key]};bb={x['uuid']:x for x in b[key]}
        changed[key]={'added_uuids':sorted(set(bb)-set(aa)),'removed_uuids':sorted(set(aa)-set(bb)),
         'modified_uuids':[x for x in sorted(set(aa)&set(bb))if aa[x]!=bb[x]]}
    return {'schema':'f722-exact-power-geometry-comparison/v1','reference_board_sha256':left['board_sha256'],
      'compared_board_sha256':right['board_sha256'],'reference_native_sha256':sha256(reference),'compared_native_sha256':sha256(other),
      'port_ledger_sha256':sha256(ledger),'nets':sorted(nets),'contacts':sum(len(n['contacts'])for n in case['networks']),
      'categories':rows,'differences':changed,'exact_structured_inputs_identical':all(r['identical']for r in rows.values()),
      'material_is_modeled_not_measured':True,'numeric_cache_transferred':False,'board_result_rebound':False,
      'scope':'Exact native object/fill/drill/port/stackup input comparison only. Fresh final-source binding remains required after any later board change.',
      'script_sha256':sha256(__file__)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['reference','other','reference-board','other-board','ledger','out']:p.add_argument('--'+name,required=True)
    a=p.parse_args();r=compare(a.reference,a.other,a.reference_board,a.other_board,a.ledger)
    Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k]for k in ['reference_board_sha256','compared_board_sha256','nets','contacts','exact_structured_inputs_identical','differences']}))

if __name__=='__main__':main()
