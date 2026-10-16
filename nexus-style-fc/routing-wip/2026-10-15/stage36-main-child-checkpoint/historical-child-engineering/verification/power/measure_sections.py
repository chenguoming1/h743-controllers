import json,math
from pathlib import Path
P=Path('/workspace/shared/nexus-compact-power-review');G=json.load(open(P/'v2-geometry.json'))
def union(a):
 o=[]
 for lo,hi in sorted(a):
  if hi<=lo:continue
  if o and lo<=o[-1][1]+1e-10:o[-1][1]=max(o[-1][1],hi)
  else:o.append([lo,hi])
 return o
def minus(a,b):
 for lo,hi in b:
  out=[]
  for l,h in a:
   if hi<=l or lo>=h:out.append([l,h]);continue
   if lo>l:out.append([l,lo])
   if hi<h:out.append([hi,h])
  a=out
 return a
def ring(points,x):
 cross=[]
 for (x1,y1),(x2,y2) in zip(points,points[1:]+points[:1]):
  if (x1<=x<x2) or (x2<=x<x1):cross.append(y1+(y2-y1)*(x-x1)/(x2-x1))
 cross.sort();return [[cross[i],cross[i+1]] for i in range(0,len(cross)-1,2)]
def section(x):
 a=[]
 for z in G['zones']:
  if z['net']!='VX':continue
  for poly in z['filled'].get('F.Cu',[]):
   b=ring(poly['outer'],x)
   for hole in poly['holes']:b=minus(b,ring(hole,x))
   a+=b
 return union(a)
r=[]
for i,(a,b) in enumerate(zip([103.58,106.12,108.66,111.2],[106.12,108.66,111.2,113.74])):
 vals=[]
 for j in range(521):
  x=a+.75+(b-a-1.5)*j/520;s=section(x);w=sum(h-l for l,h in s);vals.append((w,x,s))
 w,x,s=min(vals)
 I=sum([4.5,1,1,2.4][:i+1]);r.append({'gap_index':i+1,'x_mm':x,'filled_width_mm':w,'intervals_y_mm':s,'current_A':I,'copper_thickness_mm':.060,'section_average_A_per_mm2':I/(.06*w),'note':'Minimum over sampled inter-land gap only; no header-hole annular or edge current crowding resolved. Not a peak or thermal rating.'})
print(json.dumps(r,indent=2));(P/'v2-copper-sections.json').write_text(json.dumps(r,indent=2))
