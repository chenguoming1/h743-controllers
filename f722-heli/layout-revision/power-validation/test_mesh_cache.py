"""Small synthetic cache tests. No native board geometry is built or solved."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np
from shapely.geometry import box

from copper_fem import Limits, Mesh, Refused
import mesh_cache as cache


def fixture():
    material = {'sheet_ohm': .01, 'thickness_mm': .015, 'plating_mm': .015}
    context = {'manifest': {'files': {'board': {'path': 'synthetic.kicad_pcb'},
                                     'geometry': {'sha256': 'b' * 64}},
                            'analysis_source_sha256': {}},
               'board_sha256': 'a' * 64, 'geometry': {'copper_layers': ['F.Cu']},
               'material': material, 'stackup': {'layer_z_mm': {'F.Cu': .0075}}}
    network = {'net': 'synthetic', 'contacts': {'a': {'pad': 'J1.1', 'layer': 'F.Cu'},
                                             'b': {'pad': 'J2.1', 'layer': 'F.Cu'}}}
    mesh = Mesh({'F.Cu': box(0, 0, 4, 1).union(box(5, 0, 6, 1))},
                {'a': ('F.Cu', box(0, 0, .3, 1)), 'b': ('F.Cu', box(3.7, 0, 4, 1))},
                .5, material['sheet_ohm'], material['thickness_mm'])
    return context, network, mesh


def changed_geometry_helper(*args, **kwargs):
    raise AssertionError('Fingerprint-only test helper must never run')


class MeshCacheTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.context, self.network, self.mesh = fixture()
        self.binding = cache.mesh_binding(self.context, self.network, .5)

    def save(self):
        return cache.save_mesh(self.mesh, self.root, self.binding)

    def rewrite_arrays(self, change):
        """Give malformed arrays valid transport hashes to exercise validation."""
        metadata_path = next(self.root.glob('*.json'))
        envelope = json.loads(metadata_path.read_text())
        meta = envelope['payload']
        with np.load(self.root / meta['arrays_file'], allow_pickle=False) as archive:
            arrays = {key: archive[key] for key in archive.files}
        change(arrays)
        temporary = self.root / 'modified.npz'
        np.savez(temporary, **arrays)
        digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
        filename = metadata_path.stem + '.' + digest + '.npz'
        temporary.rename(self.root / filename)
        meta.update(arrays_sha256=digest, arrays_file=filename)
        envelope['payload_sha256'] = hashlib.sha256(cache._json(meta)).hexdigest()
        metadata_path.write_bytes(cache._json(envelope))

    def test_roundtrip_equivalence_conservation_and_provenance(self):
        original = self.mesh.solve({'a': 1., 'b': -1.}, 'b')
        saved = self.save()
        restored = cache.load_mesh(self.root, self.binding, Limits())
        actual = restored.solve({'a': 1., 'b': -1.}, 'b')
        self.assertEqual(restored.xyz, self.mesh.xyz)
        self.assertGreater(restored.floating_nodes, 0)
        self.assertEqual(restored.floating_nodes, self.mesh.floating_nodes)
        for name in ['triangles', 'xy', 'mapping', 'layer_ids', 'active', 'grad', 'areas', 'labels']:
            np.testing.assert_array_equal(getattr(restored, name), getattr(self.mesh, name))
        self.assertEqual((restored.K != self.mesh.K).nnz, 0)
        self.assertEqual(restored.contact_nodes, self.mesh.contact_nodes)
        self.assertEqual(actual['contact_voltage_V'], original['contact_voltage_V'])
        self.assertAlmostEqual(actual['copper_loss_W'], .034, places=10)
        self.assertAlmostEqual(actual['copper_loss_W'], actual['port_power_W'], places=12)
        self.assertLess(actual['KCL_max_residual_A'], 1e-8)
        self.assertFalse(saved['hit'])
        self.assertTrue(restored.mesh_cache_info['hit'])
        for name in ['binding', 'binding_sha256', 'arrays_sha256', 'metadata_sha256', 'origin_source_sha256']:
            self.assertEqual(saved[name], restored.mesh_cache_info[name])
        self.assertEqual(len(saved['origin_source_sha256']['copper_fem.py']), 64)

    def test_solver_changes_preserve_binding_geometry_changes_invalidate(self):
        self.save()
        with patch.object(Mesh, 'solve', changed_geometry_helper), patch.object(Mesh, 'impedance', changed_geometry_helper):
            self.assertEqual(cache.mesh_binding(self.context, self.network, .5), self.binding)
        with patch.object(cache.fem, 'triangle_geometry', changed_geometry_helper):
            changed = cache.mesh_binding(self.context, self.network, .5)
        self.assertNotEqual(changed, self.binding)
        self.assertIsNone(cache.load_mesh(self.root, changed, Limits()))

    def test_stale_bindings_are_misses(self):
        self.save()
        for field in ['board_sha256', 'native_geometry_sha256', 'spacing_mm']:
            changed = copy.deepcopy(self.binding)
            changed[field] = 1. if field == 'spacing_mm' else 'c' * 64
            self.assertIsNone(cache.load_mesh(self.root, changed, Limits()))
        changed = copy.deepcopy(self.binding)
        changed['network']['contacts']['a']['pad'] = 'J3.1'
        self.assertIsNone(cache.load_mesh(self.root, changed, Limits()))
        changed = copy.deepcopy(self.binding)
        changed['material']['sheet_ohm'] *= 2
        self.assertIsNone(cache.load_mesh(self.root, changed, Limits()))

    def test_relocated_identical_sources_reuse_binding(self):
        self.save()
        relocated = copy.deepcopy(self.context)
        relocated['manifest']['files']['board']['path'] = '../new-activation/source.kicad_pcb'
        relocated['manifest']['files']['geometry']['path'] = '../new-activation/native-geometry.json'
        binding = cache.mesh_binding(relocated, self.network, .5)
        self.assertEqual(binding, self.binding)
        restored = cache.load_mesh(self.root, binding, Limits())
        self.assertTrue(restored.mesh_cache_info['hit'])

    def test_tampered_bytes_refused(self):
        self.save()
        archive = next(self.root.glob('*.npz'))
        with archive.open('r+b') as handle:
            handle.seek(30)
            value = handle.read(1)
            handle.seek(30)
            handle.write(bytes([value[0] ^ 1]))
        with self.assertRaisesRegex(Refused, 'hash mismatch'):
            cache.load_mesh(self.root, self.binding, Limits())

    def test_metadata_tampering_refused(self):
        self.save()
        path = next(self.root.glob('*.json'))
        envelope = json.loads(path.read_text())
        envelope['payload']['n'] += 1
        path.write_text(json.dumps(envelope))
        with self.assertRaisesRegex(Refused, 'metadata hash mismatch'):
            cache.load_mesh(self.root, self.binding, Limits())

    def test_numeric_loader_disables_pickle_and_object_payloads_refuse(self):
        self.save()
        with patch.object(cache.np, 'load', wraps=np.load) as loader:
            cache.load_mesh(self.root, self.binding, Limits())
            self.assertFalse(loader.call_args.kwargs['allow_pickle'])
        self.rewrite_arrays(lambda arrays: arrays.update(xy=arrays['xy'].astype(object)))
        with patch.object(cache.np, 'load', side_effect=AssertionError('Unsafe header reached loader')):
            with self.assertRaisesRegex(Refused, 'unsafe/non-numeric'):
                cache.load_mesh(self.root, self.binding, Limits())

    def test_invalid_indices_and_nonfinite_numeric_values_refuse(self):
        self.save()
        self.rewrite_arrays(lambda arrays: arrays['triangles'].__setitem__((0, 0), len(self.mesh.xy)))
        with self.assertRaisesRegex(Refused, 'index range triangles'):
            cache.load_mesh(self.root, self.binding, Limits())
        self.save()
        self.rewrite_arrays(lambda arrays: arrays['grad'].__setitem__((0, 0, 0), np.nan))
        with self.assertRaisesRegex(Refused, 'nonfinite array grad'):
            cache.load_mesh(self.root, self.binding, Limits())

    def test_wrong_shape_refused_before_numpy_allocation(self):
        self.save()
        self.rewrite_arrays(lambda arrays: arrays.update(xy=arrays['xy'].ravel()))
        with patch.object(cache.np, 'load', side_effect=AssertionError('Invalid header reached loader')):
            with self.assertRaisesRegex(Refused, 'array header shape xy'):
                cache.load_mesh(self.root, self.binding, Limits())

    def test_caller_limits_and_fresh_clock_retained(self):
        self.save()
        limits = Limits(max_iterations=7, max_seconds=3.)
        restored = cache.load_mesh(self.root, self.binding, limits)
        self.assertIs(restored.limits, limits)
        self.assertEqual(restored.limits.max_iterations, 7)
        self.assertLess(time.monotonic() - restored.start_time, 1.)
        for limits in [Limits(max_nodes=len(self.mesh.xy) - 1),
                       Limits(max_triangles=len(self.mesh.triangles) - 1),
                       Limits(max_terminals=1), Limits(max_element_condition=1.),
                       Limits(max_tiles=1)]:
            with self.assertRaises(Refused):
                cache.load_mesh(self.root, self.binding, limits)

    def test_barrel_layer_roundtrip(self):
        context = copy.deepcopy(self.context)
        context['geometry']['copper_layers'] = ['F.Cu', 'B.Cu']
        context['stackup']['layer_z_mm']['B.Cu'] = 1.5
        network = copy.deepcopy(self.network)
        network['contacts']['b']['layer'] = 'B.Cu'
        record = [{'outer': list(box(1.5, 0, 2.5, 1).exterior.coords), 'holes': []}]
        barrel = {'uuid': 'synthetic-via', 'copper': {'F.Cu': record, 'B.Cu': record},
                  'barrel_layers': ['F.Cu', 'B.Cu'],
                  'drill': {'start': [2, .5], 'end': [2, .5], 'width': .3}}
        mesh = Mesh({'F.Cu': box(0, 0, 4, 1), 'B.Cu': box(0, 0, 4, 1)},
                    {'a': ('F.Cu', box(0, 0, .3, 1)), 'b': ('B.Cu', box(3.7, 0, 4, 1))},
                    .5, .01, .015, [barrel], context['stackup']['layer_z_mm'])
        binding = cache.mesh_binding(context, network, .5)
        cache.save_mesh(mesh, self.root, binding)
        restored = cache.load_mesh(self.root, binding, Limits())
        self.assertEqual(mesh.xyz, restored.xyz)
        self.assertEqual(mesh.barrels, restored.barrels)
        before = mesh.solve({'a': 1., 'b': -1.}, 'b')
        after = restored.solve({'a': 1., 'b': -1.}, 'b')
        self.assertEqual(before['barrels'], after['barrels'])
        self.assertAlmostEqual(after['copper_loss_W'], after['port_power_W'], places=12)


if __name__ == '__main__':
    unittest.main()
