"""Supplement static evidence with exact source binding, via return proximity and analytic estimates. No PCB changes."""
import contextlib,io,json,math,runpy,hashlib,itertools,collections
from pathlib import Path
import numpy as np
D=Path('/workspace/shared/nexus-usb-stack-review')
with contextlib.redirect_stdout(io.StringIO()):m=runpy.run_path(str(D/'analyze_usb_static.py'))
p=json.loads((D/'geometry-evidence.json').read_text())
transitions=[]
for v in m['usbvias']:
 nearest=sorted([dict(uuid=u['uuid'],at=u['at'],center_distance_mm=math.dist(v['at'],u['at']),diameter_mm=u['diameter']) for u in m['vias'] if u['net']=='GND'],key=lambda q:q['center_distance_mm'])[:3]
 transitions.append(dict(net=v['net'],uuid=v['uuid'],at=v['at'],nearest_gnd_vias=nearest))
coverage=[]
for t in m['usbtracks']:
 L=t['length_mm'];n=max(1,math.ceil(L/.01));a=np.array(t['start']);b=np.array(t['end']);pts=a+(np.arange(n)[:,None]+.5)/n*(b-a)
 near=np.zeros(n,dtype=bool)
 for v in m['usbvias']:near|=np.linalg.norm(pts-np.array(v['at']),axis=1)<.525
 refs=['In1.Cu'] if t['layer']=='F.Cu' else ['In4.Cu'] if t['layer']=='B.Cu' else ['In1.Cu','In2.Cu','In4.Cu']
 for ref in refs:
  bad=~m['inside'](pts,ref);nfar=int((bad&~near).sum())
  coverage.append(dict(net=t['net'],uuid=t['uuid'],reference=ref,layer=t['layer'],outside_usb_via_0525mm_neighborhood_uncovered_samples=nfar,outside_usb_via_0525mm_neighborhood_uncovered_length_mm=nfar*L/n))
# Direct source-derived, empirical microstrip estimate documented by TI.
def zd(w,s,h=.1164,t=.035,er=4.16):
 z=87/math.sqrt(er+1.41)*math.log(5.98*h/(.8*w+t));return z,2*z*(1-.48*math.exp(-.96*s/h))
nominal=[dict(width_mm=w,gap_mm=s,z0_ohm=zd(w,s)[0],zdiff_ohm=zd(w,s)[1]) for w,s in [(.127,.127),(.15,.127),(.155,.127),(.16,.127),(.15,.15),(.17,.15),(.15,.35),(.2,.25)]]
# Scenario sweep, NOT a fabrication tolerance declaration.
sweep=[]
for h,t,er,w,s in itertools.product([.10476,.12804],[.030,.040],[3.96,4.36],[.145,.165],[.117,.137]):
 sweep.append(dict(h_mm=h,t_mm=t,er=er,width_mm=w,gap_mm=s,zdiff_ohm=zd(w,s,h,t,er)[1]))
base=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/c19-integration/experimental-r43')
drc=json.loads((base/'native-drc.json').read_text());rec=json.loads((base/'native-execution-receipt.json').read_text())
supp=dict(board_sha256=p['board_sha256'],native_receipt_sha256=hashlib.sha256((base/'native-execution-receipt.json').read_bytes()).hexdigest(),native_receipt_saved_board_sha256=rec['saved_board_sha256'],native_drc_sha256=hashlib.sha256((base/'native-drc.json').read_bytes()).hexdigest(),native_drc_USB_violations=[v for v in drc['violations'] if 'USB_' in json.dumps(v)],return_via_proximity=transitions,coverage_outside_usb_vias=coverage,analytic_impedance=dict(formula='Z0=87/sqrt(er+1.41)*ln(5.98*h/(0.8*w+t)); Zdiff=2*Z0*(1-0.48*exp(-0.96*s/h))',source='https://www.ti.com/content/dam/videos/external-videos/en-us/4/3816841626001/6087491555001.mp4/subassets/usb_layout_basics.pdf',h_mm=.1164,t_mm=.035,er=4.16,nominal=nominal,sensitivity=dict(description='Illustrative sensitivity only, not supplier tolerances: h +/-10%, t 30–40 um, er 3.96–4.36, width .155+/-.010 mm, gap .127+/-.010 mm. Gap-low scenario is below design manufacturing minimum and is not a routing instruction.',min_zdiff_ohm=min(r['zdiff_ohm'] for r in sweep),max_zdiff_ohm=max(r['zdiff_ohm'] for r in sweep)),limits='Empirical uncoated edge-coupled microstrip; ignores soldermask, side pours, trapezoidal etch, surface roughness, frequency-dependent dielectric, pads/vias and connector/package discontinuities. Not applicable to current In3 geometry.'))
(D/'supplement-evidence.json').write_text(json.dumps(supp,indent=2)+'\n')
print(json.dumps({'return_vias':transitions,'uncovered_far_from_USB_vias':[r for r in coverage if r['outside_usb_via_0525mm_neighborhood_uncovered_samples']],'impedance':supp['analytic_impedance']},indent=2))
