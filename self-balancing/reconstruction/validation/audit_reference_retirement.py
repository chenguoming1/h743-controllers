#!/usr/bin/python3
import os,pathlib,json,hashlib,sys,argparse
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-p6-kicad')
import pcbnew as p
D=pathlib.Path(__file__).resolve().parent.parent;ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=pathlib.Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--out',type=pathlib.Path,required=True);args=ap.parse_args();S=D/'input-p5/controller.kicad_pcb';T=args.candidate;sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();packet=json.load(open(D/'retirement-dispositions.json'));assert sha(S)==packet['source_sha256'] and sha(T)==args.sha256==packet['candidate_sha256'];target=p.LoadBoard(str(T));source=p.LoadBoard(str(S));retired=set(packet['authorized_removed_via_ids']);assert len(retired)==6;seen=[];hold=[]
for t in list(source.GetTracks()):
 if t.m_Uuid.AsString() in retired:assert isinstance(t,p.PCB_VIA);seen.append(t.m_Uuid.AsString());source.Remove(t);hold.append(t)
assert set(seen)==retired
source.BuildConnectivity();p.ZONE_FILLER(source).Fill(source.Zones())
def plane(b,l):
 x=p.SHAPE_POLY_SET()
 for z in b.Zones():
  if z.GetNetname()=='GND' and not z.GetIsRuleArea() and z.IsOnLayer(l) and z.HasFilledPolysForLayer(l):x.BooleanAdd(z.GetFilledPolysList(l))
 return x
oracle={l:plane(source,l) for l in [p.In1_Cu,p.In3_Cu,p.In4_Cu]};rows=[]
for l,expected in oracle.items():
 actual=plane(target,l);x=p.SHAPE_POLY_SET(expected);x.BooleanSubtract(actual);y=p.SHAPE_POLY_SET(actual);y.BooleanSubtract(expected);rows.append({'layer':target.GetLayerName(l),'actual_minus_oracle_mm2':y.Area()/1e12,'oracle_minus_actual_mm2':x.Area()/1e12});assert x.Area()+y.Area()<1,rows[-1]
r={'source_sha256':sha(S),'candidate_sha256':sha(T),'source_mutation':'Only the exact six declared vias are removed in memory; every source trace, pad, footprint, zone definition and other via remains intact; no source file written','removed_vias':sorted(retired),'reference_plane_comparison':rows,'status':'PASS EXACT SIX-VIA REFILL ORACLE','interpretation':'Native refill can close merged-hole concave fillets beyond individual isolated antipad contours. Exact output is independently reproducible from only the authorized six-via deletion, without granting a merged-hole reference exposure allowance.'};args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(r,indent=2));print(json.dumps(r),flush=True);sys.stdout.flush();os._exit(0)
