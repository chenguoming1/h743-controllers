"""Create one isolated native through-via/antipad fixture; never route a design."""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'native-tools'))
from export_native_copper import export

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model',type=Path,required=True);ap.add_argument('--fixtures',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out=a.out.resolve();m=json.loads(a.model.read_text());fixtures=json.loads(a.fixtures.read_text());source=Path(m['physical_board']);assert hashlib.sha256(source.read_bytes()).hexdigest()==m['board_sha256'];assert not a.out.exists()
    position=next(c['xy'] for c in fixtures['cases'] if c['allowed']);before=json.loads(Path(m['physical_native']).read_text());a.out.parent.mkdir(parents=True,exist_ok=True)
    for suffix in ['.kicad_pro','.kicad_dru']:
        source_config=source.with_suffix(suffix)
        if source_config.exists():shutil.copyfile(source_config,a.out.with_suffix(suffix))
    shutil.copyfile(source,a.out);b=p.LoadBoard(str(a.out))
    via=p.PCB_VIA(b);via.SetPosition(p.VECTOR2I(*[round(x*1e6) for x in position]));via.SetWidth(450000);via.SetDrill(200000);via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetFrontTentingMode(p.TENTING_MODE_TENTED);via.SetBackTentingMode(p.TENTING_MODE_TENTED);via.SetNet(b.FindNet('FLASH_CS'));b.Add(via)
    track=p.PCB_TRACK(b);track.SetStart(via.GetPosition());track.SetEnd(p.VECTOR2I(round((position[0]+.4)*1e6),round(position[1]*1e6)));track.SetWidth(127000);track.SetLayer(p.F_Cu);track.SetNet(b.FindNet('FLASH_CS'));b.Add(track)
    assert via.GetNetname()=='FLASH_CS' and track.GetNetname()=='FLASH_CS'
    project=a.out.with_suffix('.kicad_pro');sm=p.GetSettingsManager()
    sm.LoadProject(str(project))
    b.SetProject(sm.GetProject(str(project)))
    b.SynchronizeNetsAndNetClasses(False)
    b.BuildConnectivity()
    assert p.ZONE_FILLER(b).Fill(b.Zones()),'Native zone refill failed'
    assert via.GetNetname()=='FLASH_CS' and track.GetNetname()=='FLASH_CS','Native refill reassigned signal copper'
    p.SaveBoard(str(a.out),b)
    after=export(a.out);by_uuid={o['uuid']:o for o in after['objects']};assert all(by_uuid[o['uuid']]==o for o in before['objects']);assert before['footprints']==after['footprints'] and before['edge_cuts']==after['edge_cuts']
    assert by_uuid[via.m_Uuid.AsString()]['net']=='FLASH_CS' and by_uuid[track.m_Uuid.AsString()]['net']=='FLASH_CS','Native connectivity reassigned the intended signal net'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==m['board_sha256']
    a.out.with_suffix('.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n');report={'control_only':True,'route_solver_used':False,'source_sha256':m['board_sha256'],'output_sha256':after['board_sha256'],'source_unchanged':True,'source_objects_preserved':len(before['objects']),'control_via_uuid':via.m_Uuid.AsString(),'control_track_uuid':track.m_Uuid.AsString(),'native_signal_net_preserved':'FLASH_CS','xy':position,'reference_zone_ids':m['regenerable_reference_zones'],'native_refill_performed':True}
    a.out.with_suffix('.control.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
