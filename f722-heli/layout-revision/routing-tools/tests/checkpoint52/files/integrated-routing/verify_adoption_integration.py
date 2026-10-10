"""Bind an explicit cumulative coordinated owner proof to the adopted source."""
def verify(report, source_sha256, board_sha256):
    assert report['schema'] == 'f722-owner-coordinated-integration/v1'
    assert report['passed'] is True
    assert report['source_board_sha256'] == source_sha256
    assert report['board_sha256'] == board_sha256
    assert report['allowed_changed_nets']
    return True
