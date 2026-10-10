#!/usr/bin/env python3
"""Corrected physical case definitions; pure data transformations, no solve."""
import copy
import hashlib
import json
import math
SCHEMA='f722-corrected-power-primary-model/v2'
BRANCH_LIMIT_A = .020

FERRITE_SCREEN_OHM = 1.0

UNFILTERED = {
    'mcu_vdd19': ('U1.19', 'U1.18'),
    'mcu_vdd32': ('U1.32', 'U1.31'),
    'mcu_vdd48': ('U1.48', 'U1.47'),
    'mcu_vdd64': ('U1.64', 'U1.63'),
    'flash': ('U3.8', 'U3.4'),
    'barometer_vddio': ('U4.6', 'U4.1'),
    'barometer_vdd': ('U4.8', 'U4.7'),
}

FILTERED = {'analog': ('U1.13', 'U1.12'),
            'imu_vddio': ('U2.5', 'U2.6'),
            'imu_vdd': ('U2.8', 'U2.6')}

PARTS = {'U1': 'STM32F722RET6', 'U2': 'ICM-42688-P',
         'U3': 'W25N01GVZEIG', 'U4': 'DPS368XTSA1',
         'U10': 'TPS2553DRVR', 'U11': 'TPS2553DRVR',
         'FB1': 'BLM15AG601SN1D', 'FB2': 'BLM15AG601SN1D'}

REQUIRED_PADS = {
    **{p: ('+3V3_CORE', 'B.Cu') for p in ['U1.1','U1.19','U1.32','U1.48','U1.64','U3.8','U11.4','U11.6','FB1.1']},
    **{p: ('GND', 'B.Cu') for p in ['U1.12','U1.18','U1.31','U1.47','U1.63','U3.4','U10.5','U11.5']},
    **{p: ('+3V3_CORE', 'F.Cu') for p in ['U4.2','U4.6','U4.8','FB2.1']},
    **{p: ('GND', 'F.Cu') for p in ['U2.6','U4.1','U4.5','U4.7']},
    'U10.4': ('USB_VBUS_RAW','B.Cu'), 'U10.6': ('USB_VBUS_RAW','B.Cu'),
    'U10.1': ('USB_LIMITED','B.Cu'), 'U11.1': ('+3V3_DSM','B.Cu'),
    'FB1.2': ('+3V3_ANALOG','B.Cu'), 'U1.13': ('+3V3_ANALOG','B.Cu'),
    'FB2.2': ('+3V3_IMU','F.Cu'), 'U2.5': ('+3V3_IMU','F.Cu'), 'U2.8': ('+3V3_IMU','F.Cu'),
}

ROLE_CORRECTIONS = [
    {'component':'U10','part':'TPS2553DRVR','category':'resistors','name':'U10_USB_limiter_path','old_p':'U10.4','p':'U10.6','n':'U10.1','role':'IN -> OUT'},
    {'component':'U11','part':'TPS2553DRVR','category':'resistors','name':'U11_selected_path','old_p':'U11.4','p':'U11.6','n':'U11.1','role':'IN -> OUT'},
    {'component':'U10','part':'TPS2553DRVR','category':'loads','name':'U10_IQ_table_screen','old_p':'U10.4','p':'U10.6','n':'U10.5','role':'IN -> GND'},
    {'component':'U10','part':'TPS2553DRVR','category':'loads','name':'added_auxiliary_U10.4','old_p':'U10.4','p':'U10.6','n':'U10.5','role':'IN -> GND'},
]

FORBIDDEN_SUPPLY_PADS = {'U10.4':'EN', 'U11.4':'EN', 'U4.2':'CSB', 'U4.5':'SDO'}

class Refused(RuntimeError): pass

def require(condition, message):
    if not condition:
        raise Refused(message)

