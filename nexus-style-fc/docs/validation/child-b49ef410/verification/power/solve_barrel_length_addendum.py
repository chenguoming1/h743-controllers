"""Light terminal-only sensitivity; never regenerates copper sheets or edits sources."""
import json,hashlib,itertools
from pathlib import Path
O=Path('/workspace/shared/nexus-compact-power-review')
D=O/'barrel-length-addendum';D.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
seal=json.loads((O/'V2-POWER-REVIEW-SEAL.json').read_text())
tracked={str(O/n):v for n,v in seal['artifacts'].items()}
tracked[str(O/'V2-POWER-REVIEW-SEAL.json')]=sha(O/'V2-POWER-REVIEW-SEAL.json')
tracked[seal['source_path']]=seal['source_sha256_before_and_after']
for p,v in tracked.items():assert sha(p)==v,(p,sha(p),v)
# Isolate only definitions from sealed solver, parameterize both barrel lengths.
src=(O/'solve_bench_cases.py').read_text().split('\nrows=[]')[0]
src=src.replace("NAME=sys.argv[1] if len(sys.argv)>1 else 'prototype'","NAME='v2'")
src=src.replace("face='B.Cu',mainport='small',bridge=None):","face='B.Cu',mainport='small',bridge=None,barrel_length_mm=1.6):")
assert src.count('rho*1.6/')==2
src=src.replace('rho*1.6/','rho*barrel_length_mm/')
src=src.replace('return dict(h_mm=h,','return dict(barrel_length_mm=barrel_length_mm,h_mm=h,')
ns={};exec(compile(src,'<sealed-solver-definitions-with-barrel-length-parameter>','exec'),ns)
old=json.loads((O/'v2-bench-cases.json').read_text())['rows']
def key(r):return tuple(r[k] for k in ['h_mm','copper_um','T_C','IACS','barrel_wall_um','profile','allocation','injection_face','main_port','main_bridge_ohm'])
old_by_key={key(r):r for r in old}
rows=[];pairs=[];max_base_error=0
for h,(t,T,iacs),wall,profile,main in itertools.product([.1,.075],ns['MATERIALS'],[18,20],['ESC_pair_open','SBUS_pair_open'],['small','broad']):
 pair=[]
 for L in [1.6,1.65]:
  r=ns['run'](h,t,T,iacs,wall,profile,'uneven_8p9_plus_main',mainport=main,barrel_length_mm=L)
  survivor='SBUS' if profile=='ESC_pair_open' else 'ESC'
  r['minimum_servo_V']=min(v for k,v in r['load_pair_V'].items() if k.startswith('servo'))
  r['board_only_worst_servo_drop_V']=r['feed_pair_V'][survivor]-r['minimum_servo_V']
  r['surviving_feed']=survivor
  if L==1.6:
   oldr=old_by_key[key(r)]
   max_base_error=max(max_base_error,max(abs(v-oldr['ports_V'][k]) for k,v in r['ports_V'].items()),abs(r['copper_and_barrel_W']-oldr['copper_and_barrel_W']))
  rows.append(r);pair.append(r)
 a,b=pair
 pairs.append({k:a[k] for k in ['h_mm','copper_um','T_C','IACS','barrel_wall_um','profile','main_port','surviving_feed']}|{'baseline':{k:a[k] for k in ['minimum_servo_V','board_only_worst_servo_drop_V','sheet_loss_W','barrel_loss_W','copper_and_barrel_W','barrel_ohm','load_pair_V']},'length_1p65mm':{k:b[k] for k in ['minimum_servo_V','board_only_worst_servo_drop_V','sheet_loss_W','barrel_loss_W','copper_and_barrel_W','barrel_ohm','load_pair_V']},'delta_1p65_minus_1p60':{k:b[k]-a[k] for k in ['minimum_servo_V','board_only_worst_servo_drop_V','sheet_loss_W','barrel_loss_W','copper_and_barrel_W','barrel_ohm']}})
assert max_base_error<1e-10,max_base_error
for p,v in tracked.items():assert sha(p)==v,(p,'changed')
result={'source_sha256':seal['source_sha256_before_and_after'],'scope':'Terminal-only 1.60 versus 1.65 mm barrel-length sensitivity. No native or sheet solve. No source edits. Board copper benchmark only; contacts, harness, joints, thermal and flight qualification excluded.','input_sha256':tracked,'baseline_reproduction_max_error':max_base_error,'max_linear_residual_A':max(r['linear_residual_A'] for r in rows),'max_abs_power_balance_error_W':max(abs(r['power_balance_error_W']) for r in rows),'cases':pairs,'full_network_rows':rows}
(D/'barrel-length-sensitivity.json').write_text(json.dumps(result,indent=2)+'\n')
print('input files unchanged; baseline reproduction error',max_base_error)
print('network dimension',len(rows[0]['ports_V']),'cases',len(rows),'max residual',result['max_linear_residual_A'],'max power balance',result['max_abs_power_balance_error_W'])
for r in pairs:
 if (r['h_mm'],r['copper_um'],r['T_C'],r['barrel_wall_um'])==(.075,60,80,18):print(json.dumps(r,indent=2))
