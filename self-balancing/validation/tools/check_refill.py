#!/usr/bin/python3
"""Read-only native refill equality and drill-subtracted reference proof."""
import argparse,hashlib,json,os,pathlib
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=pathlib.Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args()
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
assert sha(a.candidate)==a.sha256
b=p.LoadBoard(str(a.candidate));b.BuildConnectivity();c=b.GetConnectivity();opens_before=c.GetUnconnectedCount(False);layers=list(b.GetEnabledLayers().CuStack());old={}
for z in b.Zones():
 if z.GetIsRuleArea():continue
 for l in layers:
  if z.IsOnLayer(l):old[(z.m_Uuid.AsString(),l)]=p.SHAPE_POLY_SET(z.GetFilledPolysList(l))
f=p.ZONE_FILLER(b);ok=f.Fill(b.Zones());b.BuildConnectivity();opens_after=b.GetConnectivity().GetUnconnectedCount(False);deltas=[]
for z in b.Zones():
 if z.GetIsRuleArea():continue
 for l in layers:
  key=(z.m_Uuid.AsString(),l)
  if key not in old:continue
  loss=p.SHAPE_POLY_SET(old[key]);loss.BooleanSubtract(z.GetFilledPolysList(l));gain=p.SHAPE_POLY_SET(z.GetFilledPolysList(l));gain.BooleanSubtract(old[key])
  deltas.append({'uuid':key[0],'net':z.GetNetname(),'layer':b.GetLayerName(l),'loss_mm2':loss.Area()/1e12,'gain_mm2':gain.Area()/1e12})
errors=[]
if not ok:errors.append('Native zone filler reported failure')
if opens_before or opens_after:errors.append('Nonzero native connectivity opens')
if any(x['loss_mm2'] or x['gain_mm2'] for x in deltas):errors.append('Persisted filled copper differs from independent fresh in-memory refill')
assert sha(a.candidate)==a.sha256,'Source changed during check'
report={'status':'PASS CURRENT NATIVE FILL' if not errors else 'NOT PASSED','source_sha256':a.sha256,'source_unchanged':True,'opens_before':opens_before,'opens_after':opens_after,'filled_zone_changes':deltas,'errors':errors,'method':__doc__}
a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='filled_zone_changes'},indent=2));raise SystemExit(bool(errors))
