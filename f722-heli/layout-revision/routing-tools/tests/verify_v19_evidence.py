#!/usr/bin/env python3
"""Portable V19 recovery and source-bound receipt checks; standard library only.

Does not replay KiCad pose operations, native copper geometry, DRC, reference
classification, placement rebuilding, the JVM router, refill, or numerical power.
"""
import argparse, ast, contextlib, io, runpy, copy, hashlib, importlib.util, json, math, re, sys, tempfile, types, uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_bytes())
def module(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base-project', type=Path, required=True)
    ap.add_argument('--historical-workspace', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    raw = module('v19_raw', ROOT/'tests/checkpoint49/materialize.py'); e = raw.Evidence()
    index = e.index['files']; excluded = e.index['excluded_files']; recovered = e.index['recovered_files']
    identity = read(ROOT/'checks/v19-source-identity.json')
    recovery = module('v19_recovery', ROOT/'sessions/recovery-v19/rebuild_historical_source.py')
    packet = ROOT/'sessions/recovery-v19'; manifest = read(packet/'paired-files.json')
    negatives = []
    def reject(name, operation):
        try: operation()
        except (AssertionError, ValueError, KeyError, FileNotFoundError): negatives.append(name)
        else: raise AssertionError('Invalid evidence accepted: '+name)
    def original(name): return (index.get(name) or excluded.get(name) or recovered[name])['sha256']
    for name in index: e.verify(name)
    for name in excluded: reject('excluded input unavailable '+name, lambda name=name: e.bytes(name))
    if a.historical_workspace:
        for name, row in {**index, **excluded, **recovered}.items():
            assert sha(a.historical_workspace/name) == row['sha256'], name
    projects = []
    with tempfile.TemporaryDirectory(prefix='v19-evidence-') as t:
        tmp = Path(t)
        for label in manifest['sources']:
            outputs = recovery.prepare_project(a.base_project, label, packet)
            for name, data in outputs.items():
                p = tmp/'ordinary-routing'/label/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
            projects.append({'source':label, 'paired_files':len(outputs), 'board_sha256':sha(tmp/'ordinary-routing'/label/'f722-heli.kicad_pcb')})
        for name in index: e.put(name, tmp)
        for name, row in recovered.items(): assert sha(tmp/name) == row['sha256'], name
        j = lambda name: read(tmp/name)
        c = 'ordinary-routing/candidate49/'; old = 'ordinary-routing/candidate48/'; review = 'checkpoint29-review/'
        board = original(c+'f722-heli.kicad_pcb'); source = original(old+'f722-heli.kicad_pcb')
        assert identity['expected_boards'] == {'candidate48':source, 'candidate49':board}
        handoff = j(c+'route-handoff.json'); adopt = j(c+'owner-adoption.json'); native = j(c+'owner-summary.json')
        provenance = j(c+'construction-provenance.json'); imp = j(c+'f722-heli.import.json')
        assert original(c+'route-handoff.json') == identity['sealed_handoff']['sha256']
        for name, digest in handoff['files'].items(): assert original(c+name) == digest, name
        extension=j(c+'owner-receipt-extensions.json');assert extension['board_sha256']==board and original(c+'owner-receipt-extensions.json')==identity['owner_extensions']['sha256']
        for name,digest in extension['files'].items(): assert original(c+name)==digest
        assert len(handoff['files'])==identity['sealed_worker_files']==138
        assert handoff['board_sha256'] == adopt['board_sha256'] == native['board_sha256'] == provenance['board_sha256'] == board
        assert handoff['integration_source_sha256'] == provenance['source_board_sha256'] == source
        assert handoff['owner_adoption_pending'] is True and adopt['native_unfinished_connections'] == 29
        assert adopt['native_errors'] == adopt['native_warnings'] == 0 and not adopt['numerical_applicability']
        assert native['drc'] == native['drc-all'] == {'unconnected':29, 'errors':0, 'warnings':0}
        assert not j(c+'owner-drc-parity.json')['schematic_parity'] and not j(c+'owner-drc-parity.json')['violations']
        assert not any(row['violations'] for row in j(c+'owner-erc.json')['sheets'])
        for section in ['process','mechanical','parity','firmware']:
            assert native[section]['passed'] and native[section]['board_sha256'] == board
        assert native['critical']['connected_nets'] == native['critical']['total_nets'] == 16
        assert not native['critical']['faults'] and not native['critical']['missing_ground_returns']
        for field, path in [('native_gate_receipt_sha256',c+'owner-summary.json'),('integration_receipt_sha256',review+'owner-coordinated-integration.json'),('reference_comparison_sha256',review+'comparison-30-to-29.json'),('actual_io_receipt_sha256',c+'protection-actual-io.json')]:
            assert adopt[field] == original(path)
        owner = j(review+'owner-review-run.json')
        assert owner['board_sha256'] == board and owner['previous_board_sha256'] == source and owner['native_count'] == 29 and owner['sealed_native_receipts_verified']
        assert {row['command']:row['exit_code'] for row in owner['commands']} == {'coordinated':0,'reference':0,'i2c':2,'actual-io22':1,'spi':0}
        assert provenance['constructor_sha256'] == original(c+'construct_mcu.used.py') == original('ordinary-routing/tests/port-a48/construct_mcu.py')
        assert provenance['source_native_sha256'] == original(old+'f722-heli.native.json') and provenance['source_map_sha256'] == original(old+'f722-heli.logical-route-map.json')
        assert provenance['proposal_sha256'] == original(c+'proposal.json') == original('ordinary-routing/tests/port-a48/proposal.json')
        assert imp['passed'] and imp['source_sha256'] == source and imp['output_sha256'] == board
        for flag in ['direct_engine_output','engine_routing_succeeded','fresh_model_zero_control_performed','numerical_power_VCAP_applicable']: assert imp[flag] is False
        # Extract the original parser's pure definitions. No pcbnew import or native pose operation.
        parser_path = tmp/'ordinary-routing/tests/mpn-parity/apply_metadata_copy.py'
        tree = ast.parse(parser_path.read_text()); wanted = {'Atom','Node','parse','children','child','value','properties','shape'}
        nodes = [n for n in tree.body if (isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in wanted) or (isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='TOKEN' for x in n.targets))]
        parser = types.ModuleType('v19_parser'); parser.__dict__.update(re=re,json=json)
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(parser_path),'exec'),parser.__dict__)
        before = parser.parse((tmp/old/'f722-heli.kicad_pcb').read_text()); after = parser.parse((tmp/c/'f722-heli.kicad_pcb').read_text())
        keyed = lambda root,kind: {parser.value(n,'uuid'):n for n in parser.children(root,kind)}
        point = lambda node,key: [float(x.value) for x in parser.child(node,key).items[1:]]
        integration = j(c+'native-coordinated-integration.json'); assert integration == j(review+'owner-coordinated-integration.json')
        assert integration['source_board_sha256'] == source and integration['board_sha256'] == board and integration['passed']
        oldobjects = {u:n for k in ['segment','via','arc'] for u,n in keyed(before,k).items()}
        newobjects = {u:n for k in ['segment','via','arc'] for u,n in keyed(after,k).items()}
        added = set(newobjects)-set(oldobjects); removed = set(oldobjects)-set(newobjects)
        assert len(added) == 21 and len(removed) == 6 and not integration['changed_objects']
        assert all(oldobjects[u].items[0].value=='segment' for u in removed)
        assert provenance['all_other_source_native_objects_exact_except_net_code']==len(oldobjects)+558==1981
        assert len(oldobjects)-len(removed)+558==1975
        assert all(parser.shape(oldobjects[u]) == parser.shape(newobjects[u]) for u in set(oldobjects)&set(newobjects))
        assert integration['retained_track_via_arc_objects'] == len(set(oldobjects)&set(newobjects)) == 1417
        for field, objects in [('added_objects',newobjects),('removed_objects',oldobjects)]:
            assert {r['uuid'] for r in integration[field]} == (added if field=='added_objects' else removed)
            for row in integration[field]: assert row['after' if field=='added_objects' else 'before'] == parser.shape(objects[row['uuid']])
        assert added == {r['uuid'] for r in provenance['added_records']} and removed == {r['uuid'] for r in provenance['removed_source_records']}
        proposal = j(c+'proposal.json'); expected_ids = set(); route_ids = []
        for ri, route in enumerate(proposal['routes']):
            ids = []
            for i,(start,end) in enumerate(zip(route['points'],route['points'][1:])):
                uid = str(uuid.uuid5(uuid.NAMESPACE_URL,source+'/port-a48/'+original(c+'proposal.json')+'/route/'+str(ri)+'/'+str(i)))
                expected_ids.add(uid); ids.append(uid); node = newobjects[uid]
                assert node.items[0].value == 'segment' and parser.value(node,'net') == route['net'] and parser.value(node,'layer') == route['layer']
                assert float(parser.value(node,'width')) == route['width'] and point(node,'start') == start and point(node,'end') == end
            route_ids.append(ids)
        via_ids = []
        for i,via in enumerate(proposal['vias']):
            xy=via['xy']
            uid = str(uuid.uuid5(uuid.NAMESPACE_URL,source+'/port-a48/'+original(c+'proposal.json')+'/via/'+str(i)))
            expected_ids.add(uid); via_ids.append(uid); node = newobjects[uid]
            assert node.items[0].value == 'via' and parser.value(node,'net') == via['net'] and point(node,'at') == xy
            assert float(parser.value(node,'size')) == .45 and float(parser.value(node,'drill')) == .2
        assert expected_ids == added and route_ids == provenance['routes'] and via_ids == provenance['vias']
        assert removed == set(proposal['removed_source_ids']) and provenance['all_156_footprints_exact']
        # Full unchanged footprint/pad structure can be compared without native pose replay.
        oldfps,newfps = keyed(before,'footprint'),keyed(after,'footprint')
        assert set(oldfps)==set(newfps) and len(newfps)==156
        assert all(parser.shape(oldfps[u])==parser.shape(newfps[u]) for u in oldfps)
        assert sum(len(parser.children(fp,'pad')) for fp in newfps.values())==558
        assert integration['retained_footprints']==156 and not provenance['changed_pad_records'] and not provenance['changed_footprint_records']
        declaration=j(c+'declared-footprint-transforms.json');assert declaration['source_board_sha256']==source and declaration['board_sha256']==board and not declaration['changes']
        poses=j(c+'poses-native.json');assert len(poses)==156 and poses==j(old+'poses-native.json')
        for fp in newfps.values():
            ref=parser.properties(fp)['Reference'].items[2].value;at=point(fp,'at')
            assert at[:2]+[(at[2] if len(at)>2 else 0)%360,parser.value(fp,'layer')]==[*poses[ref][:2],poses[ref][2]%360,poses[ref][3]]
        # Run the original owner parser integration unchanged, with its original pure parser definitions.
        prior_module=sys.modules.get('apply_metadata_copy');sys.modules['apply_metadata_copy']=parser
        path=tmp/'integrated-routing/check_coordinated_integration.py';out=tmp/'owner-parser.json';argv=sys.argv
        sys.argv=[str(path),str(tmp/old/'f722-heli.kicad_pcb'),str(tmp/c/'f722-heli.kicad_pcb'),'--out',str(out),'--net','PORT_A_TX_MCU','--net','PORT_A_RX_MCU','--net','ADC_BUS']
        try:
            with contextlib.redirect_stdout(io.StringIO()):runpy.run_path(str(path),run_name='__main__')
        finally:
            sys.argv=argv
            if prior_module is None:sys.modules.pop('apply_metadata_copy',None)
            else:sys.modules['apply_metadata_copy']=prior_module
        assert read(out)==integration
        def config(z): return [parser.shape(x) if isinstance(x,parser.Node) else x.value for x in z.items if not(isinstance(x,parser.Node) and x.items[0].value in ['filled_polygon','fill_segments'])]
        oldzones,newzones = keyed(before,'zone'),keyed(after,'zone'); assert set(oldzones)==set(newzones) and len(newzones)==3
        assert all(config(oldzones[u])==config(newzones[u]) for u in oldzones)
        ignored = {'footprint','segment','via','arc','zone'}
        rest = lambda root: [parser.shape(x) if isinstance(x,parser.Node) else x.value for x in root.items if not(isinstance(x,parser.Node) and x.items[0].value in ignored)]
        assert rest(before)==rest(after)
        oldmap = j(old+'f722-heli.logical-route-map.json')['logical_route_map']
        expected_map = {u:n for u,n in oldmap.items() if u not in removed}
        expected_map.update({u:parser.value(newobjects[u],'net') for u in added})
        assert expected_map == j(c+'f722-heli.logical-route-map.json')['logical_route_map']
        assert set(j(c+'fixed-explicit-native-ids.json')) == (set(j(old+'fixed-explicit-native-ids.json'))-removed)|added
        for row in j(c+'project-input-preservation.json')['files']: assert sha(tmp/c/row['path']) == sha(tmp/old/row['path']) == row['sha256']
        audit = j(c+'entry-support-audit.json'); wrapper = j(c+'power-audit.json'); prior = j(old+'power-audit.json')
        def bind(w):
            assert w['schema']=='f722-native-support-audit/v1' and w['passed'] is audit['passed'] is True
            assert w['board_sha256']==audit['board_sha256']==board and w['source_board_sha256']==audit['source_board_sha256']==source
            assert w['native_sha256']==audit['native_sha256']==original(c+'f722-heli.native.json') and w['source_native_sha256']==audit['source_native_sha256']==original(old+'f722-heli.native.json')
            assert w['audit_sha256']==original(c+'entry-support-audit.json') and w['source_audit_sha256']==original(old+'power-audit.json')
            assert w['audit_source_sha256']==original(c+'audit_mcu.used.py')==original('ordinary-routing/tests/port-a48/audit_mcu.py')
            assert not w['numerical_power_VCAP_applicable'] and not audit['numerical_power_VCAP_applicable']
            assert w['nets']==audit['nets'] and len(w['nets'])==28 and len(audit['gates'])==6 and all(v is True for v in audit['gates'].values())
            for n,row in w['nets'].items():
                assert row['complete'] and row['pad_group_count']==1 and row['groups']==prior['nets'][n]['groups'] and row['source_groups_exactly_preserved']
        bind(wrapper)
        for key,value in [('board_sha256','0'*64),('source_board_sha256','0'*64),('audit_sha256','0'*64),('source_audit_sha256','0'*64),('native_sha256','0'*64),('numerical_power_VCAP_applicable',True)]:
            bad=copy.deepcopy(wrapper);bad[key]=value;reject('support binding '+key,lambda bad=bad:bind(bad))
        support=module('v19_support',tmp/'integrated-routing/verify_support_adoption.py')
        compat=support.verify(wrapper,prior,source,board,tmp/c)
        assert compat=={'passed':True,'nets':28,'typed_audit_binding_checked':False}
        saved=j(c+'support-wrapper-compatibility.json')
        assert saved['support_wrapper_sha256']==original(c+'power-audit.json') and saved['verifier_sha256']==original('integrated-routing/verify_support_adoption.py') and all(saved[k]==v for k,v in compat.items())
        assert len(audit['strict_pad_entries'])==5 and all(r['passed'] for r in audit['strict_pad_entries'])
        assert len(audit['full_width_joins'])==29 and all(r['passed'] for r in audit['full_width_joins'])
        assert len(audit['finite_actual_annular_entries'])==5 and all(r['passed'] for r in audit['finite_actual_annular_entries'])
        assert audit['new_track_endpoints_checked']==len(audit['endpoint_inventory'])==38 and all(r['connections'] for r in audit['endpoint_inventory'])
        assert not audit['partial_pad_entries_not_used_as_connectivity_proof']
        assert len(audit['PORT_A_TX_MCU_before'])==2 and len(audit['PORT_A_TX_MCU_after'])==1
        assert audit['PORT_A_TX_MCU_after'][0]['pads']==['R31.2','U1.15']
        assert set(audit['changed_groups'])=={'PORT_A_TX_MCU','PORT_A_RX_MCU','ADC_BUS'} and all(len(r['after'])==1 for r in audit['changed_groups'].values())
        for n in ['PORT_A_RX_MCU','ADC_BUS']:assert audit['changed_groups'][n]['before']==audit['changed_groups'][n]['after']
        assert all(r['before']==r['after'] for r in audit['retained_groups'].values())
        assert len(audit['negative_controls'])==6 and all(r['rejected'] for r in audit['negative_controls'])
        transaction=j(c+'coordinated-change-receipt.json')
        assert transaction['added_objects']==provenance['added_records'] and transaction['removed_source_objects']==provenance['removed_source_records']
        assert transaction['source_board_sha256']==source and transaction['board_sha256']==board
        assert imp['coordinated_change_receipt_sha256']==original(c+'coordinated-change-receipt.json') and imp['construction_provenance_sha256']==original(c+'construction-provenance.json')
        assert imp['logical_route_map_sha256']==original(c+'f722-heli.logical-route-map.json')
        assert transaction['all156_full_footprint_records_exact'] and transaction['all558_full_pad_records_exact'] and transaction['all_existing_vias_exact'] and transaction['no_peer_proposal_adopted']
        actual=j(c+'protection-actual-io.json');assert actual==j(review+'actual-io22.json') and actual['board_sha256']==board and actual['geometry_sha256']==original(c+'f722-heli.native.json') and actual['source_unchanged']
        assert (actual['passed'],actual['total'],actual['all_pass'])==(13,22,False)
        assert len({(r['net'],r['clamp']) for r in actual['checks'] if r['complete_clamp_first_path_passes']})==11
        comparison=j(c+'reference-comparison48.json');assert comparison==j(review+'comparison-30-to-29.json') and comparison['before_board_sha256']==source and comparison['after_board_sha256']==board
        assert comparison['critical_object_geometry_identical'] and not comparison['critical_object_differences']
        assert all(v==0 for row in comparison['net_numeric_deltas_after_minus_before'].values() for v in row.values())
        def classifier(row):
            assert row['before_board_sha256']==source and row['after_board_sha256']==board and row['source_binding_verified']
            assert row['critical_copper_identical'] and row['unchanged_critical_own_via_windows_verified']
            assert row['missing_centerline_geometries_exactly_equal'] is True
            assert row['all_changed_critical_projection_geometry_inside_unchanged_own_windows'] is True
            assert row['all_changed_critical_projection_geometry_inside_actual_hole_window_intersections'] is True
            assert row['exact_containment_predicate_disagreement_count']==0 and row['classification_status']=='CONTAINED_REFERENCE_REGION_ONLY' and not row['changed_critical_regions']
            assert row['numeric_differences_retained']==comparison['net_numeric_deltas_after_minus_before']
            for name,digest in row['source_hashes'].items(): assert original(name)==digest, name
        ownerclass=j(c+'reference-region-review/reference-classification.json');classifier(ownerclass)
        assert handoff['reference_window_classification_sha256']==original(c+'reference-region-review/reference-classification.json')
        for key,value in [('before_board_sha256','0'*64),('missing_centerline_geometries_exactly_equal',False),('exact_containment_predicate_disagreement_count',2),('all_changed_critical_projection_geometry_inside_actual_hole_window_intersections',False)]:
            bad=copy.deepcopy(ownerclass);bad[key]=value;reject('classifier '+key,lambda bad=bad:classifier(bad))
        assert len(ownerclass['rejection_controls'])==6 and all(r['rejected'] for r in ownerclass['rejection_controls'])
        reference=j(c+'new-route-reference-review.json')
        def route_reference(r):
            assert r['board_sha256']==board and r['source_board_sha256']==source and r['native_sha256']==original(c+'f722-heli.native.json')
            assert r['all_full_footprints_exact']==156 and r['all_full_pad_records_exact']==558
            assert r['all_new_or_changed_tracks_reference_complete_outside_explicit_own_via_windows']
            current={x['uuid']:x for x in r['tracks']}
            for uid in added:
                if newobjects[uid].items[0].value=='segment':
                    z=current[uid];assert z['outside_centerline_empty'] and z['outside_width_empty'] and z['centerline_outside_own_via_windows_mm']==z['width_outside_own_via_windows_mm2']==0
            for net in ['PORT_A_TX_MCU','PORT_A_RX_MCU']:assert r['summary'][net]['all_reference_outside_own_windows_empty']
            assert r['summary']['ADC_BUS']['all_reference_outside_own_windows_empty'] is False
            gaps=r['unchanged_ADC_source_width_gaps'];assert len(gaps)==2 and all(z['exact_geometry_equal'] and z['source_width_gap_mm2']==z['candidate_width_gap_mm2'] and z['candidate_width_gap_mm2']>0 for z in gaps)
            assert sum(z['candidate_width_gap_mm2'] for z in gaps)==r['source_ADC_existing_gap_total_mm2']==6.086481252560899e-05
            assert r['AC_signal_integrity_or_EMC_qualification'] is False and r['numerical_power_qualification'] is False
        route_reference(reference)
        for key,value in [('board_sha256','0'*64),('AC_signal_integrity_or_EMC_qualification',True),('source_ADC_existing_gap_total_mm2',0)]:
            bad=copy.deepcopy(reference);bad[key]=value;reject('new route reference '+key,lambda bad=bad:route_reference(bad))
        for net in ['PORT_A_TX_MCU','PORT_A_RX_MCU','ADC_BUS']:
            measured=sum(math.dist(point(n,'start'),point(n,'end')) for n in newobjects.values() if n.items[0].value=='segment' and parser.value(n,'net')==net)
            assert math.isclose(measured,reference['summary'][net]['total_track_length_mm'],rel_tol=1e-14)
        access=j(c+'remaining-access.json');assert access['source_board_sha256']==source and access['board_sha256']==board and access['passed'] and len(access['pads'])==17 and not access['newly_sealed_unresolved_pad_via_access'] and access['reserved_RPM_portal_mm']==[15.1,9.59]
        electrical=j(c+'adc-electrical-screen.json');adc=electrical['stock_adc'];topology=electrical['topology']
        for name,digest in electrical['sources'].items(): assert original(name)==digest
        assert electrical['board_sha256']==board and electrical['source_board_sha256']==source and electrical['native_sha256']==original(c+'f722-heli.native.json')
        def acquisition(row):
            assert row['resolution_bits']==12 and row['sample_cycles']==480 and row['assumed_stock_HCLK_Hz']==216000000
            assert row['fADC_Hz']==row['assumed_stock_HCLK_Hz']/row['verified_APB2_divisor']/row['verified_ADC_PCLK_divisor']==13500000
            assert row['sample_seconds']==row['sample_cycles']/row['fADC_Hz']
            settle=(topology['Rth_resistor_tolerance_upper_ohm']+row['datasheet_table67_RADC_max_ohm']+2)*row['datasheet_table67_CADC_max_F']*math.log(4*2**row['resolution_bits'])
            assert math.isclose(settle,row['quarter_LSB_settle_required_seconds_Rth_plus_RADC_plus_2ohm'],rel_tol=1e-14)
            assert row['sample_seconds']>settle and row['guaranteed_C31_effective_capacitance_floor_claimed'] is False
        acquisition(adc)
        for key,value in [('sample_cycles',1),('guaranteed_C31_effective_capacitance_floor_claimed',True)]:
            bad=copy.deepcopy(adc);bad[key]=value;reject('conditional ADC '+key,lambda bad=bad:acquisition(bad))
        assert topology['capacitor_branch_mm']==4.448361439424413 and topology['capacitor_to_U1_pad_path_mm']==6.9633624394244125 and topology['new_ground_lead_mm']==1.3792455908938046
        assert topology['C31_interval_excludes_DC_bias_temperature_and_aging'] is True
        fragments=[r for r in electrical['exact_saved_reference_projection'] if not r['outside_width_empty']]
        assert len(fragments)==2 and all(r['outside_centerline_empty'] for r in electrical['exact_saved_reference_projection'])
        assert sorted(r['outside_explicit_own_via_windows_width_mm2'] for r in fragments)==[1.2930920115704463e-05,4.793389240990453e-05]
        assert electrical['all_reference_projection_outside_explicit_own_via_windows_empty'] is False and electrical['functional_qualification'] is False and electrical['numerical_power_VCAP_applicable'] is False
        prior_adc=j(old+'adc-electrical-screen.json')
        old_fragments=[r for r in prior_adc['exact_saved_reference_projection'] if not r['outside_width_empty']]
        assert old_fragments==fragments
        assert j(c+'i2c-geometry-review.json')['I2C_final_status']=='NOT_QUALIFIED' and j(c+'stock-spi-binding.json')['passed']
        assert not j(c+'power-revalidation-required.json')['numerical_power_and_VCAP_applicability']
        for name,row in identity['frozen_helpers'].items(): assert original(name)==row['sha256']
        data=(a.base_project/'f722-heli.kicad_pcb').read_bytes();delta=read(packet/'candidate49.f722-heli.kicad_pcb.delta.json')
        for name,bb,dd in [('wrong base',data+b'\n',delta),('wrong target',data,dict(delta,target_sha256='0'*64)),('invalid range',data,dict(delta,operations=[[0,len(data)+1]])),('invalid operation',data,dict(delta,operations=[{}]))]: reject('recovery '+name,lambda bb=bb,dd=dd:recovery.reconstruct(bb,dd))
        for name in ['../escape','/absolute','safe/../escape','windows\\escape']: reject('unsafe path '+name,lambda name=name:raw.safe(name))
    status=read(ROOT/'status.json')
    assert status['native_open_connections']==29 and status['actual_io_cases_passed']==13 and status['actual_io_channels_passed']==11 and not status['numerical_power_and_VCAP_applicability'] and not status['fabrication_ready']
    result={'passed':True,'scope':'Exact paired48/49 recovery; selected/sealed dependency hashes and separate owner extensions; full unchanged footprint/pad and copper/zone parser comparisons; deterministic UUID/path construction; original owner pure-parser integration and support adapter replay; conditional ADC arithmetic. Native geometry/DRC/refill/reference/cut/access/power results are preserved, not rerun.',
      'verifier_source_sha256':sha(__file__),'recovered_projects':projects,'raw_files_verified':len(index),'excluded_raw_files':len(excluded),'negative_controls_passed':len(negatives),'negative_controls':negatives,'original_source_hash_checks_performed':bool(a.historical_workspace),
      'sealed_worker_files_verified':138,'owner_extension_files_verified':len(extension['files']),'parsed_total_footprints':156,'parsed_total_pads':558,'exact_unchanged_footprint_structures':156,'deterministic_constructor_geometry_checked':True,'owner_pure_parser_integration_reexecuted':True,'actual_owner_support_adapter_reexecuted':True,'full_entry_binding_separately_verified':True,
      'added_tracks':19,'added_vias':2,'removed_tracks':6,'source_native_object_count':1981,'retained_native_object_count':1975,'preserved_finite_controls':6,'preserved_classifier_binding_controls':6,'native_pose_prediction_reexecuted':False,'native_placement_reproduction_reexecuted':False,'full_finite_geometry_audit_reexecuted':False,'native_DRC_reexecuted':False,'real_reference_classifier_reexecuted':False,'native_replay_inputs_complete':False,'JVM_router_refill_or_power_solve_executed':False,
      'conditional_ADC_arithmetic_reexecuted':True,'ADC_outside_window_width_fragments':fragments,'ADC_total_outside_window_width_mm2':sum(r['outside_explicit_own_via_windows_width_mm2'] for r in fragments),'ADC_functional_qualification':False,'new_changed_tracks_outside_own_windows_reference_complete':True,'critical_numeric_deltas_exactly_zero':True,'incremental_actual_hole_predicate_disagreements':0,'historical_ADC_false_width_predicate_preserved':True,
      'numerical_power_and_VCAP_applicability':False,'source43_power_result_scope':'Historical source43/37 only; not inherited by49/29','source48_mesh_free_preparation_is_numerical_qualification':False,'I2C_electrical_status':'NOT_QUALIFIED','native_open_connections':29,'native_errors':0,'native_warnings':0,'actual_io_cases':[13,22],'actual_io_channels':[11,20]}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__': main()