def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def allocation_vertices(total):
    require(total in [.30,.32], 'Unreviewed aggregate electronics budget')
    rows=[]
    for name,(p,n) in UNFILTERED.items():
        for analog in [0.,BRANCH_LIMIT_A]:
            for imu in ['none','imu_vddio','imu_vdd']:
                imu_current=0. if imu=='none' else BRANCH_LIMIT_A
                currents={key:0. for key in [*UNFILTERED,*FILTERED]}
                currents[name]=round(total-analog-imu_current,9)
                currents['analog']=analog
                if imu!='none': currents[imu]=imu_current
                rows.append({'name':f'{name}__analog{int(1000*analog)}m__{imu}',
                             'currents_A':currents})
    require(len(rows)==42 and len({r['name'] for r in rows})==42,'Wrong vertex set')
    return rows

def convex_weights(currents,total):
    """Explicit witness: every feasible allocation is in this 42-vertex hull.

    This proves load-polytope coverage, not global voltage extrema for nonlinear
    constant-power converters. That separate numerical claim is not made here.
    """
    require(set(currents)==set(UNFILTERED)|set(FILTERED),'Incomplete current vector')
    require(all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) and x>=0 for x in currents.values()),'Invalid allocation current')
    require(abs(sum(currents.values())-total)<1e-12,'Aggregate budget differs')
    a=currents['analog'];i=currents['imu_vddio'];v=currents['imu_vdd']
    require(a<=BRANCH_LIMIT_A and i+v<=BRANCH_LIMIT_A,'Filtered branch over budget')
    remainder=total-a-i-v
    require(remainder>0,'Unfiltered residual must be positive')
    weights=[]
    for row in allocation_vertices(total):
        allocations=row['currents_A']
        key=next(k for k in UNFILTERED if allocations[k]>0)
        pa=a/BRANCH_LIMIT_A if allocations['analog'] else 1-a/BRANCH_LIMIT_A
        pi=i/BRANCH_LIMIT_A if allocations['imu_vddio'] else v/BRANCH_LIMIT_A if allocations['imu_vdd'] else 1-(i+v)/BRANCH_LIMIT_A
        weights.append(currents[key]/remainder*pa*pi)
    require(abs(sum(weights)-1)<1e-12 and min(weights)>=-1e-15,'Invalid convex witness')
    for key,value in currents.items():
        actual=sum(w*r['currents_A'][key] for w,r in zip(weights,allocation_vertices(total)))
        require(abs(actual-value)<1e-12,'Convex witness does not reconstruct '+key)
    return weights

def corrected_paths(case):
    for rule in ROLE_CORRECTIONS:
        for row in case.get(rule['category'],[]):
            if row['name']==rule['name']:
                require(row['p']==rule['old_p'] and row['n']==rule['n'],'Unexpected historical terminal path: '+rule['name'])
                row['p']=rule['p']
                row['terminal_correction']='TPS2553 DRV IN=6; EN=4 is not a supply-current entry'
    return case

def sink_probes(supply):
    mode='stock_216MHz_scale1_overdrive_7WS' if supply=='BEC' else 'stock_USB_FS_full_spec'
    mcu_floor=2.7 if supply=='BEC' else 3.0
    rows=[]
    for key,(p,n) in {**UNFILTERED,**FILTERED}.items():
        floor=mcu_floor if key.startswith('mcu') or key=='analog' else 2.7 if key=='flash' else 1.2 if key=='barometer_vddio' else 1.7 if key=='barometer_vdd' else 1.71
        rows.append({'name':'actual_rail_'+key,'p':p,'n':n,'minimum_V':floor,'maximum_V':3.6,
                     'mode':mode,'purpose':('Conditional conservative VDDA design screen; does not establish steady-state VDDA/VDD tracking or ADC accuracy.' if key=='analog' else 'Selected-part recommended operating DC supply window for '+mode+'; excludes signal levels, startup and AC behavior.')})
    return rows

