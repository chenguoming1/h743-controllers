"""Integrity-checked numeric mesh cache; never deserialize Python objects.

Geometry identity deliberately excludes linear solver methods. Every receipt
retains the original complete source hashes as well as the geometry fingerprint.
An absent/stale entry is a miss; a damaged or over-cap entry is a refusal.
"""
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import tempfile
import time
import zipfile

import numpy as np
import scipy
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
import shapely

import copper_fem as fem


SCHEMA = 'f722-fem-mesh-cache/v1'
_FLOAT_ARRAYS = {'K_data', 'xy', 'grad', 'areas'}
_INT_ARRAYS = {'K_indices', 'K_indptr', 'triangles', 'mapping', 'layer_ids', 'active', 'labels'}
_ARRAYS = _FLOAT_ARRAYS | _INT_ARRAYS
_MAX_METADATA_BYTES = 8 * 1024 * 1024


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _hash(value):
    return hashlib.sha256(value).hexdigest()


def _file_hash(handle):
    handle.seek(0)
    result = hashlib.sha256()
    for chunk in iter(lambda: handle.read(1024 * 1024), b''):
        result.update(chunk)
    return result.hexdigest()


def _builder():
    helpers = ['positive_finite', 'copper_material', 'polygon_set', 'parts',
               'polygonal_area', 'area_overlay', 'grid_coordinate', 'triangle_geometry',
               'native_geometry', 'contact_geometry', 'contact_keys',
               'contact_spec_geometry', 'barrel_resistance', 'DSU']
    sources = {name: _hash(inspect.getsource(getattr(fem, name)).encode()) for name in helpers}
    for name in ['__init__', 'check_time']:
        sources['Mesh.' + name] = _hash(inspect.getsource(getattr(fem.Mesh, name)).encode())
    sources['native_edge_noding.py'] = _hash(Path(__file__).with_name('native_edge_noding.py').read_bytes())
    return {'source_sha256': sources, 'fingerprint_sha256': _hash(_json(sources)),
            'dependencies': {'numpy': np.__version__, 'scipy': scipy.__version__,
                             'shapely': shapely.__version__, 'geos': shapely.geos_version_string}}


def mesh_binding(context, network, spacing):
    """Bind the unchanged source geometry and assembly, independent of solve limits."""
    manifest = context['manifest']
    geometry = manifest['files']['geometry']['sha256']
    binding = {'schema': SCHEMA, 'board_sha256': context['board_sha256'],
               'native_geometry_sha256': geometry, 'network': network,
               'contact_order': list(network['contacts']),
               'layer_order': context['geometry']['copper_layers'],
               'spacing_mm': spacing, 'material': context['material'],
               'stackup': context['stackup'],
               'native_edge_noding_enabled': 'native_edge_noding.py' in manifest.get('analysis_source_sha256', {}),
               'geometry_builder': _builder()}
    # File locations are deliberately excluded: a new activation directory may
    # contain identical immutable board and geometry bytes after solver edits.
    # Detach mutable caller dictionaries and reject nonfinite JSON numbers.
    return json.loads(_json(binding))


def _require(ok, reason):
    if not ok:
        raise fem.Refused('Mesh cache refused: ' + reason)


def _integer(value, lower, upper):
    return type(value) is int and lower <= value <= upper


def _metadata(mesh, binding):
    return {'schema': SCHEMA, 'binding': binding, 'n': int(mesh.n),
            'raw_nodes': len(mesh.xy), 'triangles': len(mesh.triangles),
            'nonzeros': int(mesh.K.nnz), 'layers': mesh.layers,
            'contact_nodes': [[key, int(value)] for key, value in mesh.contact_nodes.items()],
            'barrels': [list(row) for row in mesh.barrels],
            'sheet': mesh.sheet, 'thickness': mesh.thickness, 'spacing': mesh.spacing,
            'area_error_mm2': mesh.area_error_mm2, 'element_geometry': mesh.element_geometry,
            'native_edge_noding': mesh.native_edge_noding,
            # Mesh historically did not retain the actual tile count. Applying
            # its construction cap conservatively prevents relaxing a new cap.
            'construction_tile_cap': mesh.limits.max_tiles,
            'origin_source_sha256': {name: _hash(Path(__file__).with_name(name).read_bytes())
                                     for name in ['copper_fem.py', 'native_edge_noding.py', 'mesh_cache.py']}}


