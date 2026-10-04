#!/usr/bin/python3
"""Portable native P5→P6 UUID replay. Requires KiCad pcbnew; no research dependencies."""
import os
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-p6-replay-kicad')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/controller-p6-replay-cache')
os.environ.setdefault('XDG_DATA_HOME','/tmp/controller-p6-replay-data')
import pcbnew as p,pathlib,json,hashlib,argparse,shutil,sys,collections
D=pathlib.Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--out',type=pathlib.Path,default=D/'reproduced');ap.add_argument('--source',type=pathlib.Path,default=D/'input-p5/controller.kicad_pcb');cfg=ap.parse_args();R=json.loads((D/'source-delta.json').read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();assert sha(cfg.source)==R['source_sha256'];cfg.out.mkdir(parents=True,exist_ok=True)
for x in ['controller.kicad_pro','controller.kicad_dru']:
 shutil.copy2(cfg.source.parent/x,cfg.out/x);shutil.copy2(cfg.source.parent/x,cfg.out/('replay-raw'+pathlib.Path(x).suffix))
b=p.LoadBoard(str(cfg.source));byid={t.m_Uuid.AsString():t for t in b.GetTracks()}
for row in R['removed']:assert row['id'] in byid;b.Remove(byid[row['id']])
rename={}
for row in R['added']:
 t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*[int(round(x*1e6)) for x in row['start']]));t.SetEnd(p.VECTOR2I(*[int(round(x*1e6)) for x in row['end']]));t.SetWidth(int(round(row['width_mm']*1e6)));t.SetLayer(b.GetLayerID(row['layer']));t.SetNetCode(b.GetNetsByName()[row['net']].GetNetCode());rename[t.m_Uuid.AsString()]=row['id'];b.Add(t)
raw=cfg.out/'replay-raw.kicad_pcb';p.SaveBoard(str(raw),b);serialized=raw.read_text()
for aa,zz in rename.items():serialized=serialized.replace(chr(34)+aa+chr(34),chr(34)+zz+chr(34))
raw.write_text(serialized)
for change in R.get('board_metadata_replacements',[]):
 text=raw.read_text();assert text.count(change['old'])==change['count'];raw.write_text(text.replace(change['old'],change['new']))
b=p.LoadBoard(str(raw));b.BuildConnectivity();assert b.GetConnectivity().GetUnconnectedCount(False)==0;p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();assert b.GetConnectivity().GetUnconnectedCount(False)==0;out=cfg.out/'controller.kicad_pcb';p.SaveBoard(str(out),b)
expected_path=D/'controller.kicad_pcb';assert sha(expected_path)==R['candidate_sha256'];expected=p.LoadBoard(str(expected_path));zone_expected={z.m_Uuid.AsString():z for z in expected.Zones()};zone_deltas=[]
for z in b.Zones():
 ez=zone_expected[z.m_Uuid.AsString()]
 for layer in list(b.GetEnabledLayers().CuStack()):
  if not z.HasFilledPolysForLayer(layer) and not ez.HasFilledPolysForLayer(layer):continue
  x=p.SHAPE_POLY_SET(z.GetFilledPolysList(layer));y=p.SHAPE_POLY_SET(ez.GetFilledPolysList(layer));xx=p.SHAPE_POLY_SET(x);xx.BooleanSubtract(y);yy=p.SHAPE_POLY_SET(y);yy.BooleanSubtract(x);zone_deltas.append({'zone':z.m_Uuid.AsString(),'layer':b.GetLayerName(layer),'symmetric_difference_mm2':(xx.Area()+yy.Area())/1e12})
def blocks(text):
 out=[];depth=0;start=0;quoted=False;esc=False;comment=False
 for i,c in enumerate(text):
  if comment:
   if c=='\n':comment=False
   continue
  if quoted:
   if esc:esc=False
   elif c=='\\':esc=True
   elif c=='"':quoted=False
   continue
  if c=='"':quoted=True;continue
  if c==';':comment=True;continue
  if c=='(':
   depth+=1
   if depth==2:start=i
  elif c==')':
   if depth==2:out.append(text[start:i+1])
   depth-=1
 return out
key=lambda x:x[1:].split(None,1)[0].rstrip(')');nonzones=lambda path:collections.Counter(q for q in blocks(path.read_text()) if key(q)!='zone');nonzone_equal=nonzones(expected_path)==nonzones(out)
result={'source_sha256':sha(cfg.source),'expected_candidate_sha256':R['candidate_sha256'],'reproduced_candidate_sha256':sha(out),'byte_identical':sha(out)==R['candidate_sha256'],'all_non_zone_records_byte_identical':nonzone_equal,'filled_copper_deltas':zone_deltas,'native_opens':b.GetConnectivity().GetUnconnectedCount(False),'note':'Filled polygon serialization may retain or omit redundant collinear vertices. Native filled-copper unions must match exactly.'};result['geometry_identical']=nonzone_equal and all(q['symmetric_difference_mm2']==0 for q in zone_deltas);(cfg.out/'replay-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True);assert result['geometry_identical'];sys.stdout.flush();os._exit(0)
