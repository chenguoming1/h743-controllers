#!/usr/bin/env python3
"""Create disposable native test boards; never modify the input board.

The controls intentionally contain broken or bypassed paths and are NOT
candidate designs. Run with the same KiCad Python as export_native_copper.py.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pcbnew as p
from export_native_copper import export

SOURCE_SHA256 = '4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f'
BROKEN_TRACK = '3620cc10-ae54-4464-ac81-9289adb6a79e'


def vec(xy):
    return p.VECTOR2I(round(xy[0] * 1e6), round(xy[1] * 1e6))


def add_track(board, net, start, end, layer=p.F_Cu):
    t = p.PCB_TRACK(board)
    t.SetStart(vec(start)); t.SetEnd(vec(end)); t.SetWidth(p.FromMM(.15))
    t.SetLayer(layer); t.SetNetCode(net.GetNetCode()); board.Add(t)
    return t.m_Uuid.AsString()


def add_via(board, net, center):
    v = p.PCB_VIA(board)
    v.SetPosition(vec(center)); v.SetWidth(p.FromMM(.6)); v.SetDrill(p.FromMM(.3))
    v.SetViaType(p.VIATYPE_THROUGH); v.SetLayerPair(p.F_Cu, p.B_Cu)
    v.SetNetCode(net.GetNetCode()); board.Add(v)
    return v.m_Uuid.AsString()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--published-board', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    before = hashlib.sha256(args.published_board.read_bytes()).hexdigest()
    if before != SOURCE_SHA256:
        raise ValueError('Controls require the pinned published board')
    args.out.mkdir(parents=True, exist_ok=True)
    results = []
    for kind in ['broken_source_lead', 'direct_front_bypass', 'plated_back_bypass']:
        b = p.LoadBoard(str(args.published_board))
        pads = {f.GetReference() + '.' + a.GetNumber(): a for f in b.GetFootprints() for a in f.Pads()}
        net = b.FindNet('USB_CC1'); source = pads['J1.A5'].GetPosition(); target = pads['R14.1'].GetPosition()
        source = [source.x / 1e6, source.y / 1e6]; target = [target.x / 1e6, target.y / 1e6]
        changes = []
        if kind == 'broken_source_lead':
            removed = [x for x in b.GetTracks() if x.m_Uuid.AsString() == BROKEN_TRACK]
            assert len(removed) == 1
            b.Remove(removed[0]); changes = [BROKEN_TRACK]
        elif kind == 'direct_front_bypass':
            changes.append(add_track(b, net, source, target))
        else:
            changes += [add_via(b, net, point) for point in [source, target]]
            changes.append(add_track(b, net, source, target, p.B_Cu))
        path = args.out / (kind + '.kicad_pcb')
        p.SaveBoard(str(path), b)
        snapshot = export(path)
        (args.out / (kind + '.json')).write_text(json.dumps(snapshot, separators=(',', ':')) + '\n')
        results.append({'kind': kind, 'board_sha256': snapshot['board_sha256'], 'changed_object_uuids': changes})
    # A single native track passes through the actual clamp pad. Correct
    # subtraction must split it; preserving connectivity by object UUID fails.
    b = p.BOARD(); net = p.NETINFO_ITEM(b, 'TEST_SIGNAL'); b.Add(net)
    for ref, x, size in [('J1', 10, .5), ('D1', 11, .6), ('R1', 12, .5)]:
        fp = p.FOOTPRINT(b); fp.SetReference(ref); fp.SetValue('GEOMETRY_CONTROL')
        fp.SetPosition(vec([x, 10])); b.Add(fp)
        pad = p.PAD(fp); pad.SetNumber('1'); pad.SetAttribute(p.PAD_ATTRIB_SMD)
        pad.SetShape(p.PAD_SHAPE_RECT); pad.SetSize(vec([size, .6]))
        pad.SetLayerSet(p.PAD.SMDMask()); pad.SetPosition(vec([x, 10])); pad.SetNetCode(net.GetNetCode()); fp.Add(pad)
    track_uuid = add_track(b, net, [10, 10], [12, 10])
    path = args.out / 'single_object_split.kicad_pcb'; p.SaveBoard(str(path), b)
    snapshot = export(path)
    (args.out / 'single_object_split.json').write_text(json.dumps(snapshot, separators=(',', ':')) + '\n')
    results.append({'kind': 'single_object_split', 'board_sha256': snapshot['board_sha256'], 'spanning_track_uuid': track_uuid})
    assert hashlib.sha256(args.published_board.read_bytes()).hexdigest() == before
    (args.out / 'manifest.json').write_text(json.dumps({'source_sha256': before, 'source_unchanged': True, 'controls': results}, indent=2) + '\n')
    print(json.dumps({'native_controls': len(results), 'source_unchanged': True, 'out': str(args.out)}))


if __name__ == '__main__':
    main()
