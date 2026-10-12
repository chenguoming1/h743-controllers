"""Read-only result reduction. Does not import or execute numerical modules."""
import hashlib, json, math, resource, gzip
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
RESULT=HERE/'run/result.json.gz'
LEDGER=HERE/'run/ledger.json'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def load(path): return json.load(gzip.open(path,'rt') if path.suffix=='.gz' else path.open())
def dump(path,value): path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')

def main():
    result=load(HERE/'reduced-result.json.gz'); ledger=load(LEDGER); execution=load(HERE/'run-execution.json')
    definitions={c['name']:c for c in ledger['cases']}
    required={name for name,c in definitions.items() if c['scope']!='same_BEC_illustrative'}
    illustrative=set(definitions)-required
    assert (len(required),len(illustrative))==(294,11)
    runs=result.get('runs',result.get('partial_runs_unqualified',[]))
    expected_networks=[n['net'] for n in ledger['networks']]
    summary={'schema':'f722-return-stitch-result-summary/v1','result_path':str(RESULT),'result_sha256':sha(RESULT),
      'ledger_sha256':sha(LEDGER),'execution_receipt_sha256':sha(HERE/'run-execution.json'),
      'status':result.get('status','COMPLETED CONDITIONAL DC SCREEN' if 'runs' in result else 'UNKNOWN'),
      'reason':result.get('reason'),'conditional_static_screen_pass':result.get('conditional_static_screen_pass'),
      'source_bytes_unchanged':execution['all_bound_sources_unchanged'],'returncode':execution['returncode'],
      'elapsed_seconds':execution['elapsed_seconds'],'peak_RSS_KiB':None,
      'required_case_count':len(required),'illustrative_case_count':len(illustrative),'grids':[],
      'full_two_grid_result':'runs' in result and [x['spacing_mm'] for x in runs]==[.12,.09],
      'partial_results_qualified':False,'electrical_final_acceptance_claimed':False}
    for run in runs:
        cases=run['cases']; names=[c['case'] for c in cases]
        assert len(names)==len(set(names))==305 and set(names)==set(definitions)
        assert all(c['case_definition_sha256']==definitions[c['case']]['case_definition_sha256'] for c in cases)
        assert [n['net'] for n in run['ports']]==expected_networks
        failures=[]
        for case in cases:
            for probe in case['probes']:
                if not probe['pass']:
                    failures.append({'case':case['case'],'case_group':'required' if case['case'] in required else 'illustrative',**probe})
        summary['grids'].append({'spacing_mm':run['spacing_mm'],'cases':len(cases),'networks':len(run['ports']),
          'all_case_identity_hashes_match':True,'required_static_pass':all(c['static_probe_pass'] for c in cases if c['case'] in required),
          'required_static_failed_cases':sorted({x['case'] for x in failures if x['case_group']=='required'}),
          'illustrative_static_failed_cases':sorted({x['case'] for x in failures if x['case_group']=='illustrative'}),
          'probe_failures':failures,'loops':[{k:v for k,v in loop.items() if k!='legs'} for loop in run['loops']]})
    summary['impedance_sensitivity']=result.get('impedance_sensitivity')
    summary['resistance_margin_checks']=result.get('resistance_margin_checks')
    margins=result.get('voltage_margin_checks',[])
    summary['required_voltage_margin_failures']=[m for m in margins if m['case'] in required and not m['pass']]
    summary['illustrative_voltage_margin_failures']=[m for m in margins if m['case'] in illustrative and not m['pass']]
    summary['all_impedance_sensitivity_pass']=all(x['pass'] for x in result.get('impedance_sensitivity',[])) if summary['full_two_grid_result'] else None
    summary['all_resistance_margin_checks_pass']=all(x['pass'] for x in result.get('resistance_margin_checks',[])) if summary['full_two_grid_result'] else None
    if runs:
        fine=runs[-1]; required_cases=[c for c in fine['cases'] if c['case'] in required]
        extrema={}
        for case in required_cases:
            for probe in case['probes']:
                key=probe['name']; row={'case':case['case'],'voltage_V':probe['voltage_V'],'minimum_V':probe.get('minimum_V'),'maximum_V':probe.get('maximum_V')}
                margin=min(probe['voltage_V']-probe.get('minimum_V',-math.inf),probe.get('maximum_V',math.inf)-probe['voltage_V'])
                row['nearest_floor_or_ceiling_margin_V']=margin
                if key not in extrema or row['voltage_V']<extrema[key]['voltage_V']:extrema[key]=row
        summary['latest_grid_required_probe_minima']=extrema
        flash=[]
        for case in required_cases:
            definition=definitions[case['case']]
            if definition['parameters']['bounded_allocation_A']['flash']<=0:continue
            v=case['voltage_V'];probe=next(x for x in case['probes'] if x['name']=='actual_rail_flash')
            flash.append({'case':case['case'],'supply':definition['supply'],'flash_current_A':definition['parameters']['bounded_allocation_A']['flash'],
              'actual_flash_voltage_V':probe['voltage_V'],'minimum_V':probe['minimum_V'],
              'supply_drop_L2_2_to_U3_8_V':v['L2.2']-v['U3.8'],'return_difference_U3_4_to_U9_1_V':v['U3.4']-v['U9.1']})
        summary['latest_grid_flash_loaded_cases']=flash
        summary['geometry_certificate_count']=len(result.get('geometry_certificate_summaries',{}))
        summary['mesh_cache_receipt_count']=len(result.get('mesh_cache_receipts',[]))
    dump(HERE/'result-summary.json',summary)
    print(json.dumps({k:summary[k] for k in ['status','reason','conditional_static_screen_pass','full_two_grid_result','required_voltage_margin_failures','illustrative_voltage_margin_failures','all_impedance_sensitivity_pass','all_resistance_margin_checks_pass']},indent=2))

if __name__=='__main__':main()
