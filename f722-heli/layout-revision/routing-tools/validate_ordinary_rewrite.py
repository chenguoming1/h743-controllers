"""Validate a source-bound, explicit ordinary route replacement allowance."""
import hashlib
import json
from pathlib import Path


def validate(before, after, receipt_path, source_native_sha256):
    receipt_path = Path(receipt_path)
    r = json.loads(receipt_path.read_text())
    assert r['schema'] == 'f722-coordinated-servo2-native-construction/v1'
    assert r['source_board_sha256'] == before['board_sha256']
    assert r['source_native_sha256'] == source_native_sha256
    assert r['physical_net'] == 'SERVO2_MCU'
    old = {o['uuid']: o for o in before['objects']}
    now = {o['uuid']: o for o in after['objects']}
    allowed = set(r['mutable_route_uuids'])
    assert allowed and allowed <= set(old)
    assert all(old[uid]['kind'] in ['track', 'via'] and old[uid]['net'] == r['physical_net'] for uid in allowed)
    changed = [uid for uid in old.keys() & now.keys() if old[uid] != now[uid]]
    removed = sorted(old.keys() - now.keys())
    added = sorted(now.keys() - old.keys())
    assert not changed, 'Existing UUID geometry was edited; explicit replacement requires new UUIDs'
    assert set(removed) <= allowed, 'Undeclared source object removed'
    assert all(now[uid]['kind'] in ['track', 'via'] and now[uid]['net'] == r['physical_net'] for uid in added)
    assert all(old[uid] == now.get(uid) for uid in old.keys() - allowed)
    assert all(before[key] == after[key] for key in ['footprints', 'edge_cuts', 'copper_layers'])
    return allowed, dict(passed=True, receipt_sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
                        physical_net=r['physical_net'], permitted_source_route_uuids=sorted(allowed),
                        actual_removed_uuids=removed, actual_added_uuids=added,
                        existing_uuid_records_edited=[], source_objects_outside_allowance_exact=len(old)-len(allowed),
                        all_pads_power_critical_and_other_net_objects_exact=True,
                        scope='Explicit ordinary route replacement only. Connectivity, pad cuts, entries, process, reference and numerical qualification remain separate.')