def check_corrected_case(case):
    expected_resistors={'U11_selected_path':('U11.6','U11.1')}
    if case['supply']=='USB':
        expected_resistors.update(U10_USB_limiter_path=('U10.6','U10.1'),
                                 U7_USB_selected_path=('U7.6','DEV_U7_OUT'),
                                 U8_USB_selected_path=('U8.2','DEV_U8_OUT'))
    else:
        expected_resistors.update(U5_efuse_path=('U5.5','U5.6'),
                                 U7_BEC_selected_path=('U7.3','DEV_U7_OUT'),
                                 U8_BEC_selected_path=('U8.7','DEV_U8_OUT'))
    by_name={r['name']:r for r in case['resistors']}
    require(len(by_name)==len(case['resistors']),'Duplicate device/resistor name')
    for name,pair in expected_resistors.items():
        require(name in by_name and (by_name[name]['p'],by_name[name]['n'])==pair,
                'Missing or wrong physical selected path: '+name)
    for converter in case['converters']:
        expected={'U9_total_efficiency':('U9.2','U9.1','L2.2','U9.1','U9.6','U9.4'),
                  'U6_total_efficiency':('U6.VIN_12_13','U6.10','U6.OUT_7_8','U6.10','U6.5','U6.4')}
        require(converter['name'] in expected and tuple(converter[k] for k in ['in_p','in_n','out_p','out_n','sense_p','sense_n'])==expected[converter['name']],
                'Converter physical power/sense role differs')
    require({c['name'] for c in case['converters']}==({'U9_total_efficiency'} if case['supply']=='USB' else {'U9_total_efficiency','U6_total_efficiency'}),'Missing physical converter')
    for category in ['resistors','loads']:
        for row in case.get(category,[]):
            if row['name'] in [r['name'] for r in ROLE_CORRECTIONS]:
                rule=next(r for r in ROLE_CORRECTIONS if r['name']==row['name'])
                require((row['p'],row['n'])==(rule['p'],rule['n']),'Control pin used as power terminal: '+row['name'])
    loads=[r for r in case['loads'] if r['name'].startswith('aggregate_electronics_adversarial')]
    require(abs(sum(r['current_A'] for r in loads)-case['parameters']['electronics_A'])<1e-12,'Electronics budget mismatch')
    require(all(r['p'] not in FORBIDDEN_SUPPLY_PADS and r['n'] not in FORBIDDEN_SUPPLY_PADS for r in loads),'Control/strap used as electronics supply or return')
    require(sum(r['current_A'] for r in loads if r['p']=='U1.13')<=BRANCH_LIMIT_A+1e-12,'Analog branch current over budget')
    require(sum(r['current_A'] for r in loads if r['p'] in ['U2.5','U2.8'])<=BRANCH_LIMIT_A+1e-12,'Combined IMU branch current over budget')
    probes={r['name']:r for r in case['probes']}
    for expected in sink_probes(case['supply']):
        require(probes.get(expected['name'])==expected,'Missing or altered actual sink/mode window: '+expected['name'])
    require(case.get('execution_enabled',False)is False,'Case must not carry an independent execution release')