def _shape_spec(meta, limits):
    n, raw, triangles, nonzeros = (meta[key] for key in ['n', 'raw_nodes', 'triangles', 'nonzeros'])
    _require(_integer(raw, 1, limits.max_nodes) and _integer(n, 1, raw), 'node cap/shape')
    _require(_integer(triangles, 1, limits.max_triangles), 'triangle cap/shape')
    _require(_integer(meta['construction_tile_cap'], 1, limits.max_tiles), 'tile cap')
    _require(isinstance(meta['barrels'], list) and len(meta['barrels']) <= 4 * limits.max_nodes, 'barrel cap')
    _require(_integer(nonzeros, 1, 9 * triangles + 4 * len(meta['barrels'])), 'matrix nonzero cap')
    return {'K_data': (nonzeros,), 'K_indices': (nonzeros,), 'K_indptr': (n + 1,),
            'xy': (raw, 2), 'triangles': (triangles, 3), 'mapping': (raw,),
            'layer_ids': (raw,), 'active': None, 'labels': (n,),
            'grad': (triangles, 3, 2), 'areas': (triangles,)}


def _restore(meta, arrays, binding, limits):
    shapes = _shape_spec(meta, limits)
    _require(set(arrays) == _ARRAYS, 'unexpected numeric arrays')
    n, raw = meta['n'], meta['raw_nodes']
    for key, value in arrays.items():
        _require(value.dtype.kind in ('f' if key in _FLOAT_ARRAYS else 'iu') and value.dtype.itemsize <= 8,
                 'non-numeric array ' + key)
        _require(value.shape == shapes[key] if shapes[key] is not None else
                 value.ndim == 1 and 1 <= len(value) <= n, 'array shape ' + key)
        _require(np.all(np.isfinite(value)), 'nonfinite array ' + key)
    layers = meta['layers']
    _require(isinstance(layers, list) and layers == binding['layer_order'] and
             all(isinstance(layer, str) for layer in layers) and len(set(layers)) == len(layers), 'layers')
    contacts = meta['contact_nodes']
    _require(isinstance(contacts, list) and 2 <= len(contacts) <= limits.max_terminals, 'terminal cap')
    _require(all(isinstance(row, list) and len(row) == 2 and isinstance(row[0], str) and
                 _integer(row[1], 0, n - 1) for row in contacts), 'contact indices')
    _require([row[0] for row in contacts] == binding['contact_order'] and
             len({row[1] for row in contacts}) == len(contacts), 'contact identity')
    for key, upper in [('triangles', raw), ('mapping', n), ('layer_ids', len(layers)),
                       ('active', n), ('K_indices', n), ('labels', n)]:
        _require(np.all((arrays[key] >= 0) & (arrays[key] < upper)), 'index range ' + key)
    indptr = arrays['K_indptr']
    _require(indptr[0] == 0 and indptr[-1] == meta['nonzeros'] and np.all(indptr[1:] >= indptr[:-1]), 'CSR row pointers')
    _require(np.array_equal(np.unique(arrays['mapping']), np.arange(n)), 'incomplete reduced-node mapping')
    _require(np.all(arrays['areas'] > 0), 'nonpositive element area')
    triangle_layers = arrays['layer_ids'][arrays['triangles']]
    _require(np.all(triangle_layers == triangle_layers[:, :1]), 'triangle crosses copper layers')
    for name, expected in [('sheet', binding['material']['sheet_ohm']),
                           ('thickness', binding['material']['thickness_mm']), ('spacing', binding['spacing_mm'])]:
        _require(math.isfinite(meta[name]) and meta[name] > 0 and meta[name] == expected, 'material/spacing ' + name)
    _require(math.isfinite(meta['area_error_mm2']), 'nonfinite area receipt')
    condition = meta['element_geometry']['maximum_condition_bound']
    _require(math.isfinite(condition) and 0 < condition <= limits.max_element_condition, 'element condition cap')
    _require(isinstance(meta['native_edge_noding'], dict), 'native-edge receipt')
    for row in meta['barrels']:
        _require(isinstance(row, list) and len(row) == 6, 'barrel shape')
        a, b, resistance, uid, la, lb = row
        _require(_integer(a, 0, n - 1) and _integer(b, 0, n - 1) and
                 isinstance(resistance, (int, float)) and math.isfinite(resistance) and resistance > 0 and
                 isinstance(uid, str) and la in layers and lb in layers, 'barrel data')
    matrix = csr_matrix((arrays['K_data'], arrays['K_indices'], indptr), shape=(n, n))
    matrix.check_format(full_check=True)
    _require(matrix.has_canonical_format, 'noncanonical CSR matrix')
    components, labels = connected_components(matrix, directed=False)
    _require(np.array_equal(labels, arrays['labels']), 'component labels')
    contact_labels = {int(labels[row[1]]) for row in contacts}
    _require(len(contact_labels) == 1 and
             np.array_equal(np.flatnonzero(labels == next(iter(contact_labels))), arrays['active']), 'active component')
    mesh = fem.Mesh.__new__(fem.Mesh)
    mesh.limits = limits
    for key in ['xy', 'triangles', 'mapping', 'layer_ids', 'active', 'grad', 'areas', 'labels']:
        setattr(mesh, key, arrays[key])
    for key in ['n', 'layers', 'sheet', 'thickness', 'spacing', 'area_error_mm2',
                'element_geometry', 'native_edge_noding']:
        setattr(mesh, key, meta[key])
    mesh.K, mesh.components = matrix, components
    mesh.contact_nodes = dict(contacts)
    mesh.barrels = [tuple(row) for row in meta['barrels']]
    mesh.floating_nodes = n - len(mesh.active)
    mesh.xyz = [(layers[int(layer)], float(x), float(y)) for layer, (x, y) in zip(mesh.layer_ids, mesh.xy)]
    mesh.start_time = time.monotonic()
    return mesh


