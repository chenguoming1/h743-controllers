from pathlib import Path
import hashlib,json,ast
P=Path(__file__).resolve().parent
base=Path('support/measure_reference.py').read_text()
start=base.index('import portable_paths as portable');end=base.index('refs=')
head="""import fcntl
ROOT=Path('unresolved/runtime')
lock=(ROOT/'execution.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
sys.path[:0]=[str(ROOT/'python-deps'),'support']
import finite_kernel as k
from shapely.geometry import LineString,Point,box
from shapely.ops import unary_union,nearest_points
from shapely import wkb
O=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
canon=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
write=lambda p,x:Path(p).write_text(canon(x)+'\\n')
C=Path('../native')
plan={'source_board_sha256':'7d9af57e9b22064fc6b2fd9cde4f2f5b72dc252cdbb1b104e706472bfdbbcdcb'}
manifest=read(C/'compressed-artifacts.json')
assert manifest['native']['compressed']['sha256']=='09771f922d59f4714bb42a7532369ce88534738d177e0125bf211a1ed52bd5db'
_binding={'candidate_board_sha256':'b31e6b9ca47e8e5a0b8967ec25f8390a66541b0c374ebedde77a39380e7d73ca','candidate_native_logical_sha256':'6c0485bf7e1098d0f51d8d63ca7e7a5ee6a26c21656192c0c967cd6e32917261'}
SOURCE_CACHE=Path('all-track-reference/inputs/source-all-track-projection.json.gz')
assert sha(SOURCE_CACHE)=='47ffdd7f7f7c54bf0bbd4ae7506b609c985ada5332c5eb1a26ca443b5cb07a52'
"""
base=base[:start]+head+base[end:]
base=base.replace("guard_path=portable.DATA/'selected-native-records.json'", "guard_path=Path('support/selected-native-records.json')")
base=base.replace("tag=sys.argv[2];extract(tag,Path(plan['paths']['source_native']) if tag=='source' else C/'after.native.json.gz',source_manifest['native'] if tag=='source' else manifest['native']);sys.exit()", "tag=sys.argv[2];assert tag=='candidate';extract(tag,C/'after.native.json.gz',manifest['native']);sys.exit()")
base=base.replace("a,b=[json.load(gzip.open(O/(tag+'-projection-input.json.gz'),'rt')) for tag in ['source','candidate']]", "a=json.load(gzip.open(SOURCE_CACHE,'rt'));b=json.load(gzip.open(O/'candidate-projection-input.json.gz','rt'))")
base=base.replace("a['native_logical_sha256']=='a4fddb679e9d73dd2a7b6300fa8888be47e30ab6f139bd5b78ab308d9192563c'", "a['native_logical_sha256']=='ae89889c542bca2c96abbdd48e66e70215ab7da84ceb9bccf7d619f8739825a5'")
old="ref,dielectric=refs[layer];oldplane,newplane=planes[0][ref],planes[1][ref];oldshape=wkb.loads(a['records'][uid]['shapes'][layer],hex=True);prior=oldshape.difference(oldplane);unsupported=shape.difference(newplane);newloss=shape.intersection(lost[ref]);centerloss=line.intersection(lost[ref]);gain=shape.intersection(gained[ref])"
new="""ref,dielectric=refs[layer];oldplane,newplane=planes[0][ref],planes[1][ref]
    retained=uid in a['records'];oldshape=wkb.loads(a['records'][uid]['shapes'][layer],hex=True) if retained else shape
    prior=oldshape.difference(oldplane);unsupported=shape.difference(newplane);newloss=shape.intersection(lost[ref]);centerloss=line.intersection(lost[ref]);gain=shape.intersection(gained[ref])
    base['source_record_present']=retained;base['source_projection_meaning']='actual retained source copper' if retained else 'candidate copper projected onto source plane, comparison only'
""".rstrip()
assert old in base;base=base.replace(old,new)
base=base.replace("'all_track_projections_sha256':sha(out)", "'all_track_projections_sha256':sha(out),'source_cache':{'path':str(SOURCE_CACHE),'sha256':sha(SOURCE_CACHE)},'removed_source_track_UUIDs':sorted(set(u for u,r in a['records'].items() if r['kind']=='track')-set(b['records']))")
base=base.replace("signal.alarm(120)","signal.alarm(60)")
base=base.replace("'seconds':120","'per_stage_seconds':60")
ast.parse(base)
with (P/'measure.py').open('x') as f:f.write(base)
print(hashlib.sha256(base.encode()).hexdigest())
