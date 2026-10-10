from pathlib import Path
import pcbnew as p,json,hashlib
D=Path(__file__).resolve().parent/'candidate03';out=D/'f722-heli.kicad_pcb';b=p.LoadBoard(str(out));sm=p.GetSettingsManager();assert sm.LoadProject(str(D/'f722-heli.kicad_pro'));b.SetProject(sm.GetProject(str(D/'f722-heli.kicad_pro')));b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(out),b);print(json.dumps({'filled_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
