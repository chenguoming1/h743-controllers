#!/usr/bin/env python3
"""Verify paired candidate bytes or explicitly replay its KiCad construction.

Default mode is read-only and does not import KiCad. Native replay is separate
from restoring saved bytes and does not adopt or qualify this candidate.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal

HERE=Path(__file__).resolve().parent.parent
SOURCE=HERE.parent/'native2-in4-rx-v5-20261013/hardware/f722-heli.kicad_pcb'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())

def verify():
    paired=read(HERE/'PAIRED-HARDWARE.json');assert paired['file_count']==len(paired['files'])==61
    actual={p.relative_to(HERE/'hardware').as_posix() for p in (HERE/'hardware').rglob('*') if p.is_file()}
    assert actual=={r['path'] for r in paired['files']}
    for row in paired['files']:
        p=HERE/'hardware'/row['path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
    delta=read(HERE/'recipe/route-delta.json')
    assert len(delta['add_tracks'])==25 and len(delta['add_vias'])==2 and len(delta['remove_records'])==1
    assert not delta['pose_changes'] and not delta['pad_net_maps']
    assert delta['remove_records'][0]['record']['uuid']=='208a99a5-2f93-5966-9d3f-3c1b30f5b196'
    assert sha(HERE/'hardware/f722-heli.kicad_pcb')==delta['expected_board_sha256']
    return delta

def rebuild(out,delta):
    resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,)*2)
    resource.setrlimit(resource.RLIMIT_CPU,(300,300));signal.alarm(300)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    import pcbnew as pcb
    assert pcb.GetBuildVersion()=='10.0.6+dfsg-1',pcb.GetBuildVersion()
    assert sha(SOURCE)==delta['source_board_sha256']
    assert not out.exists() and out.parent.is_dir(),'Use a fresh destination'
    assert shutil.disk_usage(out.parent).free>=128*1024**2+4*1024**2
    shutil.copytree(HERE/'hardware',out);board_path=out/'f722-heli.kicad_pcb';shutil.copyfile(SOURCE,board_path)
    board=pcb.LoadBoard(str(board_path));manager=pcb.GetSettingsManager();project=out/'f722-heli.kicad_pro'
    assert manager.LoadProject(str(project));board.SetProject(manager.GetProject(str(project)))
    routes={r.m_Uuid.AsString():r for r in board.GetTracks()};nm=lambda x:round(x*1000000)
    for removal in delta['remove_records']:
        r=removal['record'];item=routes[r['uuid']]
        assert item.GetNetname()==r['net'] and item.GetWidth()==nm(r['width'])
        assert [item.GetStart().x,item.GetStart().y]==list(map(nm,r['start']))
        assert [item.GetEnd().x,item.GetEnd().y]==list(map(nm,r['end']))
        board.Remove(item)
    held=[]
    for row in delta['add_tracks']+delta['add_vias']:
        assert row['uuid'] not in routes
        if row['kind']=='track':
            item=pcb.PCB_TRACK(board);item.SetStart(pcb.VECTOR2I(*map(nm,row['start'])));item.SetEnd(pcb.VECTOR2I(*map(nm,row['end'])));item.SetWidth(nm(row['width']));item.SetLayer(board.GetLayerID(row['layer']))
        else:
            assert row['type']=='through' and row['tented']=={'B.Mask':True,'F.Mask':True}
            item=pcb.PCB_VIA(board);item.SetPosition(pcb.VECTOR2I(*map(nm,row['xy'])));item.SetWidth(nm(row['diameter']));item.SetDrill(nm(row['drill']));item.SetViaType(pcb.VIATYPE_THROUGH);item.SetLayerPair(pcb.F_Cu,pcb.B_Cu);item.SetFrontTentingMode(pcb.TENTING_MODE_TENTED);item.SetBackTentingMode(pcb.TENTING_MODE_TENTED)
        item.SetUuid(pcb.KIID(row['uuid']));item.SetNet(board.FindNet(row['net']));board.Add(item);held.append(item)
    pcb.SaveBoard(str(board_path),board);board.SynchronizeNetsAndNetClasses(False);board.BuildConnectivity()
    assert pcb.ZONE_FILLER(board).Fill(board.Zones());pcb.SaveBoard(str(board_path),board)
    actual=sha(board_path);result={'board_sha256':actual,'expected_board_sha256':delta['expected_board_sha256'],'exact_board_bytes':actual==delta['expected_board_sha256'],'adoption_or_qualification_claimed':False}
    (out/'replay-result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    assert result['exact_board_bytes'],'Fresh native result differs; preserve output and investigate'
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--rebuild-native',type=Path);args=parser.parse_args()
    delta=verify();result={'paired_hardware_files_verified':61,'source_bound_delta_verified':True,'native_replay_executed':False,'adoption_claimed':False}
    if args.rebuild_native:result.update(rebuild(args.rebuild_native.resolve(),delta));result['native_replay_executed']=True
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=='__main__':main()
