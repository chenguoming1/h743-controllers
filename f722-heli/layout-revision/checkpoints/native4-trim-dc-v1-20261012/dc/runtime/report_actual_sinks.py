#!/usr/bin/env python3
"""Strict actual-pad report extractor for a future corrected two-grid result.

No solver imports. The report refuses stale/missing/duplicate source, case,
probe or convergence evidence. It never upgrades a refused or failed solve.
"""
import argparse
import math
from pathlib import Path
from power_case_model import digest,require,Refused,sink_probes
from validate_static import read_json as read,sha256 as sha
from compile_power_ledger import save
from model_contract import check_ledger

def unique(rows,key,label):
    result={row[key]:row for row in rows}
    require(len(result)==len(rows),'Duplicate '+label)
    return result

def extract(result,ledger,expected_board,expected_ledger,expected_freeze):
    require(result.get('board_sha256')==expected_board,'Result board identity differs')
    require(result.get('ledger_sha256')==expected_ledger,'Result ledger identity differs')
    require(result.get('freeze_sha256')==expected_freeze,'Result freeze identity differs')
    if result.get('status')=='REFUSED':
        return {'status':'REFUSED; NO ACTUAL-SINK ACCEPTANCE','board_sha256':expected_board,
                'reason':result.get('reason'),'runner_overall_boolean':result.get('conditional_static_screen_pass'),
                'partial_runs_unqualified':result.get('partial_runs_unqualified',[])}
    check_ledger(ledger,ledger['model_contract'],full=True)
    definitions=unique(ledger['cases'],'name','ledger case')
    require(len(definitions)==sum(ledger['model_contract']['counts'][k] for k in ['required','illustrative']),'Corrected scope missing')
    runs=result.get('runs',[])
    require([r['spacing_mm'] for r in runs]==ledger['mesh_spacings_mm']==[.12,.09],'Incomplete or wrong two-grid result')
    margins={}
    for row in result.get('voltage_margin_checks',[]):
        key=(row['case'],row['probe'])
        require(key not in margins,'Duplicate convergence evidence')
        margins[key]=row
    expected_margins={(name,p['name']) for name,c in definitions.items() for p in c['probes']}
    require(set(margins)==expected_margins,'Missing, extra or stale voltage convergence evidence')
    grid_cases=[unique(run['cases'],'case','result case') for run in runs]
    require(all(set(rows)==set(definitions) for rows in grid_cases),'Missing, extra or stale result case')
    for name,c in definitions.items():
        grid_probes=[unique(rows[name]['probes'],'name','result probe') for rows in grid_cases]
        require(all(set(ps)=={p['name'] for p in c['probes']} for ps in grid_probes),'Missing or extra result probe')
        for p in c['probes']:
            a,b=[ps[p['name']]['voltage_V'] for ps in grid_probes]
            require(math.isfinite(a) and math.isfinite(b),'Nonfinite probe voltage')
            delta=abs(a-b);margin=min(b-p.get('minimum_V',-math.inf),p.get('maximum_V',math.inf)-b)
            tolerance=ledger['convergence']['absolute_voltage_V'];guard=max(delta,tolerance)
            g=margins[(name,p['name'])]
            for key,value in [('change_V',delta),('margin_V',margin),('numerical_guard_V',guard)]:
                require(math.isfinite(g[key]) and abs(g[key]-value)<1e-10,'Rewritten voltage convergence evidence')
            require(g['pass'] is (delta<=tolerance and margin>=guard),'Rewritten voltage convergence outcome')
    output=[];bias=[]
    for run in runs:
        rows=unique(run['cases'],'case','result case')
        require(set(rows)==set(definitions),'Missing, extra or stale result case')
        for name,c in definitions.items():
            row=rows[name]
            require(row.get('case_definition_sha256')==c['case_definition_sha256'],'Resolved case hash differs: '+name)
            require(digest({k:v for k,v in c.items() if k!='case_definition_sha256'})==c['case_definition_sha256'],'Ledger case bytes changed')
            probes=unique(row['probes'],'name','result probe')
            require(set(probes)=={p['name'] for p in c['probes']},'Missing or extra result probe')
            for p in sink_probes(c['supply']):
                r=probes[p['name']];v=r['voltage_V'];g=margins[(name,p['name'])]
                require(math.isfinite(v),'Nonfinite sink voltage')
                require((r.get('minimum_V'),r.get('maximum_V'))==(p['minimum_V'],p['maximum_V']),'Sink floor/ceiling differs')
                actual=row['voltage_V'][p['p']]-row['voltage_V'][p['n']]
                require(abs(actual-v)<1e-10,'Actual pad/reference report mismatch')
                lower=v-p['minimum_V'];upper=p['maximum_V']-v
                pass_window=lower>=0 and upper>=0
                require(r.get('pass') is pass_window,'Rewritten sink window outcome')
                output.append({'case':name,'scope':c['scope'],'grid_mm':run['spacing_mm'],
                    'sink':p['name'],'p':p['p'],'n':p['n'],'mode':p['mode'],'voltage_V':v,
                    'minimum_V':p['minimum_V'],'maximum_V':p['maximum_V'],
                    'lower_margin_V':lower,'upper_margin_V':upper,'window_pass':pass_window,
                    'two_grid_guard':g,'purpose':p['purpose']})
            volts=row['voltage_V'];vbat=volts['U1.1']-volts['U1.18']
            csb=volts['U4.2']-volts['U4.1'];io=volts['U4.6']-volts['U4.1']
            bias.append({'case':name,'grid_mm':run['spacing_mm'],'VBAT_local_V':vbat,
                         'VBAT_1p65_to_3p6_window':1.65<=vbat<=3.6,
                         'CSB_local_V':csb,'VDDIO_local_V':io,'CSB_minus_0p7_VDDIO_V':csb-.7*io,
                         'acceptance':'Separate role observations, not full functional or signal timing qualification'})
    return {'status':'ACTUAL-SINK REPORT; CONDITIONAL DC EVIDENCE ONLY',
        'board_sha256':expected_board,'ledger_sha256':expected_ledger,'freeze_sha256':expected_freeze,
        'runner_overall_boolean':result['conditional_static_screen_pass'],
        'actual_supply_rows':output,'bias_role_rows':bias,
        'sink_window_failures':sum(not r['window_pass'] for r in output),
        'sink_two_grid_failures':sum(not r['two_grid_guard']['pass'] for r in output[ len(output)//2:]),
        'limitations':['Preserves all failures and the original runner boolean.',
                       '294 required cases and11 illustrations remain separately classified.',
                       'Conditional branch-current and hot-DCR engineering bounds require bench evidence.',
                       'No universal CORE or flight qualification; VDDA tracking, clocks, signals, package sharing, AC and component temperature remain separate.']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['result','ledger','freeze','out']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--expected-board-sha',required=True)
    a=p.parse_args();require(not a.out.exists(),'Preserve prior report')
    freeze=read(a.freeze);board=freeze['files']['board']
    require(board['sha256']==a.expected_board_sha and sha((a.freeze.parent/board['path']).resolve())==a.expected_board_sha,'Frozen board differs')
    report=extract(read(a.result),read(a.ledger),a.expected_board_sha,sha(a.ledger),sha(a.freeze))
    report['result_sha256']=sha(a.result);report['reporter_sha256']=sha(__file__)
    save(a.out,report)

if __name__=='__main__':main()
