"""Exact public-relative inputs for this one v5 reference-review recipe."""
import gzip, hashlib, json, os
from pathlib import Path
HERE=Path(__file__).resolve().parent
DATA=HERE/'inputs'
CHECKPOINT=Path(os.environ.get('F722_REFERENCE_CHECKPOINT_ROOT',str(HERE.parent))).resolve()
OUTPUT=Path(os.environ.get('F722_REFERENCE_OUTPUT',str(HERE/'generated'))).resolve()
def sha(path,logical=False):
    h=hashlib.sha256()
    with (gzip.open(path,'rb') if logical else open(path,'rb')) as stream:
        for part in iter(lambda:stream.read(1048576),b''):h.update(part)
    return h.hexdigest()
def read(path):
    with (gzip.open(path,'rt') if str(path).endswith('.gz') else open(path)) as stream:return json.load(stream)
def verify():
    manifest=read(HERE/'MANIFEST.json')
    for name,row in manifest['package_files'].items():
        assert sha(HERE/name)==row['sha256'], 'Changed recipe file: '+name
    for name,row in manifest['public_inputs'].items():
        path=CHECKPOINT/row['checkpoint_relative_path']
        assert sha(path)==row['sha256'], 'Changed public input: '+name
        if row.get('logical_sha256'):
            assert sha(path,True)==row['logical_sha256'], 'Changed logical input: '+name
    return manifest
def geometry_context():
    assert os.environ.get('F722_REFERENCE_RUN_GRANTED')=='1', 'Use run_review.py --run-geometry explicitly.'
    assert __debug__, 'Do not run Python with optimization.'
    manifest=verify()
    assert OUTPUT.is_dir() and OUTPUT!=HERE and not OUTPUT.is_relative_to(CHECKPOINT), 'Use isolated output outside the checkpoint.'
    return manifest
def native_binding(row):
    return {'compressed':{'sha256':row['sha256']},'uncompressed':{'sha256':row['logical_sha256']}}
