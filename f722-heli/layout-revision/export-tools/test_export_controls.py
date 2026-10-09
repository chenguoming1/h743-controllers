#!/usr/bin/env python3
"""Focused fault injection for export gates and file-to-native checks."""
import copy
import csv
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch
from argparse import ArgumentParser, Namespace
import sys

import pcbnew
import native_export as ex


class ExportControls(unittest.TestCase):
    hardware_path = None
    control_path = None

    @classmethod
    def setUpClass(cls):
        cls.hardware = cls.hardware_path.resolve()
        cls.board = pcbnew.LoadBoard(str(cls.hardware/'f722-heli.kicad_pcb'))
        cls.inv = ex.native_inventory(cls.board)
        cls.parts = json.loads((cls.hardware/'parts.json').read_text())
        cls.control = cls.control_path.resolve()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='test-only-', dir=ex.HERE)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def receipt_fixture(self):
        identity = {k: '1'*64 for k in ['source_pcb_sha256','source_parts_sha256','source_tree_sha256']}
        (self.root/'test-only-evidence.txt').write_text('SYNTHETIC TEST FIXTURE. Not board evidence.\n')
        index = {'schema': 'f722-export-receipts-v1', **identity, 'receipts': {}}
        for name in ex.REQUIRED_RECEIPTS:
            receipt = {'schema': 'f722-validation-receipt-v1', 'scope': name, 'result': 'pass',
                       **identity, 'method': 'Synthetic unit-test fixture', 'limitations': 'Not a real board review',
                       'native_warning_signature_sha256': '2'*64,
                       'evidence': [{'path': 'test-only-evidence.txt', 'sha256': ex.sha(self.root/'test-only-evidence.txt')}]}
            ex.write_json(self.root/f'{name}.json', receipt)
            index['receipts'][name] = {'path': f'{name}.json', 'sha256': ex.sha(self.root/f'{name}.json')}
        ex.write_json(self.root/'index.json', index)
        return identity, index

    def test_complete_receipt_fixture_accepted(self):
        identity, _ = self.receipt_fixture()
        self.assertEqual(set(ex.verify_receipts(self.root/'index.json', identity, '2'*64)), set(ex.REQUIRED_RECEIPTS))

    def test_missing_receipts_rejected(self):
        with self.assertRaisesRegex(ex.GateError, 'require a validation receipt'):
            ex.verify_receipts(None, {}, '')

    def test_existing_output_rejected_without_claiming_ownership(self):
        sentinel = self.root/'sentinel.txt'
        sentinel.write_text('Existing package must remain untouched')
        args = Namespace(hardware=self.hardware, output=self.root)
        with self.assertRaisesRegex(ex.GateError, 'already exists'):
            ex.run(args)
        self.assertFalse(args.output_created)
        self.assertEqual(sentinel.read_text(), 'Existing package must remain untouched')

    def test_output_inside_hardware_rejected(self):
        args = Namespace(hardware=self.hardware, output=self.hardware/'must-not-be-created')
        with self.assertRaisesRegex(ex.GateError, 'inside the hardware source'):
            ex.run(args)
        self.assertFalse(args.output_created)
        self.assertFalse(args.output.exists())

    def test_wrong_pcbnew_version_rejected(self):
        args = Namespace(hardware=self.hardware, output=self.root/'version-test',
                         expected_pcb_sha256=ex.HISTORICAL_PCB)
        with patch.object(ex.pcbnew, 'Version', return_value='10.0.7'):
            with self.assertRaisesRegex(ex.GateError, '10.0.6 Python runtime'):
                ex.run(args)

    def test_wrong_cli_version_rejected(self):
        args = Namespace(hardware=self.hardware, output=self.root/'version-test',
                         expected_pcb_sha256=ex.HISTORICAL_PCB, kicad_cli=self.root/'not-executed-cli')
        with patch.object(ex.subprocess, 'check_output', return_value='10.0.7\n'):
            with self.assertRaisesRegex(ex.GateError, 'CLI version mismatch'):
                ex.run(args)

    def test_stale_source_rejected(self):
        identity, _ = self.receipt_fixture()
        identity['source_pcb_sha256'] = '3'*64
        with self.assertRaisesRegex(ex.GateError, 'stale/missing source_pcb'):
            ex.verify_receipts(self.root/'index.json', identity, '2'*64)

    def test_missing_scope_rejected(self):
        identity, index = self.receipt_fixture()
        del index['receipts']['electrical-power-review']
        ex.write_json(self.root/'index.json', index)
        with self.assertRaisesRegex(ex.GateError, 'required scopes'):
            ex.verify_receipts(self.root/'index.json', identity, '2'*64)

    def test_changed_evidence_rejected(self):
        identity, _ = self.receipt_fixture()
        (self.root/'test-only-evidence.txt').write_text('Tampered')
        with self.assertRaisesRegex(ex.GateError, 'Evidence hash changed'):
            ex.verify_receipts(self.root/'index.json', identity, '2'*64)

    def test_unreviewed_warning_rejected(self):
        identity, _ = self.receipt_fixture()
        with self.assertRaisesRegex(ex.GateError, 'Warning review'):
            ex.verify_receipts(self.root/'index.json', identity, '3'*64)

    def test_changed_receipt_rejected(self):
        identity, _ = self.receipt_fixture()
        with (self.root/'parts-identity.json').open('a') as f:
            f.write(' ')
        with self.assertRaisesRegex(ex.GateError, 'Receipt bytes changed'):
            ex.verify_receipts(self.root/'index.json', identity, '2'*64)

    def test_parts_footprint_mismatch_rejected(self):
        parts = copy.deepcopy(self.parts)
        parts['R16']['proposed_footprint'] = 'wrong:package'
        with self.assertRaisesRegex(ex.GateError, 'footprint mismatch: R16'):
            ex.verify_identities(self.inv, parts)

    def test_silent_manual_header_drop_rejected(self):
        parts = copy.deepcopy(self.parts)
        del parts['J2']
        with self.assertRaisesRegex(ex.GateError, 'identity set differs'):
            ex.verify_identities(self.inv, parts)

    def test_position_rotation_change_rejected(self):
        rows = ex.read_csv(self.control/'assembly'/'native-all-pos.csv')
        rows[0]['Rot'] = str(float(rows[0]['Rot'])+90)
        ex.write_csv(self.root/'native-all-pos.csv', list(rows[0]), [list(row.values()) for row in rows])
        with self.assertRaisesRegex(ex.GateError, 'coordinate/rotation mismatch'):
            ex.build_assembly(self.root, self.inv, self.parts)

    def fabrication_fixture(self):
        for name in ['gerbers', 'drill']:
            shutil.copytree(self.control/name, self.root/name)

    def test_changed_slot_size_rejected(self):
        self.fabrication_fixture()
        p = self.root/'drill'/'f722-heli-NPTH.drl'
        p.write_text(p.read_text().replace('T1C0.710', 'T1C0.810'))
        with self.assertRaisesRegex(ex.GateError, 'NPTH native/Excellon'):
            ex.verify_fabrication(self.root, self.inv)

    def test_shifted_paste_flash_rejected(self):
        self.fabrication_fixture()
        p = self.root/'gerbers'/'f722-heli-F_Paste.gtp'
        contents, count = re.subn(r'X(-?\d+)Y(-?\d+)D03\*',
                                  lambda m: f'X{int(m[1])+1000000}Y{m[2]}D03*', p.read_text(), count=1)
        self.assertEqual(count, 1)
        p.write_text(contents)
        with self.assertRaisesRegex(ex.GateError, 'F.Paste native pad/flash'):
            ex.verify_fabrication(self.root, self.inv)


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--hardware', type=Path, required=True, help='Paired historical control hardware directory')
    parser.add_argument('--control', type=Path, required=True, help='Regenerated historical control output directory')
    args, remaining = parser.parse_known_args()
    ExportControls.hardware_path = args.hardware
    ExportControls.control_path = args.control
    sys.argv = [sys.argv[0], *remaining]
    unittest.main(verbosity=2)
