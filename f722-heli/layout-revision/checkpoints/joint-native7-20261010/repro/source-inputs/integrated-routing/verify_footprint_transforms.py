"""Predict declared orthogonal KiCad pose operations; require exact footprint identity.

This is a separate path from translation-only verification. It permits no arbitrary
pad, net, property, graphic, land or courtyard editing, and gives no DRC acceptance.
"""
from pathlib import Path
import argparse, hashlib, json, sys, tempfile
import pcbnew as p
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ordinary-routing/tests/mpn-parity'))
from apply_metadata_copy import parse, children, properties, value, shape

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def check_shapes(before, after, predicted, changes):
    def keyed(root):
        rows=children(root,'footprint')
        result={properties(f)['Reference'].items[2].value:f for f in rows}
        assert len(rows)==len(result)==156
        return result
    old,new,expected=map(keyed,(before,after,predicted))
    assert set(old)==set(new)==set(expected) and changes and set(changes)<=set(old)
    rows=[]
    for ref in sorted(old):
        assert value(old[ref],'uuid')==value(new[ref],'uuid')==value(expected[ref],'uuid')
        if ref not in changes:
            assert shape(old[ref])==shape(new[ref])==shape(expected[ref]), ('undeclared footprint change',ref)
        else:
            assert shape(new[ref])==shape(expected[ref]), ('unpredicted footprint structure',ref)
            assert shape(old[ref])!=shape(new[ref]), ('empty transformation',ref)
            rows.append({'reference':ref,'uuid':value(old[ref],'uuid'),**changes[ref]})
    return rows

def verify(before,after,declaration):
    before,after,declaration=map(Path,(before,after,declaration))
    manifest=json.loads(declaration.read_text());old,new=sha(before),sha(after)
    assert manifest['schema']=='f722-declared-footprint-transforms/v1'
    assert manifest['source_board_sha256']==old and manifest['board_sha256']==new
    changes=manifest['changes'];assert changes
    b=p.LoadBoard(str(before));fps={f.GetReference():f for f in b.GetFootprints()}
    assert len(fps)==156 and set(changes)<=set(fps)
    for ref,change in changes.items():
        assert set(change)=={'before','after','flip_left_right'}
        start,end=change['before'],change['after'];assert len(start)==len(end)==4
        assert all(v[3] in ('F.Cu','B.Cu') and v[2]%90==0 for v in (start,end))
        f=fps[ref]
        assert f.GetPosition()==p.VECTOR2I(round(start[0]*1e6),round(start[1]*1e6))
        assert (f.GetOrientationDegrees()-start[2])%360==0 and f.GetLayerName()==start[3]
        if start[3]!=end[3]:
            assert type(change['flip_left_right']) is bool
            f.Flip(f.GetPosition(),change['flip_left_right'])
        else:
            assert change['flip_left_right'] is None
        f.SetOrientationDegrees(end[2]);f.SetPosition(p.VECTOR2I(round(end[0]*1e6),round(end[1]*1e6)))
        assert f.GetLayerName()==end[3] and (f.GetOrientationDegrees()-end[2])%360==0
    with tempfile.TemporaryDirectory(prefix='f722-pose-proof-') as td:
        predicted=Path(td)/'predicted.kicad_pcb';p.SaveBoard(str(predicted),b)
        rows=check_shapes(parse(before.read_text()),parse(after.read_text()),parse(predicted.read_text()),changes)
        semantic=hashlib.sha256(json.dumps([shape(f) for f in children(parse(predicted.read_text()),'footprint')],separators=(',',':')).encode()).hexdigest()
    assert sha(before)==old and sha(after)==new
    return {'schema':'f722-verified-footprint-transforms/v1','passed':True,
            'source_board_sha256':old,'board_sha256':new,'declaration_sha256':sha(declaration),
            'script_sha256':sha(__file__),'native_version':p.GetBuildVersion(),
            'footprints':156,'exact_unchanged_footprints':156-len(rows),
            'transformations':rows,'predicted_footprint_semantic_sha256':semantic,
            'all_footprint_structure_matches_declared_native_transform':True,
            'scope':'Only declared KiCad Flip/orthogonal orientation/position operations; '
                    'all resulting native footprint structures match exactly. No arbitrary '
                    'net/pad/land/property/courtyard changes; no mechanical/electrical acceptance.'}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('before',type=Path);ap.add_argument('after',type=Path);ap.add_argument('declaration',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    result=verify(a.before,a.after,a.declaration);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