def revise_case(original,vertex=None):
    case=corrected_paths(copy.deepcopy(original))
    case.pop('case_definition_sha256',None)
    case['execution_enabled']=False
    if vertex is not None:
        case['name']='corrected_'+original['scope']+'_'+original['supply']+str(original['parameters']['input_at_defined_source_V'])+'_'+''.join(p[1:] for p in original['parameters']['ABC_ports'])+'_'+vertex['name']
        case['parameters']['allocation_vertex']=vertex['name']
        case['loads']=[r for r in case['loads'] if r['name']!='aggregate_electronics_adversarial']
        for key,current in vertex['currents_A'].items():
            if current:
                p,n={**UNFILTERED,**FILTERED}[key]
                case['loads'].append({'name':'aggregate_electronics_adversarial__'+key,'p':p,'n':n,'current_A':current})
        case['parameters']['bounded_allocation_A']=vertex['currents_A']
    case['nets']=list(dict.fromkeys([*case['nets'],'+3V3_ANALOG','+3V3_IMU']))
    case['resistors'] += [
        {'name':ref+'_conditional_hot_DCR','p':ref+'.1','n':ref+'.2','ohm':FERRITE_SCREEN_OHM,
         'condition':'1 ohm engineering acceptance screen, conditional on measured hot resistance <=1 ohm and branch current <=20mA; not a Murata guarantee or copper-temperature conversion.'}
        for ref in ['FB1','FB2']]
    case['probes'] += sink_probes(case['supply'])
    case['probes'] += [{'name':'U11_actual_IN_operating','p':'U11.6','n':'U11.5','minimum_V':2.5,'maximum_V':6.5},
                       {'name':'U11_EN_high_condition','p':'U11.4','n':'U11.5','minimum_V':1.1,'maximum_V':6.5}]
    if case['supply']=='USB':
        case['probes'] += [{'name':'U10_actual_IN_operating','p':'U10.6','n':'U10.5','minimum_V':2.5,'maximum_V':6.5},
                           {'name':'U10_EN_high_condition','p':'U10.4','n':'U10.5','minimum_V':1.1,'maximum_V':6.5}]
    case['report_only_probes']=[r for r in case['report_only_probes'] if r['name']!='CORE_actual_adversarial_sink']
    case['report_only_probes'] += [
        {'name':'VDDA_relative_to_'+key,'p':'U1.13','n':p,
         'reason':'Steady-state rail tracking difference only; no 300mV steady-state allowance is asserted.'}
        for key,(p,n) in UNFILTERED.items() if key.startswith('mcu')]
    case['report_only_probes'] += [{'name':ref+'_actual_bead_drop','p':ref+'.1','n':ref+'.2',
                                  'reason':'Conditional DCR screen; full branch also includes downstream copper and actual ground return.'} for ref in ['FB1','FB2']]
    case['report_only_probes'] += [
        {'name':'VBAT_local_to_VSS18','p':'U1.1','n':'U1.18',
         'reason':'Backup-domain supply only, recommended1.65..3.6V; VSS18 is the explicit board reference, not an inferred package current split.'},
        {'name':'CSB_local_to_GND1','p':'U4.2','n':'U4.1',
         'reason':'Logic strap only; compare to0.7*actual U4.6 VDDIO in the separate role report.'}]
    case['assumptions'] += [
        'Corrected physical supply entries: TPS2553 pin6 is IN, pin4 is EN; DPS368 pin2 CSB and pin5 SDO are not power entry/return pins.',
        'Filtered branches each have a conditional 20mA budget, with combined IMU VDD+VDDIO <=20mA. Their demand is included once within the electronics aggregate.',
        '42-vertex load-polytope coverage does not by itself prove global voltage extrema for nonlinear constant-power converter equations.',
        '105C remains modeled copper temperature, not ambient, ferrite body temperature, or permitted X5R body temperature.',
        'U11 supply/enable consumption and CORE-powered bias are counted once in the aggregate electronics allowance; their individual injection/contact-current distribution is not separately resolved by this allocation model.',
        'U10 IQ remains the inherited conditional140uA table screen at actual IN6/GND5. Auxiliary2mA sensitivity slices are disabled; any future legacy added_auxiliary_U10.4 label must still map its actual endpoint to IN6 and be renamed before publication.']
    case['U11_bias_current_accounting']={
        'included_once_in_electronics_aggregate':True,'separate_IQ_or_EN_load_added':False,
        'individual_spatial_current_distribution_resolved':False,
        'reference_only':{'IQ_on_max_A':.000140,'IQ_conditions':'VIN6.5V, OUT open, RILIM20kohm; not a verified actual3.3V/loaded bound',
                          'EN_absolute_input_current_A':.0000005,'EN_conditions':'VEN0V or6.5V; not a separately verified actual-state bound'},
        'package_ground_split':'Pin5/exposed-pad current sharing and EN return distribution are not established.',
        'future_change':'A dedicated physical IQ/EN load needs a reviewed bound deducted from the aggregate, with a new model identity; never double count.'}
    check_corrected_case(case)
    case['case_definition_sha256']=digest(case)
    return case

def allocation_independent_context(case):
    """Remove only the five reviewed allocation fields, retaining everything else."""
    value=copy.deepcopy(case)
    for key in ['name','case_definition_sha256']:value.pop(key,None)
    value['parameters'].pop('allocation_vertex',None)
    loads=[r for r in value['loads'] if r['name']=='aggregate_electronics_adversarial']
    probes=[r for r in value['report_only_probes'] if r['name']=='CORE_actual_adversarial_sink']
    require(len(loads)==len(probes)==1,'Historical allocation fields missing or duplicated')
    for row in [*loads,*probes]:
        row['p']='ALLOCATION_POSITIVE';row['n']='ALLOCATION_RETURN'
    return value

