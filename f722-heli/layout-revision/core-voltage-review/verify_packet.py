#!/usr/bin/env python3
"""Verify compact packet integrity and retained facts. No writes/network/solver."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
if not __debug__:
    raise RuntimeError('Run without Python optimization; assertion checks are required.')
def read(name):
    return json.loads((root / name).read_text())

manifest = read('MANIFEST.json')
for name, expected in manifest['files'].items():
    path = root / name
    if path.resolve().is_relative_to(root) is False:
        raise RuntimeError('Path escapes packet: ' + name)
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise RuntimeError('SHA-256 mismatch: ' + name)

inventory = read('native-core-pin-inventory.json')
assert inventory['board_sha256'] == '246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7'
pads = {p['key']: p for p in inventory['pads']}
pads_by_uuid = {p['uuid']: p for p in inventory['pads']}
expected_roles = {
    'U1.1': 'VBAT', 'U1.13': 'VDDA', 'U1.19': 'VDD', 'U1.32': 'VDD',
    'U1.48': 'VDD', 'U1.64': 'VDD', 'U2.5': 'VDDIO', 'U2.8': 'VDD',
    'U3.8': 'VCC', 'U4.2': 'CSB', 'U4.6': 'VDDIO', 'U4.8': 'VDD',
    'U9.6': 'VOS', 'U11.4': 'EN', 'U11.6': 'IN',
}
for pin, role in expected_roles.items():
    assert pads[pin]['pin_name'] == role, (pin, role)

facts = read('historical-contact-findings.json')
assert facts['historical_result_sha256'] == '28dfe7bcff16f08e3919be7063cf06727ab25678e3585e86f6acfda26e0742f1'
assert len(facts['injection_vertices']) == 10
bad = facts['incorrect_supply_injections']
assert {x['element']['p'] for x in bad} == {'U10.4', 'U11.4'}
assert len(bad) == 77
for x in bad:
    assert x['native_pads'][0]['pin_name'] == 'EN'
    assert x['actual_supply_pads'][0]['pin_name'] == 'IN'
    assert x['native_pads'][0]['net'] == x['actual_supply_pads'][0]['net']

successor = read('candidate41-pin-identity-check.json')
assert successor['candidate41_board_sha256'] == '539d9547eb8c4d5984481293ae10cee34355ee838dff11ab43b00cca270ceae2'
assert successor['parts_byte_identical']
assert all(successor['schematics_byte_identical'].values())
for p in successor['pads']:
    prior = pads_by_uuid[p['uuid']]
    assert (p['key'], p['net'], p['pin_name']) == (prior['key'], prior['net'], prior['pin_name'])

limits = read('supply-limits.json')
assert limits['universal_functional_floor_V'] is None
assert limits['acceptance_status'].startswith('unqualified')
subcheck = read('power-path-subcheck/audit.json')
assert subcheck['checks']['all_frozen_hashes_match']
assert subcheck['checks']['freeze_file_count'] == 28
assert not subcheck['checks']['numerical_solver_run']
assert not subcheck['checks']['canonical_inputs_modified']
print(json.dumps({
    'packet_hashes_verified': len(manifest['files']),
    'retained_role_checks': len(expected_roles),
    'historical_incorrect_supply_elements': len(bad),
    'candidate41_role_correlations': len(successor['pads']),
    'status': 'Packet integrity and retained-fact consistency passed.',
    'not_established': 'Original source re-extraction, manufacturer-document authenticity, electrical solution, connectivity, board acceptance or device qualification.',
}, indent=2))
