import sys
sys.path.insert(0,'/workspace/shared/nexus-main-placement-fix/scripts')
from router import *
sys.path.insert(0,'/workspace/shared/nexus-main-placement-fix/successor-work/adc-local')
import apply_adc_dsm_delta as delta
b=k.LoadBoard('/workspace/shared/nexus-main-placement-fix/stage35/hardware/nexus-style-fc.kicad_pcb');fs={f.GetReference():f for f in b.GetFootprints()};rem=[]
fs['C29'].SetPosition(vec((111,119.2)));fs['C29'].SetOrientationDegrees(270);fs['R16'].SetPosition(vec((111.4,121.15)))
ids={'8a82374b-9efb-544d-8005-299d31dff60e','ff7cfb1b-c125-4db0-9000-8d64e4e8fec9','5e536048-2391-429d-8264-80126486a4d8','a02119b1-09d1-4d92-9b29-4a59e74f56a8'}
for t in list(b.GetTracks()):
 if t.GetNetname()=='VX_SENSE' or t.m_Uuid.AsString() in ids:rem.append(t);b.Remove(t)
for net,p in [('VX_SENSE',(112.45,118.66))]:
 ok=[Router(b,l,net,.45).free(p,p) for l in [k.F_Cu,k.B_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu]];print('VIA',net,p,ok,flush=True)
 assert all(ok)
 v=k.PCB_VIA(b);v.SetPosition(vec(p));v.SetWidth(450000);v.SetDrill(200000);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(b.FindNet(net));b.Add(v)
paths=[('5V',k.F_Cu,.35,[(111.825,117.825),(112.225,118.125),(112.575,118.125),(112.8,118.25),(113,118.5),(113.325,119.225)]),('VX_SENSE',k.F_Cu,.127,[(111,118.72),(112.45,118.66)]),('VX_SENSE',k.B_Cu,.127,[(112.45,118.66),(113.05,118.45),(113.175,118.3),(113.35,117.55)]),('VX_SENSE',k.F_Cu,.2,[(111,118.72),(110.5,119.35),(110.45,119.525),(110.45,119.9),(110.55,120.075),(111.4,120.64)]),('VX',k.F_Cu,.2,[(111.4,121.66),(109.558,119.85)])]
for net,l,w,p in paths:
 rt=Router(b,l,net,w);ok=all(rt.free(a,z) for a,z in zip(p,p[1:]));print('PATH',net,ok,flush=True);assert ok;rt.add(p)
rem+=delta.apply(b)
p=(111.775,119.6)
assert all(Router(b,l,'GND',.45).free(p,p) for l in [k.F_Cu,k.B_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu])
v=k.PCB_VIA(b);v.SetPosition(vec(p));v.SetWidth(450000);v.SetDrill(200000);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(b.FindNet('GND'));b.Add(v)
rt=Router(b,k.F_Cu,'GND',.2);assert rt.free((111,119.68),p);rt.add([(111,119.68),p])
from pathlib import Path
import shutil
O=Path('/workspace/shared/nexus-main-placement-fix/stage36');assert not O.exists();O.mkdir()
for folder in ['hardware','tools']:shutil.copytree('/workspace/shared/nexus-main-placement-fix/stage35/'+folder,O/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
k.SaveBoard(str(O/'hardware/nexus-style-fc.kicad_pcb'),b)
print('ADC_ONLY_SAVED',flush=True)