def equivalent_context(cases,expected_count):
    require(len(cases)==expected_count,'Historical context case membership changed')
    expected=allocation_independent_context(cases[0])
    require(all(allocation_independent_context(c)==expected for c in cases),
            'Historical cases differ beyond reviewed allocation fields; preserve and review distinct contexts')
    vertices=[c['parameters']['allocation_vertex'] for c in cases]
    require(len(set(vertices))==len(vertices),'Duplicate historical context allocation')
    return digest(expected)

def context_receipt(old):
    groups={}
    for c in old['cases']:
        if c['scope'] in ['classic','capacity']:
            key=c['scope']+'/'+','.join(c['parameters']['ABC_ports'])
            groups.setdefault(key,[]).append(c)
    require(len(groups)==6,'Expected six historical BEC contexts')
    rows={key:{'cases':[c['name'] for c in cases],
               'non_allocation_context_sha256':equivalent_context(cases,10)} for key,cases in groups.items()}
    usb=[c for c in old['cases'] if c['scope']=='usb_configuration']
    rows['USB']={'cases':[c['name'] for c in usb],
                 'non_allocation_context_sha256':equivalent_context(usb,2)}
    return rows

def build_proposal(old):
    require(len(old['cases'])==73 and len(old['loops'])==5,'Historical selection changed')
    required=[c for c in old['cases'] if c['scope'] in ['classic','capacity','usb_configuration']]
    require(len(required)==62,'Historical required count changed')
    context_receipt(old)
    result=[]
    contexts={}
    for c in old['cases']:
        if c['scope'] in ['classic','capacity']:
            key=(c['scope'],tuple(c['parameters']['ABC_ports']))
            contexts.setdefault(key,c)
    require(len(contexts)==6,'Expected six BEC contexts')
    for c in contexts.values():
        for vertex in allocation_vertices(.32): result.append(revise_case(c,vertex))
    usb=[c for c in old['cases'] if c['scope']=='usb_configuration']
    require(len(usb)==2 and all(c['parameters']['electronics_A']==.30 for c in usb),'Historical USB samples changed')
    for vertex in allocation_vertices(.30): result.append(revise_case(usb[0],vertex))
    illustrations=[revise_case(c) for c in old['cases'] if c['scope']=='same_BEC_illustrative']
    result+=illustrations
    require(len(result)==305 and len(illustrations)==11,'Proposed selection count differs')
    require(len({c['name'] for c in result})==len(result),'Duplicate corrected case name')
    proposal=copy.deepcopy(old)
    proposal.update(schema=SCHEMA,status='DISABLED PROPOSAL; NO VALIDATION RESULT',execution_enabled=False,
                    freeze_manifest_sha256=None,assumption_record_sha256=None,definition_source_sha256={},
                    source_stage='Physical terminal correction proposal; source-bound review only',
                    cases=result,case_family='294-required-and-11-illustrative-corrected-proposal')
    return proposal

def build_cases(plan,settings):
    require(plan.get('schema')=='f722-corrected-case-plan-disabled/v2' and plan.get('execution_enabled')is False,
            'Expected reviewed corrected disabled plan')
    old=plan['historical_primary']
    require(digest(old)==plan['historical_primary_definition_sha256'],'Historical context definitions changed')
    receipt=context_receipt(old)
    require(receipt==plan['historical_context_equivalence'],'Bound historical context equivalence changed')
    proposal=build_proposal(old)
    for key in ['material','mesh_spacings_mm','convergence','limits']:
        require(settings[key]==old[key],'Preserved physical/numerical settings changed: '+key)
    require(plan['VCAP_copper_loops']==old['loops'],'Preserved VCAP loops changed')
    families={'baseline':[],'servo':[]}
    for case in proposal['cases']:
        case.pop('case_definition_sha256',None)
        case.pop('execution_enabled',None)
        case['model_revision']='f722-physical-terminal-correction/v2'
        case['qualification']='Conditional prototype DC case only; no nonlinear interior-extrema, component-temperature, package-current-sharing, AC or flight guarantee'
        case['case_definition_sha256']=digest(case)
        families['servo' if case['scope']=='same_BEC_illustrative' else 'baseline'].append(case)
    return families,[]
