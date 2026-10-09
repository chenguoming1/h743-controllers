#!/usr/bin/env python3
"""Compile explicit case definitions and immutable source evidence. Never solve."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
from copper_fem import Refused, contact_keys
from validate_static import read_json, sha256, preflight
from audit_native_ports import audit_ports
from power_case_model import case_factory


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


def build_cases(plan,settings):
    make_case,make_feed_case=case_factory(plan)
    vertices=plan['proposed_case_dimensions']['electronics_allocation_vertices']
    pairs=plan['proposed_case_dimensions']['ABC_port_pairs']
    baseline=[];upper=[];servo=[];deferred=[]
    for scope in ['classic','capacity']:
        contexts=[(v,pair)for v in plan['proposed_case_dimensions']['BEC_input_at_ideal_J6_pads_V']for pair in pairs]
        if settings['include_7p4V_electronics_baseline']:contexts.append((7.4,'BC'))
        for vin,pair in contexts:
            for vertex in vertices:baseline.append(materialize(make_case(scope,vin,pair,vertex),vertices))
            for profile in plan['engineering_sensitivity_profiles']:
                if profile not in ['baseline','upper_initial']:
                    deferred.append(dict(scope=scope,supply='BEC',vin=vin,pair=pair,profile=profile))
    for vin in plan['proposed_case_dimensions']['USB_source_sensitivity_V']:
        for vertex in vertices:baseline.append(materialize(make_case('usb_configuration',vin,'NONE',vertex,supply='USB'),vertices))
        for profile in ['eta75','eta95','u8_120m','u8_150m','auxiliary_added','regulation_1pct','regulation_2pct','coupled_adverse']:
            deferred.append(dict(scope='usb_configuration',supply='USB',vin=vin,pair='NONE',profile=profile))
    for pair in ['NONE',*pairs]:
        for vertex in vertices:
            case=make_case('classic',12.6,pair,vertex,'upper_initial',dsm_override=0)
            case['scope']='classic_upper_unloaded_receiver'
            case['probes']=[p for p in case['probes']if p['name']!='classic_DSM_pad']+[
                dict(name='unloaded_classic_DSM_upper',p='J12.1',n='J12.2',maximum_V=3.465)]
            upper.append(materialize(case,vertices))
    feeds=plan['same_BEC_illustrative_feed_profiles']
    definitions=[('moderate',feed,'classic')for feed in feeds]
    representative=['equal40m','paired_J8_weak','paired_J6_weak','crossed_J6_positive_strong',
                    'crossed_J8_positive_strong','J8_feed_lost','J6_feed_lost']
    for name in plan['servo_comparison_profiles']:
        if name!='moderate':
            definitions.extend((name,feed,'capacity')for feed in representative)
            definitions.append((name,'equal40m','classic'))
    for name,feed,scope in definitions:
        for vertex in settings['servo_sample_allocations']:
            if vertex not in vertices:raise Refused('Unknown fixed servo sample allocation')
            case=materialize(make_feed_case(name,feed,scope),vertices,vertex)
            case['assumptions'].append(settings['servo_sample_meaning'])
            case['allocation_basis']='fixed declared illustration; not selected from a numerical ranking'
            servo.append(case)
    return {'baseline':baseline,'upper':upper,'servo':servo},deferred


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


def compile_inputs(source,plan_path,registry_path,settings_path,out,allow_numerical=False):
    source=Path(source);out=Path(out)
    if out.exists():raise Refused('Compilation destination already exists; use a new isolated directory')
    plan=read_json(plan_path);registry=read_json(registry_path);settings=read_json(settings_path)
    if plan.get('schema')!='f722-static-case-plan-disabled/v1' or plan.get('execution_enabled')is not False:
        raise Refused('Expected the disabled review plan')
    if settings.get('scope')not in ['power-only','final-board']:raise Refused('Unknown compilation scope')
    source_files={'board':'f722-heli.kicad_pcb','geometry':'owner-native.json','parts':'parts.json',
      'parity':'owner-parity.json','process':'owner-process.json','mechanical':'owner-mechanical.json',
      'critical':'owner-critical.json','power_connectivity':'power-audit.json','drc_normal':'owner-drc.json',
      'drc_all_track':'owner-drc-all.json','ordinary_protection':'owner-protection.json','ordinary_supplemental':'owner-supplemental.json'}
    hashes={key:sha256(source/name)for key,name in source_files.items()}
    data={key:read_json(source/name)for key,name in source_files.items()if key!='board'}
    for key in ['geometry','parity','process','mechanical','critical','power_connectivity','ordinary_protection','ordinary_supplemental']:
        if data[key].get('board_sha256')!=hashes['board']:raise Refused('Stale source evidence: '+key)
    if any(data[key].get('passed')is not True for key in ['parity','process','mechanical'])or data['critical'].get('faults'):
        raise Refused('Source physical/parity gates are incomplete or failed')
    if not data['geometry'].get('source_unchanged'):raise Refused('Native exporter did not preserve the source')
    if data['process'].get('geometry_sha256')!=hashes['geometry']:
        raise Refused('Process receipt is not bound to the selected geometry export')
    networks={}
    native_pads={p['key']:p for p in data['geometry']['objects']if p['kind']=='pad'and p.get('number')}
    rebound=[]
    for name,spec in registry['contacts'].items():
        keys=contact_keys(spec)
        if any(k not in native_pads or native_pads[k]['net']!=spec['net']or spec['layer']not in native_pads[k]['copper']for k in keys):
            raise Refused('Native terminal identity/net/layer changed: '+name)
        networks.setdefault(spec['net'],{})[name]={'pads':keys,'layer':spec['layer']}
        rebound.append({'name':name,'pads':keys,'net':spec['net'],'layer':spec['layer'],
                        'native_pad_uuids':[native_pads[k]['uuid']for k in keys]})
    networks=[{'net':net,'contacts':contacts}for net,contacts in sorted(networks.items())]
    for ref,mpn in plan['current_selected_parts'].items():
        if ref.startswith('U')and data['parts'].get(ref,{}).get('mpn')!=mpn:raise Refused('Selected part changed: '+ref)
    # Exact resistor manufacturer identities establish the values used by the plan.
    for ref,mpn in {'R54':'RT0402BRD0753K6L','R55':'RT0402BRD0710KL','R16':'ERJ3RSFR12V'}.items():
        actual=data['parts'].get(ref,{}).get('mpn','')
        if actual!=mpn:raise Refused('Current-value part identity requires review: '+ref+' '+actual)
    critical={row['net']:row for row in data['critical']['fullnet_connectivity']}
    connectivity={'board_sha256':hashes['board'],'normalization':'Native UUID groups, supplemented by complete critical pad-key sets resolved against this exact export','nets':{}}
    for network in networks:
        net=network['net'];objects=[p for p in data['geometry']['objects']if p['kind']=='pad'and p.get('net')==net and p.get('number')]
        row=data['power_connectivity']['nets'].get(net)
        if row is None:
            proof=critical.get(net,{})
            if proof.get('complete')is not True or proof.get('unreached')or set(proof.get('pads',[]))!={p['key']for p in objects}:
                raise Refused('Missing native connectivity proof: '+net)
            row={'pad_group_count':1,'groups':[{'pad_uuids':[p['uuid']for p in objects]}],
                 'proof_source':'critical complete native pad-key set; keys mapped to frozen export UUIDs'}
        connectivity['nets'][net]=row
    excluded=[]
    for key in ['ordinary_protection','ordinary_supplemental']:
        for check in data[key]['checks']:
            if check.get('complete_clamp_first_path_passes')is not True:
                if settings['scope']=='final-board' or check['net']in {n['net']for n in networks}:
                    raise Refused('Relevant protection check failed: '+check['net'])
                excluded.append({'report':key,'id':check['id'],'net':check['net'],'reason':'Unfinished ordinary signal path outside this provisional DC power-only scope'})
    if excluded and not settings.get('preserve_failed_ordinary_protection_checks_as_out_of_scope'):
        raise Refused('Out-of-scope failed checks have no explicit compilation policy')
    families,deferred=build_cases(plan,settings)
    all_cases=[case for family in families.values()for case in family]
    check_cases(all_cases,networks)
    stamp_cases(all_cases)
    out.mkdir(parents=True);(out/'input').mkdir()
    for key,name in source_files.items():shutil.copyfile(source/name,out/'input'/name)
    for name,path in [('case-plan.json',plan_path),('terminal-registry.json',registry_path),('compiler-settings.json',settings_path)]:
        shutil.copyfile(path,out/'input'/name)
    save(out/'input/connectivity.json',connectivity)
    save(out/'input/physical.json',{'board_sha256':hashes['board'],'passed':True,
        'scope':'Process clearances, mechanical checks, critical faults; source reports retained',
        'input_hashes':{key:hashes[key]for key in ['process','mechanical','critical']},'excluded_ordinary_protection_checks':excluded})
    save(out/'input/rebound-terminals.json',{'board_sha256':hashes['board'],'contacts':rebound})
    files={key:{'path':'input/'+name,'sha256':sha256(out/'input'/name)}for key,name in source_files.items()}
    for key,name in [('connectivity','connectivity.json'),('physical','physical.json'),('case_plan','case-plan.json'),
                     ('terminal_registry','terminal-registry.json'),('compiler_settings','compiler-settings.json'),('rebound_terminals','rebound-terminals.json')]:
        files[key]={'path':'input/'+name,'sha256':sha256(out/'input'/name)}
    manifest={'schema':'f722-scoped-static-freeze/v1','status':'frozen-for-scoped-static-screen','scope':settings['scope'],
       'source_stage':settings['source_stage'],'saved_fill_verified':True,'checks_run_on_frozen_board':True,
       'tested_nets':[n['net']for n in networks],'files':files,'numerical_execution_authorized':allow_numerical,
       'qualification':'Provisional source-bound power review; final ordinary routing requires fresh source/check binding',
       'excluded_ordinary_protection_checks':excluded,
       'compiler_source_sha256':{n:sha256(Path(__file__).parent/n)for n in ['compile_power_ledger.py','power_case_model.py']}}
    manifest['analysis_source_sha256']={n:sha256(Path(__file__).parent/n)for n in ['copper_fem.py','dc_circuit.py','validate_static.py','audit_native_ports.py']}
    save(out/'freeze.json',manifest)
    common={'schema':'f722-static-ledger/v1','status':'ready','freeze_manifest_sha256':sha256(out/'freeze.json'),
       'source_stage':settings['source_stage'],'material':settings['material'],'mesh_spacings_mm':settings['mesh_spacings_mm'],
       'convergence':settings['convergence'],'limits':settings['limits'],'networks':networks,'unit_transfers':[],
       'loops':plan['VCAP_copper_loops'],'assumption_record_sha256':files['case_plan']['sha256']}
    common['definition_source_sha256']={'case_plan':files['case_plan']['sha256'],'terminal_registry':files['terminal_registry']['sha256'],
        'settings':files['compiler_settings']['sha256'],'case_model':manifest['compiler_source_sha256']['power_case_model.py']}
    receipts={}
    for name,cases in {**families,'primary':all_cases}.items():
        save(out/('ledger-'+name+'.json'),{**common,'case_family':name,'cases':cases})
        context=preflight(out/'freeze.json',out/('ledger-'+name+'.json'))
        receipts[name]={'case_count':len(cases),'ledger_sha256':context['ledger_sha256'],'preflight_passed':True}
    save(out/'deferred-case-plan.json',{'status':'DEFERRED; NO REAL BASELINE RANKINGS','execution_enabled':False,
       'baseline_ledger_sha256':receipts['baseline']['ledger_sha256'],'freeze_sha256':sha256(out/'freeze.json'),
       'slices':deferred,'upper_additional_errors':[.01,.02],
       'rule':'Materialize only from validated, source-bound baseline numerical results. No arbitrary weakest allocation is selected.'})
    port_receipt=audit_ports(out/'input'/source_files['board'],out/'input'/source_files['geometry'],
                             out/'ledger-primary.json',out/'input/connectivity.json',out/'input'/source_files['critical'])
    if not port_receipt['passed']:raise Refused('Compiled native port audit failed')
    save(out/'port-audit.json',port_receipt)
    if hashes!={key:sha256(source/name)for key,name in source_files.items()}:
        raise Refused('Source evidence changed during compilation')
    receipt={'status':'COMPILED AND PREFLIGHTED; NO FEM OR CIRCUIT RUN','board_sha256':hashes['board'],
      'freeze_sha256':sha256(out/'freeze.json'),'numerical_execution_authorized':allow_numerical,
      'families':receipts,'deferred_slices':len(deferred),'finite_contacts':port_receipt['contact_count'],
      'deferred_case_plan_sha256':sha256(out/'deferred-case-plan.json'),
      'loops':len(port_receipt['loops']),'measured_harness_templates_included':False,
      'excluded_ordinary_protection_checks':excluded}
    save(out/'compile-receipt.json',receipt)
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['source','plan','registry','settings','out']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--allow-numerical',action='store_true',help='Use only after the owner releases the numerical compute slot for this source')
    a=p.parse_args()
    r=compile_inputs(a.source,a.plan,a.registry,a.settings,a.out,a.allow_numerical)
    print(json.dumps({k:r[k]for k in ['status','board_sha256','families','deferred_slices','finite_contacts','loops']}))


if __name__=='__main__':main()