def _receipt(meta, key, metadata_bytes, hit):
    return {'schema': SCHEMA, 'hit': hit, 'binding_sha256': key, 'binding': meta['binding'],
            'arrays_sha256': meta['arrays_sha256'], 'metadata_sha256': _hash(metadata_bytes),
            'origin_source_sha256': meta['origin_source_sha256'],
            'geometry_builder_sha256': meta['binding']['geometry_builder']['fingerprint_sha256']}


def save_mesh(mesh, cache_dir, binding):
    """Publish the content-addressed NPZ first, then atomically commit metadata."""
    root = Path(cache_dir)
    root.mkdir(parents=True, exist_ok=True)
    key = _hash(_json(binding))
    arrays = {name: getattr(mesh, name) for name in _ARRAYS - {'K_data', 'K_indices', 'K_indptr'}}
    arrays.update(K_data=mesh.K.data, K_indices=mesh.K.indices, K_indptr=mesh.K.indptr)
    meta = _metadata(mesh, binding)
    # Validate before publication, using the same checks that protect readers.
    _restore(meta, arrays, binding, mesh.limits)
    temporary = []
    try:
        with tempfile.NamedTemporaryFile(dir=root, prefix='.mesh-', suffix='.npz', delete=False) as handle:
            temporary.append(Path(handle.name))
            np.savez(handle, **arrays)
            handle.flush()
            os.fsync(handle.fileno())
        with temporary[-1].open('rb') as handle:
            meta['arrays_sha256'] = _file_hash(handle)
        meta['arrays_file'] = key + '.' + meta['arrays_sha256'] + '.npz'
        os.replace(temporary[-1], root / meta['arrays_file'])
        metadata_bytes = _json({'payload': meta, 'payload_sha256': _hash(_json(meta))})
        _require(len(metadata_bytes) <= _MAX_METADATA_BYTES, 'metadata size cap')
        with tempfile.NamedTemporaryFile(dir=root, prefix='.mesh-', suffix='.json', delete=False) as handle:
            temporary.append(Path(handle.name))
            handle.write(metadata_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary[-1], root / (key + '.json'))
    finally:
        for path in temporary:
            path.unlink(missing_ok=True)
    mesh.mesh_cache_info = _receipt(meta, key, metadata_bytes, False)
    return mesh.mesh_cache_info


