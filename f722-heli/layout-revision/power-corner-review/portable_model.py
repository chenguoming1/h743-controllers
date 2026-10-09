"""Portable circuit-only functions extracted from reviewed source files.

Read source-identities.json for function provenance. The sealed impedance export
is an input, not independently reproduced field evidence.
"""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
from copper_fem import Refused
from dc_circuit import solve_circuit
from power_case_model import case_factory
ROOT=Path(__file__).resolve().parent
PLAN=ROOT/'inputs/case-plan.disabled.json'
REFERENCE=ROOT/'inputs/reference'
SOURCE_BOUNDS=ROOT/'inputs/source-bounds.json'
def sha256(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
LAUNCH_SOURCE_SHA256=sha256(__file__)

def save(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def stamp_cases(cases):
    for case in cases:
        case.pop('case_definition_sha256',None)
        case['case_definition_sha256']=hashlib.sha256(json.dumps(case,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def materialize(case, vertices, vertex=None):
    case=copy.deepcopy(case)
    if vertex is not None:
        pair=vertices[vertex]
        case['name']+='__sample_'+vertex
        case['parameters']['allocation_vertex']=vertex
        for row in case['loads']:
            if row['name']=='aggregate_electronics_adversarial':
                row.update(p=pair['p'],n=pair['n']);row.pop('pending_selection',None)
        for row in case['report_only_probes']:
            if row['name']=='CORE_actual_adversarial_sink':row.update(p=pair['p'],n=pair['n'])
    case.pop('execution_enabled',None)
    case['definition_review_notes']=case.pop('activation_blockers',[])
    return case

def check_cases(cases,networks):
    contacts={name:network['net']for network in networks for name in network['contacts']}
    names=set()
    for case in cases:
        if case['name']in names:raise Refused('Duplicate compiled case name')
        names.add(case['name'])
        nodes={'SOURCE_GND','BEC_POS','USB_SOURCE','DEV_U7_OUT','DEV_U8_OUT'}|set(contacts)
        for category in ['sources','resistors','loads','converters','probes','report_only_probes']:
            for row in case.get(category,[]):
                for key in ['p','n','in_p','in_n','out_p','out_n','sense_p','sense_n']:
                    if key in row:
                        if row[key]not in nodes:raise Refused('Unresolved compiled endpoint '+row['name'])
                        if row[key]in contacts and contacts[row[key]]not in case['nets']:
                            raise Refused('Case omits a referenced copper net')
        if any(r.get('ohm')is None or r['ohm']<=0 for r in case['resistors']):raise Refused('Unmeasured or nonpositive resistance')
        if any(x['current_A']<0 for x in case['loads']):raise Refused('Negative compiled load')
        electronics=sum(x['current_A']for x in case['loads']if x['name']=='aggregate_electronics_adversarial')
        dsm=sum(x['current_A']for x in case['loads']if x['name']=='DSM_external')
        if abs(electronics+dsm-case['parameters']['CORE_aggregate_A'])>1e-12:raise Refused('CORE current budget mismatch')
        if case.get('receiver_scope',case['scope'])=='capacity' and any(p['name']=='classic_DSM_pad'for p in case['probes']):
            raise Refused('Capacity case inherited a classic DSM guarantee')
        if case['supply']=='USB' and (dsm or any(x['name'].endswith('_servo_illustration')for x in case['loads'])):
            raise Refused('External loads in USB configuration case')
        if case['scope']=='same_BEC_illustrative':
            if len([s for s in case['sources']if s['voltage_V']!=0])!=1:
                raise Refused('Same-BEC case must have one external voltage source')
            if any(s['name']=='J6_return_reference'for s in case['sources']):
                raise Refused('Same-BEC case bypasses a finite return conductor')

def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()

def endpoint_cases(plan):
    make,_=case_factory(plan)
    vertices=plan['proposed_case_dimensions']['electronics_allocation_vertices']
    pairs=plan['proposed_case_dimensions']['ABC_port_pairs']
    cases=[]
    for scope in ['classic','capacity']:
        for pair in pairs:
            for vertex in vertices:
                c=materialize(make(scope,12.6,pair,vertex),vertices)
                c['extension_family']='loaded_12p6_endpoint';cases.append(c)
    for vin in [5.,12.6]:
        for pair in ['NONE',*pairs]:
            for vertex in vertices:
                c=materialize(make('classic',vin,pair,vertex,'upper_initial',dsm_override=0),vertices)
                c['scope']='classic_upper_unloaded_receiver'
                c['extension_family']='upper_output_endpoint'
                c['probes']=[p for p in c['probes']if p['name']!='classic_DSM_pad']+[
                    dict(name='unloaded_classic_DSM_upper',p='J12.1',n='J12.2',maximum_V=3.465)]
                # Every selected contact already exists in the archived operator.
                for ref in ['J9','J10','J11']:
                    c['report_only_probes'].append(dict(name=ref+'_pad_upper_report',p=ref+'.3',n=ref+'.4',
                        reason='Report loaded and unloaded pad maxima; no universal upper limit is assigned to unspecified external peripherals.'))
                cases.append(c)
    if len(cases)!=140:raise Refused('Changed endpoint dimensions require review')
    stamp_cases(cases);return cases

def solve_pair(case,packet):
    selected=set(case['nets']);runs=[]
    for grid in packet['grids']:
        blocks=[b for b in grid['ports']if b['net']in selected]
        if {b['net']for b in blocks}!=selected:raise Refused('Case uses an unbound network')
        r=solve_circuit(case,blocks)
        r.update(spacing_mm=grid['spacing_mm'],port_set_sha256=grid['port_set_sha256'],loaded_fields_recomputed=False)
        runs.append(r)
    if len(runs)!=2:raise Refused('Two grids required')
    a,b=runs;checks=[];reports=[];tol=packet['convergence']['absolute_voltage_V']
    for category,destination in [('probes',checks),('report_only_probes',reports)]:
        if [p['name']for p in a[category]]!=[p['name']for p in b[category]]:raise Refused('Probe identity mismatch')
        for pa,pb in zip(a[category],b[category]):
            delta=abs(pa['voltage_V']-pb['voltage_V']);guard=max(delta,tol)
            row={'probe':pb['name'],'fine_voltage_V':pb['voltage_V'],'change_V':delta,'numerical_guard_V':guard,'voltage_grid_pass':delta<=tol}
            if category=='probes':
                margin=min(pb['voltage_V']-pb.get('minimum_V',-math.inf),pb.get('maximum_V',math.inf)-pb['voltage_V'])
                row.update(margin_V=margin,guarded_margin_V=margin-guard,pass_=delta<=tol and margin>=guard)
                row['pass']=row.pop('pass_')
            else:
                row['acceptance_limit']=False
                if 'comparison_floor_V'in pb:row.update(comparison_floor_V=pb['comparison_floor_V'],guarded_comparison_headroom_V=pb['voltage_V']-pb['comparison_floor_V']-guard)
            destination.append(row)
    return {'case':case['name'],'case_definition_sha256':case['case_definition_sha256'],'runs':runs,
       'voltage_checks':checks,'report_only_grid_checks':reports,
       'port_voltage_checks_pass':all(x['pass']for x in checks),'voltage_grid_pass':all(x['voltage_grid_pass']for x in checks),
       'loaded_field_acceptance':None,'meaning':'Coupled-circuit voltages on verified two-grid impedances; new loaded fields have not been recovered.'}

def replay_archive(ledger,result,packet):
    largest=0.;count=0
    original={r['spacing_mm']:{c['case']:c for c in r['cases']}for r in result['runs']}
    for case in ledger['cases']:
        pair=solve_pair(case,packet)
        for row in pair['runs']:
            prior=original[row['spacing_mm']][case['name']]
            error=max(abs(value-prior['voltage_V'][node])for node,value in row['voltage_V'].items())
            largest=max(largest,error);count+=1
            if error>1e-10 or row['case_definition_sha256']!=prior['case_definition_sha256']:
                raise Refused('Archived circuit replay differs')
    return {'cases_per_grid':len(ledger['cases']),'circuit_replays':count,'maximum_node_voltage_difference_V':largest,
      'acceptance_absolute_V':1e-10,'passed':True,'new_loaded_field_solves':0}

def extrema(cases,results):
    defs={c['name']:c for c in cases};groups={}
    for item in results:
        case=defs[item['case']]
        for kind in ['voltage_checks','report_only_grid_checks']:
            for p in item[kind]:
                key=case.get('extension_family',case['scope'])+'/'+p['probe']
                groups.setdefault(key,[]).append({'case':case['name'],**p})
    return {key:{'minimum':min(rows,key=lambda r:r['fine_voltage_V']),'maximum':max(rows,key=lambda r:r['fine_voltage_V'])}for key,rows in groups.items()}

def resource_guard(seconds=300):
    if any(os.environ.get(k)!='1'for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS']):
        raise Refused('Set per-process OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1')
    resource.setrlimit(resource.RLIMIT_AS,(4096*1024**2,4096*1024**2))
    def expired(*_):raise Refused('Bounded circuit-only wall time exceeded')
    signal.signal(signal.SIGALRM,expired);signal.alarm(seconds)

LIMITS = [
    'Circuit voltages and currents on archived finite-contact two-grid port impedances only; no new loaded-field KCL, energy or current-density certificate.',
    'Original 62 required cases, five VCAP loops, numerical gates and failed overloaded illustration are unchanged; this does not extend their full-field acceptance.',
    'All efficiencies and effective resistances away from device test conditions are engineering assumptions, not manufacturer guarantees.',
    'TPS63070 PWM +/-1% reference bound already includes the stated IC-temperature/input table range; no additional arbitrary IC-temperature factor.',
    'Positive 100 nA leakage uses its stated VFB=0.8 V endpoint condition; negative 100 nA is an engineering sensitivity, not a signed TI guarantee.',
    'Divider TCR signs are independent with no assumed tracking. Resistor bodies at 105 C are a sensitivity; X5R capacitor bodies remain limited to 85 C.',
    'No continuous-input interpolation proof, transient, ripple, thermal, lifetime, assembly or flight qualification. Capacity DSM has no classic voltage-accuracy promise.',
]

def read(path):
    return json.loads(Path(path).read_text())

def ensure_generator_unchanged():
    if sha256(Path(__file__)) != LAUNCH_SOURCE_SHA256:
        raise Refused('Generator changed after launch; refuse mislabeled evidence')

def scenario(name, **kw):
    return dict(name=name, **kw)

def profiles():
    lower = [scenario(f'eta_u6_{a}_u9_{b}', eta6=a/100, eta9=b/100)
             for a in [75, 85, 95] for b in [75, 85, 95]]
    lower += [scenario('u8_120m', ron8=.12), scenario('u8_150m', ron8=.15),
              scenario('u7_50m', ron7=.05), scenario('u7_60m', ron7=.06),
              scenario('ifb_positive100n', ifb=1e-7), scenario('ifb_negative100n_assumed', ifb=-1e-7)]
    for key, dt in [('body85',60), ('interval_minus40_to85',65), ('body105_sensitivity',80)]:
        lower.append(scenario(key, delta_temperature=dt))
        lower.append(scenario('combined_'+key, delta_temperature=dt, eta6=.75, eta9=.75, ron8=.15, ifb=-1e-7))
    lower.append(scenario('combined_interval_u7_60m', delta_temperature=65, eta6=.75, eta9=.75, ron8=.15, ron7=.06, ifb=-1e-7))
    # Quiet-ground/sense motion makes efficiency effects non-monotone across
    # different constraints. Preserve every finite crossed pairing.
    for a in [75,85,95]:
        for b in [75,85,95]:
            if (a,b)==(75,75):continue
            lower += [scenario(f'combined_interval_eta{a}_{b}',delta_temperature=65,eta6=a/100,eta9=b/100,ron8=.15,ifb=-1e-7),
                      scenario(f'combined_interval_u7_60m_eta{a}_{b}',delta_temperature=65,eta6=a/100,eta9=b/100,ron8=.15,ron7=.06,ifb=-1e-7)]
    upper = [scenario('upper_'+key, high=True, delta_temperature=dt, ifb=1e-7)
             for key,dt in [('body85',60), ('interval_minus40_to85',65), ('body105_sensitivity',80)]]
    upper += [scenario('upper_combined_interval', high=True, delta_temperature=65, ifb=1e-7, eta6=.75, eta9=.75, ron8=.15)]
    upper += [scenario(f'upper_combined_interval_eta{a}_{b}',high=True,delta_temperature=65,ifb=1e-7,eta6=a/100,eta9=b/100,ron8=.15)
              for a in [75,85,95] for b in [75,85,95] if (a,b)!=(75,75)]
    usb = [scenario('usb_eta75', eta9=.75), scenario('usb_eta85', eta9=.85), scenario('usb_eta95', eta9=.95),
           scenario('usb_u8_120m',ron8=.12), scenario('usb_u8_150m',ron8=.15), scenario('usb_combined',eta9=.75,ron8=.15)]
    return lower, upper, usb

def apply_profile(original, profile):
    c = copy.deepcopy(original)
    name = profile['name']
    c['name'] += '__sensitivity_' + name
    c['extension_family'] = name
    c['sensitivity_definition'] = copy.deepcopy(profile)
    c['parameters']['independent_sensitivity_overrides'] = copy.deepcopy(profile)
    c['regulation_scope']['additional_output_error_fraction'] = None
    c['regulation_scope']['classification'] = 'Exact separate converter error controls are in sensitivity_definition; these are engineering sensitivities.'
    high = profile.get('high', False)
    if c['supply'] == 'BEC':
        dt = profile.get('delta_temperature', 0)
        sign = 1 if high else -1
        rt = 53600*(1+sign*.001)*(1+sign*25e-6*dt)
        rb = 10000*(1-sign*.001)*(1-sign*25e-6*dt)
        for r in c['resistors']:
            if r['name']=='R54_feedback_top': r['ohm']=rt
            if r['name']=='R55_feedback_bottom': r['ohm']=rb
        ifb = profile.get('ifb', 1e-7 if high else 0.)
        feedback = (.808 if high else .792) + ifb*(rt*rb/(rt+rb))
    for r in c['resistors']:
        if r['name'].startswith('U8_') and r['name'].endswith('_selected_path'):
            r['ohm'] = profile.get('ron8', .09)
        if r['name'].startswith('U7_') and r['name'].endswith('_selected_path'):
            r['ohm'] = profile.get('ron7', .033)
    for cv in c['converters']:
        if cv['name'].startswith('U6'):
            cv['efficiency']=profile.get('eta6',.85)
            cv['voltage_V']=feedback*(1+profile.get('error6',0))
        else:
            cv['efficiency']=profile.get('eta9',.85)
            cv['voltage_V']=(3.432 if high else 3.1845)*(1+profile.get('error9',0))
        if cv['quiescent_A'] != 0:
            raise Refused('Additive converter IQ would double count eta_total loss')
    c['assumptions'] += LIMITS
    stamp_cases([c])
    return c

def bases(plan, reference_ledger):
    make,_ = case_factory(plan)
    vertices = plan['proposed_case_dimensions']['electronics_allocation_vertices']
    lower = [materialize(make(scope, vin, pair, vertex), vertices)
             for scope in ['classic','capacity'] for vin in [5.,12.6]
             for pair in plan['proposed_case_dimensions']['ABC_port_pairs'] for vertex in vertices]
    upper = [c for c in endpoint_cases(plan) if c['extension_family']=='upper_output_endpoint']
    usb = [c for c in reference_ledger['cases'] if c['supply']=='USB']
    if (len(lower), len(upper), len(usb)) != (120, 80, 2):
        raise Refused('Changed required complete-vertex contexts')
    stamp_cases(lower)
    return lower,upper,usb

def compact_pair(case, packet):
    pair = solve_pair(case, packet)
    selected8 = 'U8.7' if case['supply']=='BEC' else 'U8.2'
    selected7 = 'U7.3' if case['supply']=='BEC' else 'U7.6'
    for run in pair['runs']:
        voltage=run['voltage_V']
        resistors={r['name']:r for r in run['resistors']}
        r8=next(r for r in run['resistors'] if r['name'].startswith('U8_') and r['name'].endswith('_selected_path'))
        r7=next(r for r in run['resistors'] if r['name'].startswith('U7_') and r['name'].endswith('_selected_path'))
        run['device_condition_screen'] = dict(
            U8_selected_input_relative_power_ground_V=voltage[selected8]-voltage['U8.12'],
            U8_selected_path_A=r8['current_A'],
            U8_row_requires_input_at_least_V=5., U8_row_test_current_A=.2,
            U8_at_exact_test_current=abs(r8['current_A']-.2)<1e-9,
            U7_selected_input_relative_ground_V=voltage[selected7]-voltage['U7.1'],
            U7_selected_path_A=r7['current_A'], U7_row_test_current_A=.2,
            U7_at_exact_test_current=abs(r7['current_A']-.2)<1e-9)
        if case['supply']=='USB':
            amps=resistors['U10_USB_limiter_path']['current_A']
            run['current_limit_screens']=dict(USB_limiter_path_A=amps, USB_reference_min_A=.3512,
                                              USB_reference_headroom_A=.3512-amps,
                                              guarantee=False, reason='Static screen against declared reference; no enumeration, startup or dynamic current-limit model.')
        else:
            conv={c['name']:c for c in run['converters']}
            c6=conv['U6_total_efficiency']; c9=conv['U9_total_efficiency']
            run['current_limit_screens']=dict(
                U5_selected_path_A=resistors['U5_efuse_path']['current_A'],
                U5_RON_test_current_A=3.,
                U6_output_A=c6['output_A'], U6_Vout_over_Vin=c6['output_V']/c6['input_V'],
                U6_2A_row_applicable_ratio=c6['output_V']<=c6['input_V'],
                U6_distance_to_2A_reference_A=2.-c6['output_A'],
                U9_output_A=c9['output_A'], U9_distance_to_1A_model_cap_A=1.-c9['output_A'],
                guarantee=False, reason='Reference conditions only; no U5 programmed current-limit or sustained U6 mild-boost guarantee established.')
        # All scalar circuit conservation evidence survives; per-node voltages
        # and port injections are retained only in archived/full endpoint files.
        del run['voltage_V']; del run['port_injections']
    pair['all_report_and_acceptance_grid_pass']=all(p['voltage_grid_pass'] for k in ['voltage_checks','report_only_grid_checks'] for p in pair[k])
    return pair

def profile_summary(cases, results):
    groups={}
    for c,r in zip(cases,results):
        name=c['extension_family']
        g=groups.setdefault(name,dict(cases=0, voltage_pass=True, all_grid_pass=True, minimum_guarded_margin_V=None,
                                      limiting_case=None, limiting_probe=None, failed_checks=[], minimum_USB_current_headroom_A=None))
        g['cases']+=1;g['voltage_pass'] &= r['port_voltage_checks_pass'];g['all_grid_pass'] &= r['all_report_and_acceptance_grid_pass']
        for p in r['voltage_checks']:
            if g['minimum_guarded_margin_V'] is None or p['guarded_margin_V']<g['minimum_guarded_margin_V']:
                g.update(minimum_guarded_margin_V=p['guarded_margin_V'],limiting_case=c['name'],limiting_probe=p['probe'])
            if not p['pass']:g['failed_checks'].append(dict(case=c['name'],**p))
        current=r['runs'][-1]['current_limit_screens'].get('USB_reference_headroom_A')
        if current is not None:g['minimum_USB_current_headroom_A']=min(current,g['minimum_USB_current_headroom_A'] if g['minimum_USB_current_headroom_A'] is not None else math.inf)
    return groups

def budget_margin(pair, target):
    checks=list(pair['voltage_checks'])
    rows=[dict(margin_V=p['guarded_margin_V'], probe=p['probe']) for p in checks]
    if target=='u8_accuracy':
        rows += [dict(margin_V=p['guarded_comparison_headroom_V'],probe=p['probe'])
                 for p in pair['report_only_grid_checks'] if 'guarded_comparison_headroom_V' in p]
    for kind in ['voltage_checks','report_only_grid_checks']:
        if any(not p['voltage_grid_pass'] for p in pair[kind]):
            rows.append(dict(margin_V=-1.,probe='voltage_grid_convergence'))
    return min(rows,key=lambda r:r['margin_V'])

def budget_profile(base_profile, target, value):
    p=copy.deepcopy(base_profile);p['name']+='__budget_'+target+'_'+format(value,'.12g')
    if target=='u7':p['ron7']=value
    elif target.startswith('u8'):p['ron8']=value
    elif target=='u6_error':p['error6']=-value
    elif target=='u9_error':p['error9']=-value
    elif target=='joint_error':p.update(error6=-value,error9=-value)
    elif target=='u9_upper_error':p['error9']=value
    else:raise Refused('Unknown budget target')
    return p

def allowance(cases, packet, base_profile, target):
    """Find a boundary, then rescreen EVERY allocation/context at safe endpoint.

    A bisection is a numerical scenario boundary, not proof of monotonicity or
    continuum qualification. Failed bracket evidence is preserved, never hidden.
    """
    start=.033 if target=='u7' else .09 if target.startswith('u8') else 0.
    if target.startswith('u8'):start=base_profile.get('ron8',start)
    upper=.15 if target=='u7' else 5. if target.startswith('u8') else .05
    step_tolerance=1e-7
    evaluations=0
    def evaluate(c,value):
        nonlocal evaluations
        held_profile={**c.get('sensitivity_definition',{}),**base_profile}
        definition=apply_profile(c,budget_profile(held_profile,target,value));evaluations+=1
        try:
            pair=compact_pair(definition,packet)
            return dict(case=c['name'],value=value,**budget_margin(pair,target),
                        definition_sha256=definition['case_definition_sha256'], result=pair)
        except Refused as err:
            if 'Bounded circuit-only wall time exceeded' in str(err):
                raise
            return dict(case=c['name'],value=value,margin_V=-math.inf,probe='model_refusal',refusal=str(err),
                        definition_sha256=definition['case_definition_sha256'])
    initial=[evaluate(c,start) for c in cases]
    worst=min(initial,key=lambda r:r['margin_V'])
    if worst['margin_V']<0:
        return dict(target=target,base_profile=base_profile,status='baseline already fails',limiting=finite_result(worst),evaluations=evaluations)
    lookup={c['name']:c for c in cases}
    high_scan=[evaluate(c,upper) for c in cases]
    high_worst=min(high_scan,key=lambda r:r['margin_V'])
    if high_worst['margin_V']>=0:
        raise Refused('No context brackets budget '+target+' in reviewed range')
    seed=lookup[high_worst['case']]; boundaries=[]
    # Each changed limiting context is retained; never label a seed-only screen
    # a complete-allocation allowance.
    for _ in range(len(cases)+1):
        lo=start;hi=upper;low_result=evaluate(seed,lo);high_result=evaluate(seed,hi)
        if high_result['margin_V']>=0:
            raise Refused('Budget was not bracketed; increase reviewed range')
        while hi-lo>step_tolerance:
            mid=(lo+hi)/2;result=evaluate(seed,mid)
            if result['margin_V']>=0:lo=mid;low_result=result
            else:hi=mid;high_result=result
        boundaries.append(dict(seed=seed['name'],safe_value=lo,failed_value=hi,
                               safe=finite_result(low_result),failed=finite_result(high_result)))
        verification=[evaluate(c,lo) for c in cases]
        worst=min(verification,key=lambda r:r['margin_V'])
        if worst['margin_V']>=0:
            boundary_reason=high_result['probe']
            physical_boundary=boundary_reason not in ['voltage_grid_convergence','model_refusal']
            return dict(target=target,base_profile=base_profile,status='bounded scenario allowance',
                        safe_value=lo,failed_value=hi,bracket_width=hi-lo,
                        boundary_reason=boundary_reason,boundary_case=high_result['case'],
                        physical_voltage_boundary_resolved=physical_boundary,
                        boundary_meaning=('Guarded voltage threshold bracket' if physical_boundary else
                                          'Numerical/model boundary; safe value is a checked lower bound, not a resolved physical resistance/error maximum'),
                        unit='ohm' if target in ['u7','u8_accuracy','u8_operating'] else 'fraction of modeled setpoint',
                        all_contexts_checked=len(cases),all_contexts_pass=True,
                        limiting=finite_result(worst),boundaries=boundaries,evaluations=evaluations,
                        full_context_safe_checks=[dict(case=r['case'],value=r['value'],margin_V=r['margin_V'],probe=r['probe'],
                                                      definition_sha256=r['definition_sha256'],
                                                      case_result_sha256=canonical(r['result'])) for r in verification],
                        qualification='Small-circuit numerical boundary with the existing grid guard; not a device maximum or monotonic/continuous-input proof.')
        seed=lookup[worst['case']];upper=hi
    raise Refused('Allocation ranking did not settle')

def finite_result(row):
    row=copy.deepcopy(row)
    if not math.isfinite(row['margin_V']):row['margin_V']=None
    return row
