"""Fixed-geometry child material sensitivity; no CAD or original evidence edits."""
from pathlib import Path
import json

OUT = Path(__file__).resolve().parent
# Reuse the verified setup and parameterized solver, stopping before any output loop.
setup = (OUT / 'calculate.py').read_text().split('rows = []')[0]
context = {'__file__': str(OUT / 'calculate.py')}
exec(compile(setup, '<verified-child-network-setup>', 'exec'), context)
run = context['ns']['run']
rows = []
for copper, wall in [(60,18),(90,18),(120,18),(60,25),(60,35),(90,25),(120,35)]:
    r = run(.075, copper, 80, .95, wall, 'both_equal20m',
            'KST_rounded_upper_graph_plus_main_19p6A', main_current_A=1.1,
            barrel_length_mm=1.65, header_bore_mm=.97)
    rows.append(r)
    print(copper, wall, 'sheet W',round(r['sheet_loss_W'],5),
          'barrel W',round(r['barrel_loss_W'],5),'total W',round(r['copper_and_barrel_W'],5))
assert max(r['linear_residual_A'] for r in rows) < 1e-7
assert max(abs(r['power_balance_error_W']) for r in rows) < 1e-5
I = 19.6
result = {
    'scope': 'Material-only sensitivities on exact current child geometry, synthetic matched dual feeds, 19.6 A imposed allocation, 80 C prescribed. Not candidate layouts, supplier guarantees or thermal ratings.',
    'source_sha256': context['seal']['source_sha256_before_and_after'],
    'rows': rows,
    'illustrative_design_targets_not_approved_limits': {
        'design_A_rounded': 20, 'screen_A': I,
        'base_loss_equivalent_mOhm': rows[0]['copper_and_barrel_W']/I**2*1000,
        'loss_target_W': .4, 'target_loss_equivalent_mOhm': .4/I**2*1000,
        'ambient_C_example': 40, 'rise_C_example': 20,
        'lumped_thermal_C_per_W_needed_at_base': 20/rows[0]['copper_and_barrel_W'],
        'lumped_thermal_C_per_W_at_target': 20/.4,
        'limitation': 'P/I^2 is a loss-equivalent value for this distributed load, not a unique feed-to-servo resistance. A lumped thermal check does not bound local hot spots.',
    },
    'not_modeled': ['changed rear power-pour geometry', 'new stitching vias',
                    'current sharing through soldered header pins', 'thermal equilibrium',
                    'contact/harness losses', 'BEC dynamics'],
}
(OUT/'full-load-options.json').write_text(json.dumps(result,indent=2)+'\n')
