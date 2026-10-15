"""Draw measured source geometry only. No board edits or native jobs."""
import os,json
os.environ['MPLCONFIGDIR']='/tmp/nexus-usb-mpl'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
from pathlib import Path
D=Path('/workspace/shared/nexus-usb-stack-review');p=json.loads((D/'geometry-evidence.json').read_text())
fig,axs=plt.subplots(1,3,figsize=(13,8),gridspec_kw={'width_ratios':[1.25,1,1]})
colors={'USB_DP':'#c43d4b','USB_DM':'#137cab'};styles={'F.Cu':':','B.Cu':'-','In3.Cu':'--'}
for ax in axs:
 for t in p['usb_tracks']:
  ax.plot([t['start'][0],t['end'][0]],[t['start'][1],t['end'][1]],color=colors[t['net']],linestyle=styles[t['layer']],linewidth=1.5)
 for v in p['usb_vias']:ax.add_patch(Circle(v['at'],v['diameter']/2,fill=False,edgecolor=colors[v['net']],linewidth=1.1))
 for q in p['parts']:
  if q['net'] not in colors and q['ref']!='U7':continue
  sx,sy=q['size'];sx,sy=(sy,sx) if abs(q['rotation'])%180==90 else (sx,sy)
  ax.add_patch(Rectangle((q['at'][0]-sx/2,q['at'][1]-sy/2),sx,sy,facecolor=colors.get(q['net'],'#777'),alpha=.5))
  if ax!=axs[0]:ax.text(q['at'][0],q['at'][1]-.12,f"{q['ref']}.{q['pin']}",fontsize=6,ha='center',va='bottom')
 ax.set_aspect('equal');ax.grid(alpha=.15);ax.set_xlabel('x, mm');ax.invert_yaxis()
axs[0].set_xlim(106.9,117);axs[0].set_ylim(133,104.8);axs[0].set_title('Complete measured USB routing')
axs[1].set_xlim(107,111.8);axs[1].set_ylim(132.4,123);axs[1].set_title('Connector and U7 detail')
axs[2].set_xlim(107.4,111.2);axs[2].set_ylim(132.1,123.4);axs[2].set_title('Saved In4 GND projection voids\nblack = uncovered center projection')
for r in p['stored_fill_reference_coverage']:
 if r['reference']!='In4.Cu':continue
 for i in r['uncovered_intervals']:
  axs[2].plot([i['start'][0],i['end'][0]],[i['start'][1],i['end'][1]],color='#111',linewidth=4,alpha=.75)
fig.suptitle('Source-bound USB geometry • DP red / DM blue • B.Cu solid / In3 dashed / F.Cu dotted',fontsize=12)
fig.text(.5,.025,'PCB SHA256 10c4da72…059c5 | No proposed route, impedance simulation or new refill | mm coordinates viewed from front',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.045,1,.95));fig.savefig(D/'usb-geometry.png',dpi=180);fig.savefig(D/'usb-geometry.svg')
