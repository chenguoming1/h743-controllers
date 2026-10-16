"""Additional barrel-only 0.97 mm header-bore screen using unchanged 1mm sheet geometry."""
from pathlib import Path
import json
O=Path('/workspace/shared/nexus-compact-power-review');D=O/'barrel-length-addendum'
# Reuse validated setup and function definitions, never the bulk original solver.
setup=(O/'solve_barrel_length_addendum.py').read_text().split('rows=[];pairs=[]')[0]
exec(compile(setup,'<addendum-setup>','exec'),globals())
assert 'barrel_length_mm=1.6):' in src
src=src.replace('barrel_length_mm=1.6):','barrel_length_mm=1.6,header_bore_mm=1.0):')
assert src.count('((.5+wall/1000)**2-.5**2)')==1
src=src.replace('((.5+wall/1000)**2-.5**2)','((header_bore_mm/2+wall/1000)**2-(header_bore_mm/2)**2)')
src=src.replace('return dict(barrel_length_mm=barrel_length_mm,','return dict(header_bore_mm=header_bore_mm,barrel_length_mm=barrel_length_mm,')
ns={};exec(compile(src,'<sealed-solver-definitions-with-length-and-bore>','exec'),ns)
length=json.loads((D/'barrel-length-sensitivity.json').read_text())
rows=[];cases=[]
for a in length['full_network_rows']:
 if a['barrel_length_mm']!=1.65:continue
 r=ns['run'](a['h_mm'],a['copper_um'],a['T_C'],a['IACS'],a['barrel_wall_um'],a['profile'],'uneven_8p9_plus_main',mainport=a['main_port'],barrel_length_mm=1.65,header_bore_mm=.97)
 r['minimum_servo_V']=min(v for k,v in r['load_pair_V'].items() if k.startswith('servo'))
 r['surviving_feed']=a['surviving_feed']
 r['board_only_worst_servo_drop_V']=r['feed_pair_V'][a['surviving_feed']]-r['minimum_servo_V']
 rows.append(r)
 orig=next(x for x in length['full_network_rows'] if x['barrel_length_mm']==1.6 and all(x[k]==a[k] for k in ['h_mm','copper_um','T_C','IACS','barrel_wall_um','profile','main_port']))
 fields=['minimum_servo_V','board_only_worst_servo_drop_V','sheet_loss_W','barrel_loss_W','copper_and_barrel_W','barrel_ohm']
 cases.append({k:r[k] for k in ['h_mm','copper_um','T_C','IACS','barrel_wall_um','profile','main_port','surviving_feed']}|{'combined_1p65mm_0p97mm':{k:r[k] for k in fields},'delta_from_original_1p60mm_1p00mm':{k:r[k]-orig[k] for k in fields},'delta_from_length_only_1p65mm_1p00mm':{k:r[k]-a[k] for k in fields}})
for p,v in tracked.items():assert sha(p)==v,(p,'changed')
out={'source_sha256':seal['source_sha256_before_and_after'],'scope':'Optional barrel-resistance sensitivity only. Header finished bore 0.97 mm at 1.65 mm length; via bore remains nominal 0.30 mm. No sheet geometry change, no land or mating-pin fit simulation, no accepted supplier tolerance.','cases':cases,'full_network_rows':rows,'max_linear_residual_A':max(r['linear_residual_A'] for r in rows),'max_abs_power_balance_error_W':max(abs(r['power_balance_error_W']) for r in rows)}
(D/'header-bore-sensitivity.json').write_text(json.dumps(out,indent=2)+'\n')
for r in cases:
 if (r['h_mm'],r['copper_um'],r['T_C'],r['barrel_wall_um'],r['main_port'])==(.075,60,80,18,'small'):print(json.dumps(r,indent=2))
print('maxresidual',out['max_linear_residual_A'],'powerbalance',out['max_abs_power_balance_error_W'])