def load_mesh(cache_dir, binding, limits):
    """Read bounded numeric arrays only, restoring the caller's current limits."""
    key = _hash(_json(binding))
    metadata_path = Path(cache_dir) / (key + '.json')
    try:
        with metadata_path.open('rb') as handle:
            metadata_bytes = handle.read(_MAX_METADATA_BYTES + 1)
    except FileNotFoundError:
        return None
    try:
        _require(len(metadata_bytes) <= _MAX_METADATA_BYTES, 'metadata size cap')
        envelope = json.loads(metadata_bytes, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        meta = envelope['payload']
        _require(_hash(_json(meta)) == envelope['payload_sha256'], 'metadata hash mismatch')
        _require(meta['schema'] == SCHEMA, 'metadata schema')
        if _json(meta['binding']) != _json(binding):
            return None
        shapes = _shape_spec(meta, limits)
        digest = meta['arrays_sha256']
        _require(isinstance(digest, str) and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest), 'array digest')
        filename = key + '.' + digest + '.npz'
        _require(meta['arrays_file'] == filename, 'array filename is not hash-bound')
        # All stored arrays use at most eight bytes per scalar. Check archive
        # sizes and NPY headers before np.load can allocate based on a header.
        budget = sum(math.prod(shape) * 8 if shape is not None else meta['n'] * 8
                     for shape in shapes.values()) + len(_ARRAYS) * 4096
        with (Path(cache_dir) / filename).open('rb') as handle:
            _require(os.fstat(handle.fileno()).st_size <= budget, 'archive size cap')
            _require(_file_hash(handle) == digest, 'array hash mismatch')
            handle.seek(0)
            with zipfile.ZipFile(handle) as archive:
                members = archive.infolist()
                _require(len(members) == len(_ARRAYS) and {item.filename for item in members} ==
                         {name + '.npy' for name in _ARRAYS}, 'archive members')
                _require(sum(item.file_size for item in members) <= budget, 'expanded archive size cap')
                for member in members:
                    name = member.filename[:-4]
                    with archive.open(member) as stream:
                        version = np.lib.format.read_magic(stream)
                        _require(version in [(1, 0), (2, 0)], 'unsupported numeric header')
                        reader = np.lib.format.read_array_header_1_0 if version == (1, 0) else np.lib.format.read_array_header_2_0
                        shape, _, dtype = reader(stream, max_header_size=4096)
                        _require(dtype.kind in ('f' if name in _FLOAT_ARRAYS else 'iu') and dtype.itemsize <= 8,
                                 'unsafe/non-numeric array ' + name)
                        expected = shapes[name]
                        _require(shape == expected if expected is not None else
                                 len(shape) == 1 and 1 <= shape[0] <= meta['n'], 'array header shape ' + name)
                        _require(math.prod(shape) * dtype.itemsize == member.file_size - stream.tell(), 'array byte count')
            handle.seek(0)
            with np.load(handle, allow_pickle=False) as archive:
                arrays = {name: archive[name] for name in _ARRAYS}
        mesh = _restore(meta, arrays, binding, limits)
        mesh.mesh_cache_info = _receipt(meta, key, metadata_bytes, True)
        return mesh
    except fem.Refused:
        raise
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, zipfile.BadZipFile) as exc:
        raise fem.Refused('Mesh cache refused: invalid or unreadable entry: ' + str(exc)) from exc
