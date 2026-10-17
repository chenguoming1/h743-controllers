"""Summarize completed source-bound impedance calculations and checks."""
from pathlib import Path
import hashlib
import json

OUT=Path(__file__).resolve().parent
results=json.loads((OUT/'results.json').read_text())['results']
etch=json.loads((OUT/'etch-sensitivity.json').read_text())
domain=json.loads((OUT/'domain-convergence.json').read_text())
def case(rows,name,mesh):
    return next(a for a in rows if a['name']==name and a['mesh_mm']==mesh)
source=OUT.parents[3]/'hardware/nexus-style-fc.kicad_pcb'
sha=hashlib.sha256(source.read_bytes()).hexdigest()
assert sha==json.loads((OUT/'sections.json').read_text())['sha256']
summary=dict(source_sha256=sha,source_unchanged=True,
    analytic_parallel_plates=json.loads((OUT/'numerical-validation.json').read_text()),
    ideal_case_mesh_change_ohm={a['name']:abs(a['differential_ohm']-case(etch,a['name'],.0025)['differential_ohm']) for a in etch if a['mesh_mm']==.00125},
    ideal_case_domain_width_change_ohm={a['name']:abs(a['differential_ohm']-case(results,a['name'],.0025)['differential_ohm']) for a in domain},
    jlc_independent_cross_check=dict(manufacturer_synthesized_width_mm=.1171,gap_mm=.127,
        manufacturer_target_ohm=90,our_etched_model_ohm=case(etch,'JLC3313 standard ideal planes at synthesized 0.1171 width',.00125)['differential_ohm'],
        stack_name='JLC06161H-3313 standard, 1 oz outer / 0.5 oz inner, L4 with L3/L5 references',production_stack_selected=False),
    max_float_charge_C_per_m=max(abs(q) for a in results for k,q in a['dielectric']['charge_C_per_m'].items() if int(k)>=3),
    max_equation_residual_C_per_m=max(a['dielectric']['max_residual_C_per_m'] for a in results+etch),
    actual_slices_etched_estimate_min_ohm=min(a['differential_ohm'] for a in etch if a['name'].startswith('CAD slice')),
    actual_slices_etched_estimate_max_ohm=max(a['differential_ohm'] for a in etch if a['name'].startswith('CAD slice')))
(OUT/'validation-summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
