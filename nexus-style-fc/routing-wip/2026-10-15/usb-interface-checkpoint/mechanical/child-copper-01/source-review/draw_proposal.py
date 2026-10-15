"""Plot read-only transaction at native scale; polygon samples are display only."""
from pathlib import Path
import runpy, math, html
HERE=Path(__file__).resolve().parent
v=runpy.run_path(str(HERE/'verify_geometry.py'))
s=v['s'];one=v['one'];xy=v['xy'];uid=v['uid'];P=v['P']
colors={'VX':'#d63535','GND':'#207a43','S1':'#8f42bd','SBUS':'#007caa'}
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1220" height="850" viewBox="99 98.5 24.4 17"><rect x="99" y="98.5" width="24.4" height="17" fill="white"/>']
def text(x,y,t,size=.32,color='#222'):
    parts.append(f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="{size}" fill="{color}">{html.escape(t)}</text>')
def line(a,b,w,color,extra=''):
    parts.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{color}" stroke-width="{w}" stroke-linecap="round" {extra}/>')
text(99.4,99.15,'Child copper proposal | B.Cu, top-coordinate view | UNFINISHED',.44)
for o in v['obs']:
    if 'B.Cu' not in o['layers']:continue
    if o['kind']=='rect':
        x,y,xx,yy=o['rect'];parts.append(f'<rect x="{x}" y="{y}" width="{xx-x}" height="{yy-y}" fill="#e8cfa4" stroke="#ba9867" stroke-width=".025"/>')
    elif o['kind']=='circle':
        x,y=o['c'];parts.append(f'<circle cx="{x}" cy="{y}" r="{o["r"]}" fill="#e8cfa4" stroke="#ba9867" stroke-width=".025"/>')
        if 'drill' in o:parts.append(f'<circle cx="{x}" cy="{y}" r="{o["drill"]}" fill="white"/>')
for n in s.find(v['B'],'segment'):
    if v['txt'](n,'layer')!='B.Cu':continue
    if uid(n) not in v['donors']:line(xy(n,'start'),xy(n,'end'),float(one(n,'width')[1]),'#b5b8c7')
for n in s.find(v['B'],'segment'):
    if v['txt'](n,'layer')!='B.Cu':continue
    if uid(n) in v['donors']:line(xy(n,'start'),xy(n,'end'),float(one(n,'width')[1]),'#e8a052','stroke-dasharray=".16 .15" opacity=".8"')
for r in P['routes']:
    for q in r['replacement_segments']:line(q['start'],q['end'],q['width'],colors[r['net']])
    t=r['terminal_port'];text(t['center'][0]-.3,110.55,r['net'],.28,colors[r['net']])
for e in v['edges']:
    if e[0]=='gr_line':line(xy(e,'start'),xy(e,'end'),.035,'#111')
    else:
        c,r,a,sw=v['arc_angles'](e);points=[(c[0]+r*math.cos(a+sw*i/80),c[1]+r*math.sin(a+sw*i/80)) for i in range(81)]
        parts.append('<polyline fill="none" stroke="#111" stroke-width=".035" points="'+' '.join(f'{x},{y}' for x,y in points)+'"/>')
text(99.5,112,'Six donor tracks -> nine same-width segments. Orange dashes = removed copper. Gray = retained.')
text(99.5,112.55,'Minimum new-route copper-to-edge 0.565219 mm; foreign copper 0.258600 mm; foreign drill 0.726000 mm.')
text(99.5,113.1,'All 22 affected-net pads connected without fills. Stored GND fills are omitted and MUST be refilled.')
text(99.5,113.65,'Native DRC/ERC/parity and exact integrated-source fit checks remain required. No manufacturing or strength approval.')
line((99.5,114.5),(104.5,114.5),.055,'#111');line((99.5,114.35),(99.5,114.65),.035,'#111');line((104.5,114.35),(104.5,114.65),.035,'#111');text(101.6,115,'5 mm',.3)
parts.append('</svg>');(HERE/'child-routing-preview.svg').write_text('\n'.join(parts)+'\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle,Polygon
fig,ax=plt.subplots(figsize=(12.2,8.5),dpi=120);fig.subplots_adjust(left=.02,right=.98,top=.94,bottom=.04)
ax.set(xlim=(99,123.4),ylim=(115.5,99.5),aspect='equal');ax.axis('off')
fig.suptitle('Child copper proposal | B.Cu, top-coordinate view | UNFINISHED',fontsize=13)
def capsule(a,b,w,color):
    dx,dy=b[0]-a[0],b[1]-a[1];ll=math.hypot(dx,dy);nx,ny=-dy/ll*w/2,dx/ll*w/2
    ax.add_patch(Polygon([(a[0]+nx,a[1]+ny),(b[0]+nx,b[1]+ny),(b[0]-nx,b[1]-ny),(a[0]-nx,a[1]-ny)],color=color,lw=0))
    for p in (a,b):ax.add_patch(Circle(p,w/2,color=color,lw=0))
for o in v['obs']:
    if 'B.Cu' not in o['layers']:continue
    if o['kind']=='rect':
        x,y,xx,yy=o['rect'];ax.add_patch(Rectangle((x,y),xx-x,yy-y,facecolor='#e8cfa4',edgecolor='#ba9867',lw=.4))
    elif o['kind']=='circle':
        ax.add_patch(Circle(o['c'],o['r'],facecolor='#e8cfa4',edgecolor='#ba9867',lw=.4))
        if 'drill' in o:ax.add_patch(Circle(o['c'],o['drill'],color='white',lw=0))
for n in s.find(v['B'],'segment'):
    if v['txt'](n,'layer')!='B.Cu':continue
    if uid(n) not in v['donors']:capsule(xy(n,'start'),xy(n,'end'),float(one(n,'width')[1]),'#b5b8c7')
    else:
        a,b=xy(n,'start'),xy(n,'end');ax.plot([a[0],b[0]],[a[1],b[1]],color='#d99840',lw=1.5,ls='--')
for r in P['routes']:
    for q in r['replacement_segments']:capsule(q['start'],q['end'],q['width'],colors[r['net']])
    t=r['terminal_port'];ax.text(t['center'][0],110.55,r['net'],ha='center',fontsize=9,color=colors[r['net']])
for e in v['edges']:
    if e[0]=='gr_line':points=[xy(e,'start'),xy(e,'end')]
    else:
        c,r,a,sw=v['arc_angles'](e);points=[(c[0]+r*math.cos(a+sw*i/80),c[1]+r*math.sin(a+sw*i/80)) for i in range(81)]
    ax.plot([p[0] for p in points],[p[1] for p in points],color='#111',lw=.7)
for y,t in [(112,'Six donor tracks become nine same-width segments. Orange dashes: old centreline. Gray: retained copper.'),(112.6,'New-route minima: edge 0.565219 mm | foreign copper 0.258600 mm | foreign drill 0.726000 mm.'),(113.2,'All 22 affected-net pads connect without fills. Stored GND fills are omitted and MUST be refilled.'),(113.8,'Native DRC/ERC/parity and integrated-source fit checks remain required. No manufacturing or strength approval.')]:ax.text(99.5,y,t,fontsize=9)
ax.plot([99.5,104.5],[114.6,114.6],color='black',lw=1);ax.text(102,115,'5 mm',ha='center',fontsize=9)
fig.savefig(HERE/'child-routing-preview.png');plt.close(fig)
