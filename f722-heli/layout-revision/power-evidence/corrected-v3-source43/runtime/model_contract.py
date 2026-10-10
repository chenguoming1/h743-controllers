"""Exact corrected-model identity and refusal guards, independent of FEM."""
import copy
from power_case_model import digest,require,Refused,build_cases,check_corrected_case,PARTS,REQUIRED_PADS

REVISION='f722-physical-terminal-correction/v2'
JOB_KEYS=['cases','networks','loops','material','mesh_spacings_mm','convergence','limits']

def registry_networks(registry):
    require(registry.get('schema')=='f722-corrected-terminal-registry-disabled/v2' and registry.get('execution_enabled')is False,
            'Expected corrected disabled terminal registry')
    networks={}
    for name,row in registry['contacts'].items():
        require(row.get('pads') and row.get('layer') in ['F.Cu','B.Cu'],'Invalid physical terminal definition')
        networks.setdefault(row['net'],{})[name]={'pads':row['pads'],'layer':row['layer']}
    return [{'net':net,'contacts':contacts} for net,contacts in sorted(networks.items())]

def definition_contract(plan,registry,settings):
    families,_=build_cases(plan,settings)
    cases=[c for family in families.values() for c in family]
    networks=registry_networks(registry)
    require(len({c['name'] for c in cases})==len(cases),'Duplicate corrected cases')
    for c in cases:check_corrected_case(c)
    used={r[k] for c in cases for cat in ['sources','resistors','loads','converters','probes','report_only_probes'] for r in c.get(cat,[]) for k in ['p','n','in_p','in_n','out_p','out_n','sense_p','sense_n'] if k in r}
    used.update(k for loop in plan['VCAP_copper_loops'] for leg in loop['legs'] for k in [leg['source'],leg['sink']])
    virtual={'SOURCE_GND','BEC_POS','USB_SOURCE','DEV_U7_OUT','DEV_U8_OUT'}
    contacts={p for n in networks for p in n['contacts']}
    require(contacts==used-virtual,'Missing or extraneous corrected physical contact')
    require(all(len(n['contacts'])>=2 for n in networks),'One-port corrected network')
    physics={key:copy.deepcopy(settings[key]) for key in ['material','mesh_spacings_mm','convergence','limits']}
    job={**physics,'cases':cases,'networks':networks,'loops':plan['VCAP_copper_loops']}
    return {'model_revision':REVISION,
            'case_definitions':{c['name']:c['case_definition_sha256'] for c in cases},
            'case_order':[c['name'] for c in cases],
            'case_scopes':{c['name']:c['scope'] for c in cases},
            'job_sha256':{key:digest(job[key]) for key in JOB_KEYS},
            'counts':{'required':len(families['baseline']),'illustrative':len(families['servo']),
                      'loops':len(job['loops']),'networks':len(networks),'contacts':len(contacts),
                      'ground_contacts':sum(len(n['contacts']) for n in networks if n['net']=='GND')},
            'context_equivalence_sha256':digest(plan['historical_context_equivalence']),
            'scope':'Enumerated conditional prototype DC cases; exact current-polytope coverage is not a nonlinear interior-extrema proof.'}

def check_inputs(plan,registry,settings):
    actual=definition_contract(plan,registry,settings)
    require(plan.get('model_contract')==actual,'Corrected definition contract changed')
    require(registry.get('model_contract_sha256')==digest(actual),'Registry belongs to a different corrected model')
    return actual

def check_physical_source(parts,native,plan):
    for ref,spec in plan['selected_part_contract'].items():
        require(parts.get(ref,{}).get('mpn')==spec['mpn'],'Selected physical part/package changed: '+ref)
    pads={p['key']:p for p in native['objects'] if p['kind']=='pad' and p.get('number')}
    for key,spec in plan['physical_pad_contract'].items():
        actual=pads.get(key,{})
        require(actual.get('net')==spec['net'] and sorted(actual.get('copper',{}))==spec['layers'],
                'Power/control/sense physical pad identity changed: '+key)
    for key,(net,layer) in REQUIRED_PADS.items():
        require(key in pads and pads[key]['net']==net and layer in pads[key]['copper'],'Actual sink/entry identity changed: '+key)

def check_ledger(ledger,contract,full=False):
    require(ledger.get('model_revision')==contract.get('model_revision')==REVISION,'Missing corrected model revision')
    require(ledger.get('model_contract')==contract,'Ledger/manifest model contract differs')
    cases=ledger['cases'];names=[c['name'] for c in cases]
    expected=contract['case_order']
    if not full:
        family=ledger.get('case_family')
        if family=='baseline':expected=[n for n in expected if contract['case_scopes'][n]!='same_BEC_illustrative']
        elif family=='servo':expected=[n for n in expected if contract['case_scopes'][n]=='same_BEC_illustrative']
        else:require(family in ['primary','corrected-primary-and-VCAP'],'Unknown corrected case family')
    require(names==expected,'Corrected case membership/order changed')
    for case in cases:
        require(case.get('model_revision')==REVISION,'Case model revision differs')
        check_corrected_case(case)
        actual=digest({k:v for k,v in case.items() if k!='case_definition_sha256'})
        require(case.get('case_definition_sha256')==actual==contract['case_definitions'].get(case['name']),
                'Corrected resolved case identity changed: '+case['name'])
    for key in JOB_KEYS:
        if key!='cases' or full:
            require(digest(ledger[key])==contract['job_sha256'][key],'Corrected operational job changed: '+key)
    return contract['counts']
