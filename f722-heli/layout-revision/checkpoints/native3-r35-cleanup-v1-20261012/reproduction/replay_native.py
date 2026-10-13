#!/usr/bin/env python3
"""Verify this checkpoint; optionally replay its exact route recipe with KiCad 10.

Verification uses Python's standard library and never runs KiCad. Native replay
requires an explicit --rebuild destination and an installed pcbnew runtime.
It constructs a separate diagnostic board and is not a qualification workflow.
"""
import argparse
import gzip
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def verify():
    manifest = read(HERE / 'CONTENT-MANIFEST.json')
    for row in manifest['files']:
        p = HERE / row['path']
        assert p.stat().st_size == row['bytes'], p
        assert sha(p) == row['sha256'], p
        if p.name.endswith('.gz'):
            h = hashlib.sha256()
            with gzip.open(p, 'rb') as stream:
                for part in iter(lambda: stream.read(1048576), b''):
                    h.update(part)
            if row.get('logical_sha256'):
                assert h.hexdigest() == row['logical_sha256'], p
    current = read(HERE / 'CURRENT-STATE.json')
    assert sha(HERE / 'hardware/f722-heli.kicad_pcb') == current['board_sha256']
    assert len(list((HERE / 'hardware').rglob('*'))) >= 61
    assert len([p for p in (HERE / 'hardware').rglob('*') if p.is_file()]) == 61
    delta = read(HERE / 'recipe/normalized-delta.json')
    assert len(delta['remove_records']) == 17
    assert len(delta['add_tracks']) == 32 and len(delta['add_vias']) == 3
    assert delta['pose_changes'] == {'R35': [29.2, 23.0, 270, 'B.Cu']}
    assert len({r['record']['uuid'] for r in delta['remove_records']}) == 17
    assert not current['current_numerical_power_qualification']
    return current, delta

def rebuild(destination, current, delta):
    import pcbnew as pcb
    assert pcb.GetBuildVersion() == '10.0.6+dfsg-1', pcb.GetBuildVersion()
    assert not destination.exists(), 'Use a new output directory'
    refs = read(HERE / 'INPUT-REFERENCES.json')
    predecessor = HERE.parent / refs['predecessor_checkpoint_directory'] / 'hardware/f722-heli.kicad_pcb'
    assert sha(predecessor) == current['predecessor_board_sha256']
    assert shutil.disk_usage(destination.parent).free >= 128 * 1024 ** 2
    shutil.copytree(HERE / 'hardware', destination)
    board_path = destination / 'f722-heli.kicad_pcb'
    shutil.copy2(predecessor, board_path)
    board = pcb.LoadBoard(str(board_path))
    project = destination / 'f722-heli.kicad_pro'
    manager = pcb.GetSettingsManager()
    assert manager.LoadProject(str(project))
    board.SetProject(manager.GetProject(str(project)))
    nm = lambda value: round(value * 1000000)
    footprint = next(f for f in board.GetFootprints() if f.GetReference() == 'R35')
    assert [footprint.GetPosition().x, footprint.GetPosition().y, footprint.GetOrientationDegrees(), footprint.GetLayerName()] == [nm(29.2), nm(23.0), 90, 'B.Cu']
    footprint.SetOrientationDegrees(270)
    routes = {r.m_Uuid.AsString(): r for r in board.GetTracks()}
    for row in delta['remove_records']:
        uid = row['record']['uuid']
        assert uid in routes
        board.Remove(routes[uid])
    retained = []
    for row in delta['add_tracks'] + delta['add_vias']:
        if row['kind'] == 'track':
            item = pcb.PCB_TRACK(board)
            item.SetStart(pcb.VECTOR2I(*map(nm, row['start'])))
            item.SetEnd(pcb.VECTOR2I(*map(nm, row['end'])))
            item.SetWidth(nm(row['width']))
            item.SetLayer(board.GetLayerID(row['layer']))
        else:
            item = pcb.PCB_VIA(board)
            item.SetPosition(pcb.VECTOR2I(*map(nm, row['xy'])))
            item.SetWidth(nm(row['diameter']))
            item.SetDrill(nm(row['drill']))
            item.SetViaType(pcb.VIATYPE_THROUGH)
            item.SetLayerPair(pcb.F_Cu, pcb.B_Cu)
            item.SetFrontTentingMode(pcb.TENTING_MODE_TENTED)
            item.SetBackTentingMode(pcb.TENTING_MODE_TENTED)
        item.SetUuid(pcb.KIID(row['uuid']))
        item.SetNet(board.FindNet(row['net']))
        board.Add(item)
        retained.append(item)
    pcb.SaveBoard(str(board_path), board)
    board.SynchronizeNetsAndNetClasses(False)
    board.BuildConnectivity()
    assert pcb.ZONE_FILLER(board).Fill(board.Zones())
    pcb.SaveBoard(str(board_path), board)
    actual = sha(board_path)
    result = {'board_sha256': actual, 'expected_board_sha256': current['board_sha256'], 'exact_board_bytes': actual == current['board_sha256'], 'qualification': False}
    (destination / 'replay-result.json').write_text(json.dumps(result, indent=2) + '\n')
    assert result['exact_board_bytes'], 'Replay is diagnostic; exact native output differs'
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rebuild', type=Path)
    args = parser.parse_args()
    current, delta = verify()
    result = {'content_and_gzip_integrity': True, 'hardware_files': 61, 'native_replay_executed': False}
    if args.rebuild:
        result.update(rebuild(args.rebuild.resolve(), current, delta))
        result['native_replay_executed'] = True
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
