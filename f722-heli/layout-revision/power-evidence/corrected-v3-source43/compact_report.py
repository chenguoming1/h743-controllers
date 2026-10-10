#!/usr/bin/env python3
"""Deterministic compact projection of the exact combined summary, not raw replay."""
from collections import defaultdict

def compact(summary, launch):
    a=summary['actual_sink_report']; groups=defaultdict(list)
    for r in a['actual_supply_rows']:
        groups[(r['scope'],r['sink'])].append(r)
    extrema=[]
    for (scope,sink),rows in sorted(groups.items()):
        lo=min(rows,key=lambda r:r['voltage_V']); hi=max(rows,key=lambda r:r['voltage_V'])
        minimum=min(rows,key=lambda r:min(r['lower_margin_V'],r['upper_margin_V']))
        first=rows[0]
        extrema.append(dict(scope=scope,sink=sink,p=first['p'],n=first['n'],mode=first['mode'],row_count=len(rows),
            minimum_V=first['minimum_V'],maximum_V=first['maximum_V'],observed_min_V=lo['voltage_V'],observed_min_case=lo['case'],observed_min_grid_mm=lo['grid_mm'],
            observed_max_V=hi['voltage_V'],observed_max_case=hi['case'],observed_max_grid_mm=hi['grid_mm'],
            minimum_window_margin_V=min(minimum['lower_margin_V'],minimum['upper_margin_V']),
            window_failures=sum(not r['window_pass'] for r in rows),two_grid_failures=sum(not r['two_grid_guard']['pass'] for r in rows),purpose=first['purpose']))
    decisions={k:v for k,v in summary['scope_decisions'].items() if not isinstance(v,list)}
    failures=[r for r in summary['scope_decisions']['illustrative_voltage_checks'] if not r['pass']]
    illustrates=[{k:r[k] for k in ['case','lead_current_A','servo_pad_voltage_V']} for r in summary['same_BEC_illustrations_fine_grid']]
    return dict(schema='f722-corrected-power-compact-evidence/v1',
        derivation='Deterministic projection of exact combined-summary.json; not raw result replay or a new numerical solution.',
        identities={k:summary[k] for k in ['board_sha256','result_sha256','freeze_sha256','ledger_sha256']},
        launch=dict(launch),scope=summary['scope'],scope_is_final_board=summary['scope_is_final_board'],
        conditional_static_screen_pass=summary['conditional_static_screen_pass'],thermal_or_flight_qualification=summary['thermal_or_flight_qualification'],
        scope_decisions=decisions,mesh_spacings_mm=summary['mesh_spacings_mm'],material=summary['material'],convergence_requirements=summary['convergence_requirements'],
        cases_per_grid=summary['cases_per_grid'],networks_per_grid=summary['networks_per_grid'],contacts=summary['contacts'],
        verification=summary['verification'],actual_supply_row_count=len(a['actual_supply_rows']),bias_role_row_count=len(a['bias_role_rows']),
        sink_window_failures=a['sink_window_failures'],sink_two_grid_failures=a['sink_two_grid_failures'],actual_supply_extrema=extrema,
        voltage_checks=summary['voltage_checks'],illustrative_failures=failures,illustrative_fine_grid=illustrates,
        impedance_sensitivity=summary['impedance_sensitivity'],VCAP_runs=summary['VCAP_runs'],VCAP_resistance_checks=summary['scope_decisions']['VCAP_resistance_checks'],
        VCAP_numerical_extrema=summary['VCAP_numerical_extrema'],observed_numerical_extrema=summary['observed_numerical_extrema'],geometry=summary['geometry'],
        limitations=summary['limitations']+a['limitations'])
