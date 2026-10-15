from static_clearance import *
# Bounded alternate-layer straight/45-degree reservation probes; these are not router searches.
E=.15*2+.127
paths=[('inner2_west','In2.Cu',[[109.6,124.0],[109.6,110.0]]),('inner3_west','In3.Cu',[[109.6,124.0],[109.6,110.0]]),('inner2_center','In2.Cu',[[110.6,124.0],[110.6,110.0]]),('inner3_center','In3.Cu',[[110.6,124.0],[110.6,110.0]]),('inner2_east','In2.Cu',[[111.5,124.0],[111.5,110.0]]),('back_west','B.Cu',[[107.5,124.0],[107.5,110.0]])]
for name,l,pts in paths:
 rs=[r for a,b in zip(pts,pts[1:]) for r in checkseg('PAIR',l,a,b,E)]
 print(name,[(r['item']['net'],r['item'].get('ref',''),r['item'].get('pin',''),r['item']['uuid'][:8],round(r['gap_mm'],4),r['item'].get('at',r['item'].get('start'))) for r in rs])
for t in tracks:
 if t['layer']=='In2.Cu' and t['net'] in ['5V','3V3'] and min(t['start'][0],t['end'][0])<113 and max(t['start'][0],t['end'][0])>107 and min(t['start'][1],t['end'][1])<123 and max(t['start'][1],t['end'][1])>115:print('POWER',t)
