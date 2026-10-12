"""Exact input projection for comparison, not transfer of electrical qualification."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import resource

resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block:=stream.read(1048576):h.update(block)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['board','board-sha','native','native-stored-sha','native-logical-sha','out']:
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--native-logical-bytes',type=int,required=True)
    args=parser.parse_args()
    board,native_path,out=map(Path,[args.board,args.native,args.out])
    assert not out.exists() and out.resolve().is_relative_to(HERE)
    assert sha(board)==args.board_sha and sha(native_path)==args.native_stored_sha
    assert 0<args.native_logical_bytes<64*1024**2
    with gzip.open(native_path,'rb') as stream:raw=stream.read(args.native_logical_bytes+1)
    assert len(raw)==args.native_logical_bytes and hashlib.sha256(raw).hexdigest()==args.native_logical_sha
    native=json.loads(raw);del raw
    assert native['board_sha256']==args.board_sha and native['source_unchanged'] is True
    scope=json.loads((HERE/'preparation/scope.json').read_text())
    with gzip.open(HERE/'preparation/electrical-model.template.json.gz','rt') as stream:model=json.load(stream)
    spec=importlib.util.spec_from_file_location('fingerprint_board_parser',ROOT/'power-recovery-prep/prepare_final_power.py')
    parser_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser_module)
    tree=parser_module.parse_board(board.read_text())
    stackup=parser_module.one(parser_module.one(tree,'setup'),'stackup')
    holes=[o for o in native['objects'] if o.get('drill')]
    networks={}
    for net in scope['pad_inventory']:
        objects=[o for o in native['objects'] if o.get('net')==net]
        zones=[z for z in native['zones'] if not z['rule'] and z['net']==net]
        networks[net]={'object_count':len(objects),'ordered_objects_sha256':digest(objects),
                       'zone_count':len(zones),'ordered_saved_zones_sha256':digest(zones)}
    # Full hole-owner records intentionally exceed the solver's void-only
    # dependency: a comparison may conservatively refuse, never omit a bore.
    dependency={'networks':networks,'all_ordered_physical_hole_owners_sha256':digest(holes),
      'physical_hole_count':len(holes),'copper_layers_sha256':digest(native['copper_layers']),
      'outline_with_npth_sha256':digest(native['outline_with_npth']),
      'edge_cuts_sha256':digest(native['edge_cuts']),'source_stackup_AST_sha256':digest(stackup),
      'entire_footprint_inventory_sha256':digest(native['footprints']),
      'scope_sha256':digest(scope),'electrical_model_sha256':digest(model)}
    report={'schema':'f722-exact-power-input-projection/v1','source':{'board_sha256':args.board_sha,
      'native_stored_sha256':args.native_stored_sha,'native_logical_sha256':args.native_logical_sha},
      'dependencies':dependency,'dependency_sha256':digest(dependency),
      'projection_preserves_source_object_and_zone_order':True,'ignored_foreign_undrilled_copper_not_used_by_DC_model':True,
      'same_geometry_does_not_transfer_DRC_or_physical_acceptance':True,
      'electrical_qualification_or_source_equivalence_claimed':False,
      'requires_future_source_comparison_and_review':True,'native_or_geometry_solver_executed':False}
    out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'output':str(out),'sha256':sha(out),'dependency_sha256':report['dependency_sha256']}))

if __name__=='__main__':main()
