#!/usr/bin/env python3
"""Verify the paired checkpoint or replay its ten-track KiCad construction.

Default verification is read-only and uses the Python standard library.
--rebuild-native requires KiCad 10.0.6 and a fresh destination. It refills a
separate copy and compares exact PCB bytes; it does not confer qualification.
"""
import argparse
import gzip
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
PREDECESSOR = HERE.parent/'native3-r35-cleanup-v1-20261012'

def digest(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):value.update(block)
    return value.hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def verify():
    hardware=read(HERE/'PAIRED-HARDWARE.json')
    assert len(hardware['files'])==hardware['file_count']==61
    actual_files={p.relative_to(HERE/'hardware').as_posix() for p in (HERE/'hardware').rglob('*') if p.is_file()}
    assert actual_files=={row['path'] for row in hardware['files']}
    for row in hardware['files']:
        path=HERE/'hardware'/row['path']
        assert path.stat().st_size==row['bytes'] and digest(path)==row['sha256'],path
    delta=read(HERE/'recipe/route-delta.json')
    assert len(delta['add_tracks'])==10 and not delta['add_vias'] and not delta['remove_records'] and not delta['pose_changes'] and not delta['pad_net_maps']
    assert len({r['uuid'] for r in delta['add_tracks']})==10
    assert all(r['net']=='PORT_C_RX_MCU' and r['layer']=='In4.Cu' and r['width']==0.127 for r in delta['add_tracks'])
    assert digest(HERE/'hardware/f722-heli.kicad_pcb')==delta['expected_board_sha256']
    manifest=HERE/'CONTENT-MANIFEST.json'
    if manifest.exists():
        for row in read(manifest)['files']:
            path=HERE/row['path']
            assert path.stat().st_size==row['bytes'] and digest(path)==row['sha256'],path
            if row.get('logical_sha256'):
                value=hashlib.sha256()
                with gzip.open(path,'rb') as stream:
                    for block in iter(lambda:stream.read(1024*1024),b''):value.update(block)
                assert value.hexdigest()==row['logical_sha256'],path
    return delta

def rebuild(destination,delta):
    import pcbnew as pcb
    assert pcb.GetBuildVersion()=='10.0.6+dfsg-1',pcb.GetBuildVersion()
    source=PREDECESSOR/'hardware/f722-heli.kicad_pcb'
    assert digest(source)==delta['source_board_sha256']
    assert not destination.exists(),'Use a fresh destination'
    assert shutil.disk_usage(destination.parent).free>=128*1024**2
    shutil.copytree(HERE/'hardware',destination)
    board_path=destination/'f722-heli.kicad_pcb'
    shutil.copyfile(source,board_path)
    board=pcb.LoadBoard(str(board_path))
    project=destination/'f722-heli.kicad_pro'
    manager=pcb.GetSettingsManager()
    assert manager.LoadProject(str(project))
    board.SetProject(manager.GetProject(str(project)))
    source_ids={track.m_Uuid.AsString() for track in board.GetTracks()}
    held=[]
    nm=lambda value:round(value*1000000)
    for row in delta['add_tracks']:
        assert row['uuid'] not in source_ids
        item=pcb.PCB_TRACK(board)
        item.SetStart(pcb.VECTOR2I(*map(nm,row['start'])))
        item.SetEnd(pcb.VECTOR2I(*map(nm,row['end'])))
        item.SetWidth(nm(row['width']))
        item.SetLayer(board.GetLayerID(row['layer']))
        item.SetUuid(pcb.KIID(row['uuid']))
        item.SetNet(board.FindNet(row['net']))
        board.Add(item)
        held.append(item)
    pcb.SaveBoard(str(board_path),board)
    board.SynchronizeNetsAndNetClasses(False)
    board.BuildConnectivity()
    assert pcb.ZONE_FILLER(board).Fill(board.Zones())
    pcb.SaveBoard(str(board_path),board)
    actual=digest(board_path)
    result={'board_sha256':actual,'expected_board_sha256':delta['expected_board_sha256'],'exact_board_bytes':actual==delta['expected_board_sha256'],'manufacturing_release':False}
    (destination/'replay-result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    assert result['exact_board_bytes'],'KiCad reproduction differs; do not replace recorded evidence'
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rebuild-native',type=Path)
    args=parser.parse_args()
    delta=verify()
    result={'paired_files_verified':61,'native_replay_executed':False,'content_manifest_verified':(HERE/'CONTENT-MANIFEST.json').exists()}
    if args.rebuild_native:
        result.update(rebuild(args.rebuild_native.resolve(),delta))
        result['native_replay_executed']=True
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=='__main__':main()
