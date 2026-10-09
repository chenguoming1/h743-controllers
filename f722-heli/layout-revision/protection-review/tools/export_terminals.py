#!/usr/bin/env python3
"""Read-only, hash-bound native terminals and exact fitted TVS identities."""
import argparse
import hashlib
import json
from pathlib import Path

import pcbnew


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    before = sha(args.board)
    board = pcbnew.LoadBoard(str(args.board))
    refs = {f'D{i}' for i in range(3, 10)} | {f'U{i}' for i in range(12, 17)}
    terminals = []
    parts = []
    for footprint in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = footprint.GetReference()
        if ref in refs:
            parts.append({
                'reference': ref, 'uuid': footprint.m_Uuid.AsString(),
                'value': footprint.GetValue(),
                'footprint': str(footprint.GetFPID().GetLibNickname()) + ':' + str(footprint.GetFPID().GetLibItemName()),
                'fields': {field.GetName(): field.GetText() for field in footprint.GetFields()},
            })
        for pad in footprint.Pads():
            terminals.append({
                'key': ref + '.' + pad.GetNumber(), 'uuid': pad.m_Uuid.AsString(),
                'ref': ref, 'number': pad.GetNumber(), 'net': pad.GetNetname(),
                'xy_mm': [pad.GetPosition().x / 1e6, pad.GetPosition().y / 1e6],
                'copper_layers': [board.GetLayerName(layer) for layer in board.GetEnabledLayers().CuStack()
                                  if pad.IsOnLayer(layer) and pad.FlashLayer(layer)],
            })
    after = sha(args.board)
    assert before == after, 'Read-only source changed during export'
    output = {
        'schema': 'f722-tvs-native-terminal-inventory/v1',
        'board_path': str(args.board), 'board_sha256': before,
        'native_version': pcbnew.GetBuildVersion(), 'source_unchanged': True,
        'parts': parts, 'terminals': terminals,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps({'board_sha256': before, 'parts': len(parts), 'terminals': len(terminals)}))


if __name__ == '__main__':
    main()
