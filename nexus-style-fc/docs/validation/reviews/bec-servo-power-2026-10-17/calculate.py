"""Read-only current-budget screen using the sealed, unchanged child copper network.

Run with a Python environment containing NumPy. No PCB or old evidence is written.
The prescribed conductor temperature is not a solved operating temperature.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
POWER = ROOT / 'docs/validation/child-b49ef410/verification/power'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
seal = json.loads((POWER / 'V2-POWER-REVIEW-SEAL.json').read_text())
child = ROOT / 'hardware/header-board/nexus-header-board.kicad_pcb'
main = ROOT / 'hardware/nexus-style-fc.kicad_pcb'
assert sha(child) == seal['source_sha256_before_and_after']
for name, expected in seal['artifacts'].items():
    assert sha(POWER / name) == expected, name

# Execute only the sealed solver's definitions, with the local evidence location.
src = (POWER / 'solve_bench_cases.py').read_text().split('\nrows=[]')[0]
src = src.replace("O=Path('/workspace/shared/nexus-compact-power-review')", f'O=Path({str(POWER)!r})')
src = src.replace("NAME=sys.argv[1] if len(sys.argv)>1 else 'prototype'", "NAME='v2'")
ns = {}
exec(compile(src, '<sealed-local-solver-definitions>', 'exec'), ns)
old = json.loads((POWER / 'v2-bench-cases.json').read_text())['rows']
baseline = ns['run'](.075, 60, 80, .95, 18, 'both_equal20m', 'uneven_8p9_plus_main')
ref = next(r for r in old if all(r[k] == baseline[k] for k in [
    'h_mm', 'copper_um', 'T_C', 'IACS', 'barrel_wall_um', 'profile',
    'allocation', 'injection_face', 'main_port', 'main_bridge_ohm']))
reproduction_error = max(abs(baseline['ports_V'][k] - v) for k, v in ref['ports_V'].items())
assert reproduction_error < 1e-10

# Permit explicit synthetic servo allocations and main current; retain the circuit.
src = src.replace("bridge=None):", "bridge=None,main_current_A=None,barrel_length_mm=1.6,header_bore_mm=1.0):")
src = src.replace('rho*1.6/', 'rho*barrel_length_mm/')
src = src.replace('((.5+wall/1000)**2-.5**2)',
                  '((header_bore_mm/2+wall/1000)**2-(header_bore_mm/2)**2)')
src = src.replace(' if mainI:\n', ' if main_current_A is not None:mainI=main_current_A\n if mainI:\n')
ns = {}
exec(compile(src, '<parameterized-sealed-solver>', 'exec'), ns)
allocations = {'total_3A': [.475] * 4, 'total_4p6A': [1, 1, 1, .5],
               'total_6A': [1.225] * 4, 'total_10A': [4.5, 1, 1, 2.4],
               'KST_rounded_upper_graph_plus_main_19p6A': [5, 5, 5, 3.5]}
ns['ALLOCATIONS'].update(allocations)
rows = []
for allocation in allocations:
    for profile in ['both_equal20m', 'both_paired_weak_SBUS', 'SBUS_pair_open', 'ESC_pair_open']:
        r = ns['run'](.075, 60, 80, .95, 18, profile, allocation,
                      main_current_A=1.1, barrel_length_mm=1.65, header_bore_mm=.97)
        r['minimum_servo_pad_V'] = min(v for k, v in r['load_pair_V'].items() if k.startswith('servo'))
        r['max_feed_conductor_A'] = max(r['feed_currents_A'].values())
        r['feed_contact_3A_screen'] = bool(r['max_feed_conductor_A'] <= 3 + 1e-8)
        r['servo_contact_3A_screen'] = max(r['load_A']) <= 3
        if profile in ['SBUS_pair_open', 'ESC_pair_open']:
            feed = 'ESC' if profile == 'SBUS_pair_open' else 'SBUS'
            r['board_only_worst_servo_drop_V'] = r['feed_pair_V'][feed] - r['minimum_servo_pad_V']
        rows.append(r)
assert max(r['linear_residual_A'] for r in rows) < 1e-7
assert max(abs(r['power_balance_error_W']) for r in rows) < 1e-5

result = {
    'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in [child, main]},
    'method': 'Fresh terminal solves of sealed exact-child saved-copper matrices; no new mesh extraction. Main PCB not modeled.',
    'conditions': {'source_V': 7.4, 'main_abstract_A': 1.1, 'copper_um': 60,
                   'conductor_C_prescribed': 80, 'IACS': .95, 'barrel_wall_um': 18,
                   'barrel_length_mm': 1.65, 'header_bore_mm_resistance_only': .97,
                   'grid_mm': .075, 'feed_and_servo_face': 'B.Cu', 'main_port': 'small'},
    'excluded': ['main PCB copper/regulator/solder-joint loss', 'output servo harnesses and contacts',
                 'actual BEC load regulation/transients', 'thermal equilibrium',
                 'pin/solder parallel barrel shunts', 'local land crowding'],
    'assumptions': ['60 um copper and 18 um wall are unaccepted fabrication bounds',
                    '1.1 A main load is an illustrative allowance, not measured',
                    'lead/contact resistances are synthetic and not actual harness data',
                    '3 A contact screen is not qualification of the unknown female contacts'],
    'baseline_reproduction_max_V_error': reproduction_error,
    'rows': rows,
    'contact_pair_20mOhm_each': [{'A': i, 'drop_V': i * .04, 'loss_W': i*i*.04} for i in [3,5,10]],
    'two_5V_1A_accessories': [{'BEC_V': v, 'efficiency_assumed': .9,
                             'input_A': 10/(.9*v), 'ten_A_BEC_servo_budget_before_FC_A': 10-10/(.9*v)}
                            for v in [6,7.4,8]],
    'rating_only_budget_with_1p1A_main': [{'stronger_feed_share': f,
          'total_A_ceiling': 3/f, 'servo_A_ceiling': 3/f-1.1} for f in [.5,.8,1]],
    'KST_setup': {
        'user_confirmed': '3 x KST BLS505, 1 x KST DS565X, Hobbywing 120 A V4, 7.4 V BEC, both BEC power plugs',
        'unconfirmed': ['location of second BEC feed plug', 'other accessory loads', 'actual harness resistances and contact details'],
        'graph_screen_at_7p4V': {
            'BLS505_A_rounded_approx': 5, 'BLS505_count': 3,
            'DS565X_A_rounded_approx': 3.5, 'DS565X_count': 1,
            'combined_servo_A': 18.5, 'with_abstract_main_A': 19.6,
            'meaning': 'Rounded visual readings near upper plotted torque, not exact published stall currents, typical flight loads or certified limits. Constant-current stress does not model servo current reduction with voltage sag.'},
        'primary_evidence': {p.name: sha(p) for p in sorted((OUT/'primary-evidence').glob('*.pdf'))},
    },
}
(OUT / 'calculations.json').write_text(json.dumps(result, indent=2) + '\n')
for r in rows:
    print(r['allocation'], r['profile'], 'feed A', round(r['max_feed_conductor_A'],4),
          'board W', round(r['copper_and_barrel_W'],5),
          'board-only drop mV', round(r.get('board_only_worst_servo_drop_V',0)*1000,3))
print('baseline error', reproduction_error, 'max residual', max(r['linear_residual_A'] for r in rows))
