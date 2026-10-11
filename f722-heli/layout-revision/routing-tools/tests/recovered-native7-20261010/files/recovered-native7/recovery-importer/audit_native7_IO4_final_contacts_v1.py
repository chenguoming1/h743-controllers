#!/usr/bin/env python3
"""Narrow native7 IO4 contact/protection audit; input checks are geometry-free.

Exactly eleven cuts and four pad-net substitutions. This module never routes,
imports CAD, edits native data, or normalizes polygons. A real-board audit needs
an exact request/validator/output runtime lease. Synthetic tests need no lease.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import copy
import datetime as dt
import importlib.metadata
import importlib.util
from pathlib import Path

import audit_native7_final_contacts_v2 as k
imp = k.imp
KERNEL_SHA = '1c2cb00c26efe26ef306e9c03feb0034c53c136635edf77b6b69085407b90292'
IMPORTER_SHA = '00bbd9af829626cd6da030260e2ace9bab2555d1edba2359bb722dec13c79ae8'
SCOPE_SHA = '815df90a2ae84d774acc993b100d110405db7b3d4e9a5f965450943cc4aed487'
SOURCE_PLAN_SHA = 'd5f47c51e44de34910497503cebc8df808f9950a73e54ea5c36a9ca4764ac18f'
SOURCE_CONTRACTS = {'actual_io': '573842a98c339006f1cc1045106f8243be39038edb8458606884051f274e0753',
                    'candidate': 'd68e7f36e76a183703843762ac45f6de701192c04aa8e1dd8c0190aee823f82e'}
FILES = {'source_native', 'final_native', 'candidate_board', 'plan', 'provenance', 'role_sidecar',
         'cut_scope', 'paired_source_plan', 'source_logical_map', 'paired_netlist',
         'source_actual_io_contracts', 'source_candidate_contracts',
         'final_actual_io_contracts', 'final_candidate_contracts'}
PAD_NETS = {'76401567-1405-4a22-b70c-0a7f2502777e': 'unconnected-(U15-IO1-Pad1)',
            '85f6ae89-da40-4223-9e1c-51ee8cc2f22f': 'unconnected-(U15-NC10-Pad10)',
            'dddece5c-5254-4426-8e4c-1fb5f9e85655': 'PORT_C_RX_EXT',
            'af34758d-03d4-4898-8fb1-2be5765ea280': 'PORT_C_RX_EXT'}
SUBSTITUTE = {'76401567-1405-4a22-b70c-0a7f2502777e': 'dddece5c-5254-4426-8e4c-1fb5f9e85655',
              '85f6ae89-da40-4223-9e1c-51ee8cc2f22f': 'af34758d-03d4-4898-8fb1-2be5765ea280'}
RETIRED = set(SUBSTITUTE.values())
CUTS = {'00d3d778-abd5-4fa9-8b8f-9877e7b83803', '0704cc1e-3f63-51e7-b36b-26e4c9a347e5',
        '6e64820c-b464-5142-a228-ebb74be4b044', '7e53c88f-9a87-5ba3-9c32-455d9649a9f5',
        '84864ccd-ac78-5d94-bbdd-daebc37d1ceb', '8f22baac-a8ff-4219-8c6b-8d5695979bc7',
        '97282ff5-d6b5-415f-a3c4-0390df70f0ea', 'a08299df-6002-52fd-8f9e-27b83956263e',
        'bcf4a808-4cd6-5541-8d5e-f9545c5dc1a2', 'c577b646-60c8-5101-b044-be71979ecce8',
        'f30237b0-7063-45c1-947a-2b6d75ac6f88'}
RX = 'PORT_C_RX_EXT'
STAGE = 'native7_IO4_final_contact_audit'


def importer():
    path = Path(__file__).with_name('import_native7_u15_io4_v2.py')
    imp.require(imp.sha(k.__file__) == KERNEL_SHA and imp.sha(imp.__file__) == k.IMPORTER_SHA,
                'Frozen contact kernels/dependency changed')
    imp.require(imp.sha(path) == IMPORTER_SHA, 'Frozen IO4 importer changed or not yet sealed')
    spec = importlib.util.spec_from_file_location('bound_IO4_importer', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def exact_contract_delta(source, final):
    """Only the published RX clamp changes; every other actual/candidate row is exact."""
    expected = copy.deepcopy(source['checks'])
    rows = [r for r in expected if r['id'] == 'published-06']
    imp.require(len(rows) == 1 and rows[0]['net'] == RX and rows[0]['clamp'] == 'U15.1', 'Wrong old RX contract')
    rows[0]['clamp'] = 'U15.5'
    imp.require(final['checks'] == expected, 'Protection rows differ beyond the explicit IO1 to IO4 substitution')
    imp.require(final['U15_actual_clamps'] == {RX: 'U15.5', 'PORT_C_TX_EXT': 'U15.2'} and
                final['U15_routing_land_assignments'] == {'U15.6': RX, 'U15.9': 'PORT_C_TX_EXT'} and
                final['package_internal_NC_conduction'] is False, 'Actual/NC protection semantics differ')


def validate_scope(scope, source, source_plan, plan):
    old = imp.unique(source['objects'])
    cuts = imp.unique(scope['inventory']['removed_native_records'])
    imp.require(set(cuts) == CUTS and all(cuts[u] == old[u] for u in cuts), 'Exact eleven full native cuts required')
    imp.require({r['record']['uuid'] for r in plan['removed_native_records']} == CUTS and
                plan['removed_native_records'] == source_plan['removed_native_records'], 'Route plan cut set differs')
    for row in plan['removed_native_records']:
        imp.require(row['record'] == old[row['record']['uuid']] and
                    row['full_record_sha256'] == imp.record_sha(row['record']), 'Full cut record hash differs')
    delta = {r['uuid']: r['after_net'] for r in source_plan['pad_net_delta']}
    imp.require(delta == PAD_NETS, 'Exactly four canonical pad-net changes required')


def role_binding(sidecar, plan, proof, files):
    imp.exact_keys(sidecar, ['schema', 'source', 'plan_sha256', 'board_sha256', 'native_sha256', 'recipe_roles'], 'IO4 roles')
    imp.require(sidecar['schema'] == 'f722-native7-U15-IO4-recipe-roles/v2' and
                sidecar['source'] == plan['source'] and sidecar['recipe_roles'] == plan['recipe_roles'], 'Role sidecar differs')
    for key, name in [('plan_sha256', 'plan'), ('board_sha256', 'candidate_board'), ('native_sha256', 'final_native')]:
        imp.require(sidecar[key] == files[name]['sha256'] == proof[key], 'Role identity binding differs: ' + key)
    roles = imp.unique(plan['recipe_roles'], key='name')
    recipes = imp.unique(plan['added_copper'], key='name')
    imp.require(set(roles) == set(recipes), 'One explicit role per complete recipe required')
    allowed = {'upstream': RX, 'downstream': RX, 'ground': 'GND', 'hold': 'FLASH_HOLD_N'}
    for name, row in roles.items():
        imp.exact_keys(row, ['name', 'net', 'logical_net', 'role'], 'Role recipe')
        imp.require(allowed.get(row['role']) == row['net'] and
                    all(row[key] == recipes[name][key] for key in ('name', 'net', 'logical_net')), 'Role/physical net mismatch')
    imp.require({r['role'] for r in roles.values()} == set(allowed), 'All four narrow functions required')
    return {r['uuid']: roles[r['name']]['role'] for r in proof['recipe_to_native_UUIDs']}


def load_bound_inputs(request_path):
    """Pure hash/JSON/XML checks, never calls geometry or native runtime."""
    mod = importer()
    request = imp.read(request_path)
    imp.exact_keys(request, ['schema', 'files'], 'IO4 contact request')
    imp.require(request['schema'] == 'f722-native7-IO4-contact-request/v1' and set(request['files']) == FILES,
                'Missing/extra narrow IO4 request inputs')
    data = {}; files = request['files']
    for name, binding in files.items():
        imp.exact_keys(binding, ['path', 'sha256'], 'Bound file')
        path = Path(binding['path'])
        imp.require(path.is_absolute() and path.is_file() and imp.sha(path) == binding['sha256'], 'Missing/changed input: ' + name)
        data[name] = path.read_bytes() if name in ('candidate_board', 'paired_netlist') else imp.read(path)
    pins = {'source_native': imp.SOURCE_BINDINGS['native_sha256'], 'source_logical_map': imp.SOURCE_BINDINGS['logical_map_sha256'],
            'cut_scope': SCOPE_SHA, 'paired_source_plan': SOURCE_PLAN_SHA}
    pins.update({'source_' + kind + '_contracts': digest for kind, digest in SOURCE_CONTRACTS.items()})
    for name, digest in pins.items():
        imp.require(files[name]['sha256'] == digest, 'Wrong source artifact: ' + name)
    source, final, plan, proof, paired = [data[x] for x in ('source_native', 'final_native', 'plan', 'provenance', 'paired_source_plan')]
    validate_scope(data['cut_scope'], source, paired, plan)
    imp.require(source['board_sha256'] == imp.SOURCE_BINDINGS['board_sha256'], 'Wrong source native board')
    validation = mod.validate_plan(plan, source, data['source_logical_map']['logical_route_map'], paired, require_complete=True)
    imp.require(proof['schema'] == 'f722-native7-U15-IO4-import-receipt/v2' and
                proof['status'] == 'CONSTRUCTION_VERIFIED_NOT_ACCEPTED' and proof['acceptance_claimed'] is False and
                proof['importer_sha256'] == IMPORTER_SHA and proof['source'] == imp.SOURCE_BINDINGS,
                'Unbound native construction receipt')
    for key, name in [('plan_sha256','plan'), ('board_sha256','candidate_board'), ('native_sha256','final_native'),
                      ('paired_source_plan_sha256','paired_source_plan'), ('cut_scope_sha256','cut_scope'),
                      ('paired_netlist_sha256','paired_netlist'), ('role_sidecar_sha256','role_sidecar')]:
        imp.require(proof[key] == files[name]['sha256'], 'Construction binding mismatch: ' + key)
    imp.require(final['board_sha256'] == proof['board_sha256'] and final['native_build'] == source['native_build'] == '10.0.6+dfsg-1' and
                final['maximum_polygon_error_mm'] == source['maximum_polygon_error_mm'] == .00001, 'Wrong native export/build/error')
    recipes = imp.unique(plan['added_copper'], key='name'); now = imp.unique(final['objects'])
    mappings = imp.unique(proof['recipe_to_native_UUIDs']); added = imp.unique(proof['added_native_records'])
    expected = {imp.native_uuid(proof['plan_sha256'], r['name'], i): (r['name'], i)
                for r in recipes.values() for i in (range(len(r['points'])-1) if r['kind']=='track' else [None])}
    imp.require(set(mappings) == set(added) == set(expected), 'Incomplete deterministic recipe-to-native mapping')
    additions = []
    for uid, (name, index) in expected.items():
        mapping = mappings[uid]
        imp.require(mapping['name'] == name and mapping['segment_index'] == index and added[uid] == now[uid] and
                    mapping['full_record_sha256'] == imp.record_sha(now[uid]), 'Added native record/provenance differs')
        additions.append({'uuid': uid, 'recipe': recipes[name], 'segment_index': index, 'expected_native_record': added[uid]})
    # Verifies all original records, all 156 poses/558 pad contours, zone metadata,
    # complete recipe fields, and the exact four semantic substitutions. Numeric
    # net codes may change only through the verified global name/code bijection.
    mod.verify_native(source, final, validation, additions)
    raw, _ = mod.semantic_inputs()
    mod.verify_paired_native(final, data['paired_netlist'], raw)
    expected_contracts = mod.bound_contracts(paired, proof['board_sha256'], proof['native_sha256'], proof['plan_sha256'], proof['paired_netlist_sha256'])
    for kind in SOURCE_CONTRACTS:
        exact_contract_delta(data['source_' + kind + '_contracts'], data['final_' + kind + '_contracts'])
        imp.require(data['final_' + kind + '_contracts'] == expected_contracts[kind], 'Complete bound contract differs')
    roles = role_binding(data['role_sidecar'], plan, proof, files)
    data.update(request=request, added_ids=set(expected), added_roles=roles,
                source_records=imp.unique(source['objects']), final_records=now)
    return data


def rich_partition(records, *, subtract_region=None, omit_ids=frozenset(), global_holes=None):
    """Same exact contours/edge rules as v2, with fragment roots retained.

    UUID membership alone cannot detect a drill splitting one retained track.
    Keeping fragments makes that loss visible to the source-tree comparator.
    """
    *_, STRtree = k.geometry_modules()
    if global_holes is None:
        global_holes = k.hole_map(records, {l for r in records for l in r['copper']})
    nodes=[]; layers=defaultdict(list); barrels=defaultdict(list); shapes={}; holes={}
    for row in records:
        uid=row['uuid']
        if uid in omit_ids: continue
        copper,hole=k.conductive_shapes(row, global_holes); holes[uid]=hole
        if subtract_region:
            copper={l:s.difference(subtract_region[l]) if l in subtract_region else s for l,s in copper.items()}
        shapes[uid]=copper
        for layer, shape in copper.items():
            for polygon in k.polygon_parts(shape):
                i=len(nodes); nodes.append({'uuid':uid,'layer':layer,'shape':polygon}); layers[layer].append(i)
                if row.get('plated') is True and hole is not None and layer in row.get('barrel_layers',[]) and polygon.boundary.intersection(hole.boundary).length>0:
                    barrels[uid].append(i)
    parent=list(range(len(nodes)))
    def find(i):
        while parent[i]!=i: parent[i]=parent[parent[i]]; i=parent[i]
        return i
    def join(a,b): parent[find(a)]=find(b)
    contacts={}
    for layer, indices in layers.items():
        tree=STRtree([nodes[i]['shape'] for i in indices])
        for local,i in enumerate(indices):
            for other in tree.query(nodes[i]['shape'],predicate='intersects'):
                if int(other)<=local: continue
                j=indices[int(other)]; area=nodes[i]['shape'].intersection(nodes[j]['shape']).area
                if area>0:
                    join(i,j); a,b=sorted((nodes[i]['uuid'],nodes[j]['uuid']))
                    if a!=b: contacts[(a,b,layer)]=contacts.get((a,b,layer),0)+area
    for positions in barrels.values():
        for i in positions[1:]: join(positions[0],i)
    groups=defaultdict(set); memberships=defaultdict(set); components=defaultdict(list)
    for i,node in enumerate(nodes):
        node['root']=find(i); groups[node['root']].add(node['uuid']); memberships[node['uuid']].add(node['root']); components[node['root']].append(node)
    return {'groups':list(groups.values()),'memberships':memberships,'contacts':contacts,'shapes':shapes,'holes':holes,
            'nodes':nodes,'components':components}


def preserve_original_components(original, final, removed_ids=frozenset(), substitutions=None, retired=frozenset()):
    substitutions = substitutions or {}; by=defaultdict(list)
    for node in final['nodes']: by[node['uuid']].append(node)
    checks=[]
    for index, nodes in original['components'].items():
        roots=set(); missing=[]; terminals=set(); mapped=[]
        for node in nodes:
            uid=node['uuid']
            if uid in retired or uid in removed_ids: continue
            target=substitutions.get(uid,uid); terminals.add(target)
            if uid in substitutions:
                found=set(final['memberships'].get(target,set())); mapped.append({'from':uid,'to':target})
            else:
                found={n['root'] for n in by[target] if n['layer']==node['layer'] and n['shape'].intersection(node['shape']).area>0}
            if not found: missing.append({'uuid':uid,'layer':node['layer']})
            roots.update(found)
        retired_group=all(n['uuid'] in retired for n in nodes)
        checks.append({'source_component':index,'retained_terminal_UUIDs':sorted(terminals),
                       'declared_terminal_substitutions':mapped,'final_component_roots':sorted(roots),
                       'missing_conductive_fragments':missing,'retired_unused_singleton':retired_group,
                       'passed':retired_group or (bool(terminals) and not missing and len(roots)==1)})
    return checks


def connected(graph, ids):
    groups=[graph['memberships'].get(uid,set()) for uid in ids]
    return bool(groups) and bool(set.intersection(*groups))


def protection_case(records, contract, global_holes, error_mm):
    """Actual physical clamp cut; NC lands never substitute for the bonded pad."""
    _,_,_,union,_=k.geometry_modules()
    objects=[r for r in records if r['net']==contract['net']]
    pads={r['key']:r for r in objects if r['kind']=='pad'}
    keys=[contract[k] for k in ('clamp','source','target')]
    missing=[key for key in keys if key not in pads]
    if missing: return {'id':contract['id'],'net':contract['net'],'clamp':contract['clamp'],'missing_actual_pads':missing,'passed':False}
    clamp,source,target=[pads[key] for key in keys]
    whole=rich_partition(objects,global_holes=global_holes)
    cut,_=k.conductive_shapes(clamp)
    graph=rich_partition(objects,subtract_region=cut,omit_ids={clamp['uuid']},global_holes=global_holes)
    a=graph['memberships'].get(source['uuid'],set()); b=graph['memberships'].get(target['uuid'],set())
    sides=[]
    for roots in (a,b):
        perlayer=defaultdict(list)
        for root in roots:
            for node in graph['components'][root]: perlayer[node['layer']].append(node['shape'])
        sides.append({layer:union(parts) for layer,parts in perlayer.items()})
    gaps=[{'layer':l,'gap_mm':sides[0][l].distance(sides[1][l]),'required_mm':contract['minimum_gap_required_mm']+error_mm}
          for l in sorted(set(sides[0])&set(sides[1]))]
    for gap in gaps: gap['passed']=gap['gap_mm']>=gap['required_mm']
    full=connected(whole,[clamp['uuid'],source['uuid'],target['uuid']]); separated=bool(a and b) and not(a&b)
    return {'id':contract['id'],'net':contract['net'],'clamp':contract['clamp'],'full_actual_function_connected':full,
            'no_outside_actual_pad_bypass':separated,'outside_pad_gaps':gaps,
            'passed':full and separated and bool(gaps) and all(g['passed'] for g in gaps)}


def rx_roles_check(data, records, holes, error):
    objects=[r for r in records if r['net']==RX]; by=imp.unique(objects)
    pads={r['key']:r for r in objects if r['kind']=='pad'}
    required=['U15.5','U15.6','J11.1','R34.1']
    imp.require(all(p in pads for p in required),'Missing final actual RX pads')
    clamp=pads['U15.5']; cut,_=k.conductive_shapes(clamp)
    graph=rich_partition(objects,subtract_region=cut,omit_ids={clamp['uuid']},global_holes=holes)
    up=graph['memberships'].get(pads['J11.1']['uuid'],set()); down=graph['memberships'].get(pads['R34.1']['uuid'],set())
    witnesses=[]
    full=rich_partition(objects,global_holes=holes)
    for role, roots in [('upstream',up),('downstream',down)]:
        for uid in sorted(data['added_ids']):
            if data['added_roles'].get(uid)!=role: continue
            actual=graph['memberships'].get(uid,set())
            # A track entirely inside the bonded land may have no outside root;
            # it still needs a positive/full-width contact below.
            passed=(bool(actual) and actual<=roots) or (not actual and all(s.difference(cut.get(l,s)).is_empty for l,s in full['shapes'][uid].items()))
            witnesses.append({'uuid':uid,'role':role,'outside_component_roots':sorted(actual),'passed':passed})
    role_contacts=[]
    for role in ('upstream','downstream'):
        found=[]
        for (a,b,layer),area in full['contacts'].items():
            if clamp['uuid'] not in (a,b): continue
            peer=b if a==clamp['uuid'] else a
            if data['added_roles'].get(peer)==role and by[peer]['kind']=='track':
                witness=k.full_width_witness(by[peer],full['shapes'][peer][layer],full['shapes'][clamp['uuid']][layer],layer,error)
                found.append({'uuid':peer,'layer':layer,'positive_area_mm2':area,**witness})
        role_contacts.append({'role':role,'actual_bonded_pad':'U15.5','full_width_contacts':found,'passed':any(w['passed'] for w in found)})
    nc=graph['memberships'].get(pads['U15.6']['uuid'],set())
    nc_check={'routing_land':'U15.6','belongs_only_to_upstream':bool(nc) and nc<=up and not(nc&down),
              'internal_package_conduction_assumed':False}
    return {'role_assignments':witnesses,'bonded_pad_branch_contacts':role_contacts,'NC6':nc_check,
            'passed':bool(up and down) and not(up&down) and nc_check['belongs_only_to_upstream'] and
                     all(r['passed'] for r in witnesses+role_contacts)}


def audit_data(data):
    """Full-board geometry entry, called only behind the exact lease in public API."""
    imp.require(importlib.metadata.version('shapely')=='2.2.0','Pinned Shapely 2.2.0 required')
    source=k.native_records_with_fills(data['source_native']); final=k.native_records_with_fills(data['final_native'])
    error=data['final_native']['maximum_polygon_error_mm']
    oldholes=k.hole_map(source,data['source_native']['copper_layers']); newholes=k.hole_map(final,data['final_native']['copper_layers'])
    oldzones=imp.unique(data['source_native']['zones'])
    changedfills={z['uuid'] for z in data['final_native']['zones'] if z['filled']!=oldzones[z['uuid']]['filled']}
    affected=set(data['added_ids'])|changedfills|set(PAD_NETS); oldgraphs={}; graphs={}; oldrows={}; rows={}
    # Numeric net-code changes do not turn a geometrically unchanged primary into
    # a moving object. All other physical fields were checked by the pure loader.
    for net in sorted({r['net'] for r in source}|{r['net'] for r in final}):
        oldrows[net]=[r for r in source if r['net']==net]; rows[net]=[r for r in final if r['net']==net]
        oldgraphs[net]=rich_partition(oldrows[net],global_holes=oldholes); graphs[net]=rich_partition(rows[net],global_holes=newholes)
        for uid in set(oldgraphs[net]['shapes'])&set(graphs[net]['shapes']):
            a,b=oldgraphs[net]['shapes'][uid],graphs[net]['shapes'][uid]
            if set(a)!=set(b) or any(not a[l].equals(b[l]) for l in a): affected.add(uid)
    components=[]; boundaries=[]; endpoints=[]; inherited=[]; oldfindings=[]
    for net in oldgraphs:
        components += [dict(c,net=net) for c in preserve_original_components(oldgraphs[net],graphs[net],CUTS,
                                            SUBSTITUTE if net==RX else {}, RETIRED)]
    for net in graphs:
        # Source records normalized only for the verified numeric code remap.
        baseline=[]
        for r in oldrows[net]:
            r=copy.deepcopy(r)
            if r['uuid'] in data['final_records']: r['net_code']=data['final_records'][r['uuid']].get('net_code')
            baseline.append(r)
        old, changed, prior=k.compare_contact_findings(rows[net],graphs[net],baseline,oldgraphs[net],affected,error)
        oldfindings += [dict(r,net=net) for r in old]; boundaries += [dict(r,net=net) for r in changed]; inherited += [dict(r,net=net) for r in prior]
        endpoints += k.endpoint_witnesses(data['plan'],data['provenance'],rows[net],graphs[net],error)
    closures=[]
    for net in (RX,'FLASH_HOLD_N'):
        closures.append({'net':net,'positive_area_components':len(graphs[net]['groups']),'passed':len(graphs[net]['groups'])==1})
    # GND does not get a single-component waiver or an assumed package bond:
    # the complete original GND fragment groups above must survive, including
    # U15.3/.8 and actual saved planes, and all additions need measured contacts.
    contact_ids={u for r in boundaries if r['passed'] for u in (r['left_uuid'],r['right_uuid'])}
    newchecks=[{'uuid':u,'passed':u in contact_ids} for u in sorted(data['added_ids'])]
    actual=[protection_case(final,c,newholes,error) for c in data['final_actual_io_contracts']['checks']]
    source_actual=[protection_case(source,c,oldholes,error) for c in data['source_actual_io_contracts']['checks']]
    historical=[protection_case(final,c,newholes,error) for c in data['source_actual_io_contracts']['checks'] if c['id']=='published-06']
    role=rx_roles_check(data,final,newholes,error)
    checks=components+boundaries+endpoints+closures+newchecks+actual+[role]
    return {'schema':'f722-native7-IO4-final-contact-audit/v1','contact_and_protection_gate_passed':all(r['passed'] for r in checks),
            'source':imp.SOURCE_BINDINGS,'bound_inputs':data['request']['files'],'exact_cut_count':11,'pad_net_substitutions':PAD_NETS,
            'original_net_component_preservation':components,'RX_and_HOLD_complete':closures,'new_or_affected_contacts':boundaries,
            'complete_recipe_endpoint_contacts':endpoints,'new_object_contacts':newchecks,'actual_protection_checks':actual,
            'source_actual_protection_results':source_actual,'historical_IO1_expectation_on_final':historical,
            'historical_IO1_failure_is_retained_not_an_acceptance_gate':True,'IO4_role_and_NC_checks':role,
            'source_contact_findings':oldfindings,'unchanged_inherited_contact_findings':inherited,
            'changed_fill_UUIDs':sorted(changedfills),'new_or_affected_UUIDs':sorted(affected),
            'ordinary_remaining_opens_expected':['FLASH_SCK','FLASH_MISO','FLASH_MOSI','PORT_C_RX_MCU','PORT_C_TX_MCU'],
            'ordinary_remaining_opens_qualified_or_closed':False,'contour_normalization_used':False,
            'polygon_error_mm':error,'nominal_width_tolerance_mm':2*error,
            'limitations':['Contact/protection topology only; DRC, ERC, paired parity and all other physical/electrical gates remain separate.',
                          'Saved plane contacts and retained components are DC evidence only; fresh plane neck, reference, ESD, current and VCAP checks remain required.',
                          'All original native groups are preserved individually; original open groups are not silently treated as completed nets.',
                          'Partial annular contacts without straight-track width or full-land coverage evidence fail closed.',
                          'No real-board invocation is implied by synthetic verification. The bounded eleven-cut routing candidate failed mutual RX via packing.'],
            'acceptance_claimed':False,'power_evidence_stale':True}


def validate_lease(path, request_path, output):
    lease=imp.read(path)
    imp.exact_keys(lease,['schema','active','owner','lease_id','stage','request_sha256','validator_sha256','output_path','issued_utc','expires_utc'],'IO4 audit lease')
    imp.require(lease['schema']=='f722-native7-IO4-contact-owner-lease/v1' and lease['active'] is True and lease['stage']==STAGE and
                lease['request_sha256']==imp.sha(request_path) and lease['validator_sha256']==imp.sha(__file__) and lease['output_path']==str(output),
                'No exact bound IO4 audit runtime permission')
    imp.require(all(isinstance(lease[x],str) and lease[x].strip() for x in ('owner','lease_id')),'Missing lease identity')
    begin,end=[dt.datetime.fromisoformat(lease[x].replace('Z','+00:00')) for x in ('issued_utc','expires_utc')]
    imp.require(begin.tzinfo is not None and end.tzinfo is not None and begin<=dt.datetime.now(dt.timezone.utc)<end and end-begin<=dt.timedelta(hours=2),'Invalid audit runtime interval')
    return lease


def audit_final_native_contacts(request_path, lease_path, output_path):
    request_path,lease_path,output=map(Path,(request_path,lease_path,output_path))
    imp.require(output.is_absolute() and output==output.resolve() and not output.exists(),'Use a new absolute report path')
    reqhash,leasehash=imp.sha(request_path),imp.sha(lease_path)
    data=load_bound_inputs(request_path); lease=validate_lease(lease_path,request_path,output)
    report=audit_data(data)
    imp.require(imp.sha(request_path)==reqhash and imp.sha(lease_path)==leasehash,'Inputs changed during audit')
    load_bound_inputs(request_path); validate_lease(lease_path,request_path,output)
    report.update(request_sha256=reqhash,validator_sha256=imp.sha(__file__),lease_id=lease['lease_id'])
    imp.write(output,report); return report


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--check-inputs',action='store_true'); parser.add_argument('--lease',type=Path); parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if args.check_inputs:
        imp.require(args.lease is None and args.out is None,'Input-only command cannot take lease/output')
        load_bound_inputs(args.request); print('Bound IO4 inputs passed; geometry not run.')
    else:
        imp.require(args.lease and args.out,'Actual audit requires bound --lease and --out')
        report=audit_final_native_contacts(args.request,args.lease,args.out)
        print(imp.canonical({'contact_and_protection_gate_passed':report['contact_and_protection_gate_passed'],'report':str(args.out),'acceptance_claimed':False}))
        if not report['contact_and_protection_gate_passed']: raise SystemExit(2)


if __name__=='__main__':
    try: main()
    except (ValueError,KeyError,TypeError,OSError) as error: raise SystemExit(str(error)) from error
