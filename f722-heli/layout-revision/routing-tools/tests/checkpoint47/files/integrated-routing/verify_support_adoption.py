"""Typed support-proof adapter; does not infer a pass from missing fields."""
import hashlib
import json
from pathlib import Path


def verify(report, prior, source_sha, board_sha, directory):
    assert report['board_sha256'] == board_sha
    schema = report.get('schema')
    typed = schema in ('f722-complete-DSM-support-audit-binding/v1', 'f722-I2C-complete-support-binding/v1')
    if typed:
        assert report['passed'] is True and report['source_board_sha256'] == source_sha
        name = report['audit']
        assert Path(name).name == name
        path = Path(directory) / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == report['audit_sha256']
        audit = json.loads(path.read_text())
        assert audit['passed'] is True and all(v is True for v in audit['gates'].values())
        assert audit['source_board_sha256'] == source_sha
        if schema == 'f722-I2C-complete-support-binding/v1':
            assert audit['board_sha256'] == board_sha and audit['numerical_power_VCAP_applicable'] is False
            assert audit['nets'] == report['nets']
        else:
            assert audit['candidate_board_sha256'] == board_sha
            assert audit['support_nets'] == report['nets']
    else:
        assert report.get('schema') in (None, 'f722-native-support-audit/v1'), 'Unknown support-proof schema'
    assert set(report['nets']) == set(prior['nets']), 'Power support inventory changed'
    for net, row in report['nets'].items():
        groups = row['groups']
        if typed:
            assert row['passed'] is True and row['source_groups_exactly_preserved'] is True
        else:
            assert row['pad_group_count'] == 1 and row.get('complete', True)
        assert len(groups) == 1, ('Power support regression', net)
        actual = groups[0]['pad_uuids']
        expected = [u for group in prior['nets'][net]['groups'] for u in group['pad_uuids']]
        assert len(actual) == len(set(actual)) and set(actual) == set(expected), ('Power pad inventory changed', net)
    return {'passed': True, 'nets': len(report['nets']), 'typed_audit_binding_checked': typed}
