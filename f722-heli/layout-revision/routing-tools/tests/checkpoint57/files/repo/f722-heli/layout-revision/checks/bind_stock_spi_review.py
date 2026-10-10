"""Bind pinned stock-firmware arithmetic to unchanged native pad/BOM identities.

Run with KiCad's Python. This deliberately does not qualify routed timing.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pcbnew

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--board', type=Path, required=True)
p.add_argument('--parts', type=Path, required=True)
p.add_argument('--packet', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
before = sha(a.board)
inventory = json.loads((a.packet / 'native-pad-identities.json').read_text())
index = json.loads((a.packet / 'stock-source-index.json').read_text())
assert sha(a.parts) == index['authoritative_parts_sha256']
board = pcbnew.LoadBoard(str(a.board))
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
for row in inventory['rows']:
    fp = fps[row['ref']]
    assert fp.GetValue() == row['value'], row
    pads = [pad for pad in fp.Pads() if pad.GetNumber() == row['pad']]
    assert pads and sorted({p.GetNetname() for p in pads if p.GetNetname()}) == row['net'], row
assert sha(a.board) == before
out = {
    'board_sha256': before,
    'original_review_board_sha256': inventory['pcb_sha256'],
    'parts_sha256': sha(a.parts),
    'review_manifest_sha256': sha(a.packet / 'bundle-manifest.json'),
    'pad_inventory_sha256': sha(a.packet / 'native-pad-identities.json'),
    'binding_script_sha256': sha(__file__),
    'reviewed_native_pad_identities_equal': len(inventory['rows']),
    'passed': True,
    'scope': 'Pinned stock firmware clock arithmetic and reviewed device/pad/net identities apply. No new timing, loading, return-current, impedance or hardware qualification is claimed.'
}
a.out.write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out))
