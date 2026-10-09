#!/usr/bin/env python3
"""Source-bound, capped prototype DC screen. The default CLI is preflight only."""
import argparse
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
import platform
import numpy as np
import scipy
import shapely
import sexpdata
from copper_fem import Mesh, Limits, Refused, copper_material, native_geometry, contact_keys, contact_spec_geometry
from dc_circuit import solve_circuit

SCHEMA = 'f722-scoped-static-freeze/v1'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    try:
        return json.loads(Path(path).read_text(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (ValueError, OSError) as exc:
        raise Refused(f'Cannot read strict JSON {path}: {exc}') from exc


def guard_output(freeze_path, ledger_path, output_path):
    """Do not overwrite a frozen input, even when writing a refusal result."""
    freeze_path, ledger_path, output_path = map(Path,(freeze_path,ledger_path,output_path))
    protected = [freeze_path,ledger_path] + list(Path(__file__).parent.glob('*.py'))
    try:
        manifest = read_json(freeze_path)
        protected.extend(freeze_path.parent/spec['path'] for spec in manifest.get('files',{}).values()
                         if isinstance(spec,dict) and isinstance(spec.get('path'),str))
    except (Refused,TypeError,AttributeError):
        # Parse failure still must not replace the manifest or ledger itself.
        pass
    if output_path.suffix != '.json':
        raise Refused('Result output must be a separate .json file')
    for path in protected:
        if output_path.resolve() == path.resolve() or (output_path.exists() and path.exists() and output_path.samefile(path)):
            raise Refused('Output aliases a protected source; no output was written')


def stackup_centers(board, layers):
    """Use native stackup thickness, not equally spaced layers or fabrication claims."""
    tree = sexpdata.loads(Path(board).read_text())
    def find(node, key):
        hits = [x for x in node if isinstance(x, list) and x and str(x[0]) == key]
        if len(hits) != 1:
            raise Refused(f'Expected one native {key}')
        return hits[0]
    stackup = find(find(tree, 'setup'), 'stackup')
    center = {}; z = 0.0; entries = []
    for entry in stackup:
        if not isinstance(entry, list) or not entry or str(entry[0]) != 'layer':
            continue
        kind = str(find(entry, 'type')[1])
        if kind not in ('copper', 'core', 'prepreg'):
            continue
        thickness = float(find(entry, 'thickness')[1])
        if not math.isfinite(thickness) or thickness <= 0:
            raise Refused('Invalid native stackup thickness')
        name = str(entry[1])
        if kind == 'copper':
            center[name] = z + thickness/2
        entries.append({'name': name, 'type': kind, 'thickness_mm': thickness})
        z += thickness
    if list(center) != layers:
        raise Refused('Native stackup copper order differs from export')
    return {'layer_z_mm': center, 'layers': entries, 'native_metal_to_metal_thickness_mm': z,
            'fabricator_acceptance': False}


def preflight(freeze_path, ledger_path):
    freeze_path, ledger_path = Path(freeze_path), Path(ledger_path)
    manifest = read_json(freeze_path); ledger = read_json(ledger_path)
    if manifest.get('schema') != SCHEMA or manifest.get('status') != 'frozen-for-scoped-static-screen':
        raise Refused('Missing explicit frozen scope; construction checkpoints are not eligible')
    if ledger.get('schema') != 'f722-static-ledger/v1' or ledger.get('status') != 'ready':
        raise Refused('Case ledger is unfinished')
    if ledger.get('freeze_manifest_sha256') != sha256(freeze_path):
        raise Refused('Ledger is not bound to this freeze manifest')
    if manifest.get('scope') not in ('power-only', 'final-board'):
        raise Refused('Unknown frozen scope')
    for name,expected in manifest.get('analysis_source_sha256',{}).items():
        if Path(name).name!=name or sha256(Path(__file__).parent/name)!=expected:
            raise Refused('Analysis source changed after compilation: '+name)
    if not manifest.get('saved_fill_verified') or not manifest.get('checks_run_on_frozen_board'):
        raise Refused('Fresh saved-fill/check evidence is missing')
    required = ['board', 'geometry', 'connectivity', 'parts', 'parity', 'physical', 'drc_normal', 'drc_all_track']
    files = {}
    if not set(required)<=set(manifest.get('files',{})):
        raise Refused('Frozen manifest lacks required evidence files')
    for name in manifest['files']:
        spec = manifest.get('files', {}).get(name, {})
        if not spec.get('path') or not spec.get('sha256'):
            raise Refused(f'Missing frozen file {name}')
        path = freeze_path.parent / spec['path']
        if not path.is_file() or sha256(path) != spec['sha256']:
            raise Refused(f'Frozen {name} is missing or changed')
        files[name] = path
    board_hash = sha256(files['board'])
    geometry = read_json(files['geometry']); connectivity = read_json(files['connectivity'])
    for name, report in [('geometry', geometry), ('connectivity', connectivity),
                         ('parity', read_json(files['parity'])), ('physical', read_json(files['physical']))]:
        if report.get('board_sha256') != board_hash:
            raise Refused(f'{name} report belongs to another board')
        if name in ('parity', 'physical') and report.get('passed') is not True:
            raise Refused(f'{name} check has not passed')
    if geometry.get('schema') != 'kicad-native-copper/v1' or geometry.get('source_unchanged') is not True or geometry.get('units') != 'mm':
        raise Refused('Not an unchanged native millimetre export')
    if not geometry.get('outline_with_npth', {}).get('valid'):
        raise Refused('Native outline is not valid')
    networks = ledger.get('networks', [])
    nets = [x['net'] for x in networks]
    if not nets or len(set(nets)) != len(nets):
        raise Refused('Missing or duplicate network definitions')
    if set(nets) != set(manifest.get('tested_nets', [])):
        raise Refused('Case networks do not match frozen tested scope')
    all_nodes = [name for network in networks for name in network['contacts']]
    if len(set(all_nodes)) != len(all_nodes):
        raise Refused('Contact names must be unique across nets')
    contact_names = {network['net']: set(network['contacts']) for network in networks}
    for network in networks:
        if len(network['contacts']) < 2:
            raise Refused('Each network needs at least two finite ports')
        native_pads = {}
        for obj in geometry['objects']:
            if obj['kind']=='pad' and obj.get('net')==network['net']:
                native_pads.setdefault(obj['key'], []).append(obj)
        for spec in network['contacts'].values():
            if any(key not in native_pads for key in contact_keys(spec)) or spec['layer'] not in geometry['copper_layers']:
                raise Refused('Contact refers to an absent pad/net/layer')
            contact_spec_geometry(native_pads, spec)
    for category in ['unit_transfers','loops','cases']:
        names = [x['name'] for x in ledger.get(category, [])]
        if len(names) != len(set(names)):
            raise Refused(f'Duplicate {category} names')
    transfers = list(ledger.get('unit_transfers', []))
    for loop in ledger.get('loops', []):
        if not loop['legs']:
            raise Refused('Empty loop definition')
        transfers.extend(loop['legs'])
    for transfer in transfers:
        if transfer['net'] not in contact_names or not {transfer['source'],transfer['sink']} <= contact_names[transfer['net']]:
            raise Refused('Unit/loop transfer uses an absent network contact')
        if transfer['source'] == transfer['sink']:
            raise Refused('Unit/loop transfer must have distinct contacts')
    for net in nets:
        row = connectivity.get('nets', {}).get(net, {})
        if row.get('pad_group_count') != 1:
            raise Refused(f'Tested net {net} is unfinished or lacks native connectivity evidence')
        expected = {x['uuid'] for x in geometry['objects'] if x['kind']=='pad' and x.get('net')==net and x.get('number')}
        actual = {u for g in row.get('groups', []) for u in g.get('pad_uuids', [])}
        if expected != actual or not expected:
            raise Refused(f'Tested net {net} connectivity omits native pads')
    drc_summary = {}
    for name in ['drc_normal', 'drc_all_track']:
        drc = read_json(files[name])
        if 'violations' not in drc or 'unconnected_items' not in drc:
            raise Refused(f'{name} is not a complete native DRC JSON')
        errors = [x for x in drc['violations'] if x.get('severity') == 'error']
        if errors or drc.get('schematic_parity'):
            raise Refused(f'{name} has geometric/parity errors')
        opens = drc['unconnected_items']
        tested_uuids = {x['uuid'] for x in geometry['objects'] if x.get('net') in nets}
        if any(any(x.get('uuid') in tested_uuids for x in row.get('items', [])) for row in opens):
            raise Refused(f'{name} contains opens on tested power/return nets')
        if manifest['scope'] == 'final-board' and opens:
            raise Refused('Final-board scope has ordinary unfinished connections')
        drc_summary[name] = {'ordinary_opens_outside_scope': len(opens),
                             'warnings': sum(x.get('severity')=='warning' for x in drc['violations']),
                             'ignored_checks': drc.get('ignored_checks', [])}
        if drc.get('ignored_checks'):
            raise Refused('DRC has ignored checks; resolve or explicitly review outside this interface')
    stackup = stackup_centers(files['board'], geometry['copper_layers'])
    spacing = ledger.get('mesh_spacings_mm', [])
    if len(spacing) < 2 or any(not math.isfinite(x) or x <= 0 for x in spacing) or any(b >= a for a,b in zip(spacing,spacing[1:])):
        raise Refused('At least two strictly finer positive mesh spacings are required')
    if not ledger.get('unit_transfers') and not ledger.get('loops') and not ledger.get('cases'):
        raise Refused('Empty validation request')
    for case in ledger.get('cases', []):
        if 'case_definition_sha256'in case:
            definition={k:v for k,v in case.items()if k!='case_definition_sha256'}
            actual=hashlib.sha256(json.dumps(definition,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
            if case['case_definition_sha256']!=actual:
                raise Refused('Resolved case definition changed: '+case['name'])
        if not set(case.get('nets',nets)) <= set(nets) or not case.get('nets',nets):
            raise Refused('Case uses absent or empty copper network selection')
        if not case.get('probes') or any('minimum_V' not in p and 'maximum_V' not in p for p in case['probes']):
            raise Refused('Loaded cases require explicit voltage floors/ceilings')
        if not case.get('assumptions'):
            raise Refused('Loaded case assumptions must be explicit')
    material_keys = {'temperature_C','thickness_mm','conductivity_IACS','plating_mm'}
    if set(ledger.get('material',{})) != material_keys:
        raise Refused('All copper material assumptions must be explicit')
    material = copper_material(**ledger['material'])
    numerical = ledger.get('convergence', {})
    for key in ['relative_impedance', 'absolute_impedance_ohm', 'absolute_voltage_V']:
        if not math.isfinite(numerical.get(key, -1)) or numerical.get(key, -1) <= 0:
            raise Refused('Explicit positive convergence tolerances are required')
    return {'manifest': manifest, 'ledger': ledger, 'geometry': geometry, 'files': files,
            'freeze_path': freeze_path, 'ledger_path': ledger_path,
            'board_sha256': board_hash, 'drc': drc_summary, 'stackup': stackup, 'material': material,
            'freeze_sha256': sha256(freeze_path), 'ledger_sha256': sha256(ledger_path)}


def summarize_transfer(mesh, test):
    result = mesh.solve({test['source']: 1.0, test['sink']: -1.0}, test['sink'])
    resistance = result['contact_voltage_V'][test['source']]
    return {'resistance_ohm': resistance, 'field': result}


def geometry_certificate_key(net,layer,receipt,spacing=None):
    key=net+'/'+layer
    grid=receipt.get('grid_spacing_mm')
    if grid is not None:
        if isinstance(grid,bool) or not isinstance(grid,(int,float)) or not math.isfinite(grid) or grid<=0:
            raise Refused('Invalid grid-bound geometry certificate spacing')
        if spacing is not None and grid!=spacing:
            raise Refused('Geometry certificate belongs to another mesh grid')
        key+='/grid='+str(float(grid))
    return key


def remember_geometry_certificate(context, net, layer, receipt):
    # JSON is the declared cache/result schema. Tuple/list differences from an
    # in-memory producer cannot change its exact serialized geometry evidence.
    canonical=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    encoded=canonical(receipt);normalized=json.loads(encoded)
    certificates=context.setdefault('geometry_certificates',{});key=geometry_certificate_key(net,layer,receipt)
    if key in certificates and canonical(certificates[key])!=encoded:
        previous=canonical(certificates[key]);failure=Refused('Native geometry certificate changed between meshes: '+key)
        failure.geometry_reproduction={'stage':'geometry_certificate_comparison','net':net,'layer':layer,
          'previous_sha256':hashlib.sha256(previous.encode()).hexdigest(),
          'current_sha256':hashlib.sha256(encoded.encode()).hexdigest(),
          'previous_receipt':certificates[key],'current_receipt':normalized}
        raise failure
    certificates[key]=normalized


def compact_result_evidence(result):
    """Replace repeated geometry receipts with verified references for CLI JSON.

    The library result stays unchanged. Numerical arrays/rows and the one
    top-level certificate store are shared, not copied. Each distinct receipt
    object is hashed only once, using the same canonical JSON as the exact
    geometry comparison (tuple/list differences therefore remain harmless).
    Already compact blocks are checked again instead of trusting their hashes.
    """
    certificates=result.get('geometry_certificates',{})
    if not isinstance(certificates,dict):
        raise Refused('Result geometry certificate store is not a dictionary')
    encoder=json.JSONEncoder(sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
    hashes={}
    def digest(receipt):
        if not isinstance(receipt,dict):
            raise Refused('Result geometry certificate is not a dictionary')
        identity=id(receipt)
        if identity not in hashes:
            value=hashlib.sha256()
            try:
                for chunk in encoder.iterencode(receipt):value.update(chunk.encode('utf-8'))
            except (TypeError,ValueError) as exc:
                raise Refused('Result geometry certificate is not finite canonical JSON') from exc
            hashes[identity]=(receipt,value.hexdigest())
        return hashes[identity][1]
    stored={key:digest(receipt) for key,receipt in certificates.items()}
    touched=False
    def compact_block(block,net,where,spacing):
        nonlocal touched
        raw='native_edge_noding' in block
        referenced='native_edge_noding_refs' in block
        if not raw and not referenced:return block
        if raw and referenced:
            raise Refused('Result block has both full and referenced geometry evidence: '+where)
        evidence=block['native_edge_noding' if raw else 'native_edge_noding_refs']
        if not isinstance(evidence,dict):
            raise Refused('Result geometry evidence is not a layer dictionary: '+where)
        refs={}
        for layer,receipt in evidence.items():
            if not isinstance(net,str) or not isinstance(layer,str):
                raise Refused('Result geometry evidence has no exact net/layer identity: '+where)
            if not isinstance(receipt,dict):raise Refused('Invalid geometry receipt/reference: '+where)
            if raw:
                key=geometry_certificate_key(net,layer,receipt,spacing)
            else:
                key=receipt.get('certificate_key')
                if not isinstance(key,str) or key not in certificates:
                    raise Refused('Missing top-level geometry certificate reference: '+where)
                if key!=geometry_certificate_key(net,layer,certificates[key],spacing):
                    raise Refused('Invalid result geometry certificate reference: '+where+'/'+layer)
            if key not in stored:
                raise Refused('Missing top-level geometry certificate '+key+' for '+where)
            if raw:
                actual=digest(receipt)
            else:
                if not isinstance(receipt,dict) or set(receipt)!={'certificate_key','sha256'} or receipt['certificate_key']!=key:
                    raise Refused('Invalid result geometry certificate reference: '+where+'/'+layer)
                actual=receipt['sha256']
            if actual!=stored[key]:
                raise Refused('Result geometry certificate hash mismatch: '+where+'/'+layer)
            refs[layer]={'certificate_key':key,'sha256':stored[key]}
        compact=dict(block)
        compact.pop('native_edge_noding',None)
        compact['native_edge_noding_refs']=refs
        touched=True
        return compact
    def compact_transfer(transfer,where,spacing):
        if 'field' not in transfer:return transfer
        return {**transfer,'field':compact_block(transfer['field'],transfer.get('net'),where+'/field',spacing)}
    def compact_run(run,where):
        compact=dict(run)
        spacing=run.get('spacing_mm')
        if 'ports' in run:
            compact['ports']=[compact_block(block,block.get('net'),where+'/ports/'+str(i),spacing)
                              for i,block in enumerate(run['ports'])]
        if 'unit_transfers' in run:
            compact['unit_transfers']=[compact_transfer(row,where+'/unit_transfers/'+str(i),spacing)
                                       for i,row in enumerate(run['unit_transfers'])]
        if 'loops' in run:
            compact['loops']=[{**loop,'legs':[compact_transfer(leg,where+'/loops/'+str(i)+'/legs/'+str(j),spacing)
                                             for j,leg in enumerate(loop['legs'])]}
                              for i,loop in enumerate(run['loops'])]
        if 'cases' in run:
            compact['cases']=[{**case,'fields':{net:compact_block(field,net,where+'/cases/'+str(i)+'/fields/'+net,spacing)
                                               for net,field in case['fields'].items()}}
                              if 'fields' in case else case for i,case in enumerate(run['cases'])]
        return compact
    compact=dict(result)
    for category in ['runs','partial_runs_unqualified']:
        if category in result:
            compact[category]=[compact_run(run,category+'/'+str(i)) for i,run in enumerate(result[category])]
    if touched:
        compact['geometry_certificate_reference_format']={
          'schema':'f722-native-geometry-certificate-reference/v1',
          'store':'geometry_certificates','hash':'SHA-256',
          'canonical_json':{'sort_keys':True,'separators':[',',':'],'ensure_ascii':True,'allow_nan':False,'encoding':'UTF-8'}}
    return compact


def run_screen(context):
    if context['manifest'].get('numerical_execution_authorized') is False:
        raise Refused('Numerical compute slot has not been released for this compiled freeze')
    if context['manifest'].get('numerical_execution_authorized')is True and any(os.environ.get(key)!='1'for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS']):
        raise Refused('Released numerical runs require per-process OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1')
    ledger = context['ledger']; geometry = context['geometry']; material = context['material']
    limits = Limits(**ledger.get('limits', {}))
    runs = []
    context['partial_runs']=runs  # Retain completed grids on a later refusal.
    started=time.monotonic()
    def progress(stage,**extra):
        callback=context.get('progress')
        if callback:callback({'stage':stage,'elapsed_seconds':time.monotonic()-started,**extra})
    context.setdefault('geometry_certificates',{})
    context.setdefault('mesh_cache_receipts',[])
    def remember_geometry(net,layer,receipt):
        remember_geometry_certificate(context,net,layer,receipt)
    def make_mesh(network, spacing):
        progress('mesh_start',net=network['net'],spacing_mm=spacing)
        net=network['net'];mesh=None;binding=None;cache_dir=context.get('mesh_cache_dir')
        if cache_dir is not None:
            from mesh_cache import mesh_binding,load_mesh,save_mesh
            binding=mesh_binding(context,network,spacing);mesh=load_mesh(cache_dir,binding,limits)
        if mesh is not None:
            for layer,receipt in mesh.native_edge_noding.items():remember_geometry(net,layer,receipt)
            context['mesh_cache_receipts'].append(mesh.mesh_cache_info)
            progress('mesh_cache_loaded',net=net,spacing_mm=spacing,raw_nodes=len(mesh.xyz),equations=mesh.n,triangles=len(mesh.triangles))
            return mesh
        domains, pads, barrels = native_geometry(geometry, network['net'])
        contacts = {node: (spec['layer'], contact_spec_geometry(pads,spec))
                    for node,spec in network['contacts'].items()}
        mesh=Mesh(domains, contacts, spacing, material['sheet_ohm'], material['thickness_mm'],
                  barrels, context['stackup']['layer_z_mm'], material['plating_mm'], limits,
                  native_edge_provider=(lambda layer:__import__('native_edge_noding').native_edges(geometry,net,layer))
                    if 'native_edge_noding.py'in context['manifest'].get('analysis_source_sha256',{})else None,
                  geometry_progress=lambda row:progress(row.pop('stage'),net=net,spacing_mm=spacing,**row),
                  geometry_certificate=lambda layer,receipt:remember_geometry(net,layer,receipt))
        if cache_dir is not None:
            receipt=save_mesh(mesh,cache_dir,binding);context['mesh_cache_receipts'].append(receipt)
            progress('mesh_checkpoint_saved',net=net,spacing_mm=spacing,cache_receipt=receipt)
        progress('mesh_ready',net=network['net'],spacing_mm=spacing,raw_nodes=len(mesh.xyz),
                 equations=mesh.n,triangles=len(mesh.triangles),contacts=len(mesh.contact_nodes),element_geometry=mesh.element_geometry)
        return mesh
    # One network mesh is alive at a time. The compact port matrices are kept;
    # reconstruct only for direct loaded-field checks after circuit coupling.
    for spacing in ledger['mesh_spacings_mm']:
        blocks = []; unit_by_name = {}; loop_legs = {}
        for network in ledger['networks']:
            net = network['net']; mesh = make_mesh(network,spacing)
            block = mesh.impedance(); block['net'] = net; blocks.append(block)
            progress('ports_solved',net=net,spacing_mm=spacing)
            for transfer in ledger.get('unit_transfers', []):
                if transfer['net'] == net:
                    unit_by_name[transfer['name']] = summarize_transfer(mesh,transfer)
            for loop in ledger.get('loops', []):
                for i,leg in enumerate(loop['legs']):
                    if leg['net'] == net:
                        loop_legs[(loop['name'],i)] = {'net':net,**summarize_transfer(mesh,leg)}
            del mesh
        unit_rows = []
        for transfer in ledger.get('unit_transfers', []):
            item = {'name': transfer['name'], 'net': transfer['net'], **unit_by_name[transfer['name']]}
            if 'maximum_ohm' in transfer:
                item['maximum_ohm'] = transfer['maximum_ohm']
                item['pass'] = item['resistance_ohm'] <= transfer['maximum_ohm']
            unit_rows.append(item)
        loops = []
        for loop in ledger.get('loops', []):
            legs = [loop_legs[(loop['name'],i)] for i in range(len(loop['legs']))]
            if not legs:
                raise Refused('Empty loop definition')
            resistance = sum(x['resistance_ohm'] for x in legs)
            loops.append({'name': loop['name'], 'legs': legs, 'resistance_ohm': resistance,
                          'maximum_ohm': loop.get('maximum_ohm'),
                          'pass': resistance <= loop['maximum_ohm'] if 'maximum_ohm' in loop else None,
                          'meaning': 'Sum of stated DC unit legs; not inductance or startup/dynamic validation'})
        cases = []
        for case in ledger.get('cases', []):
            selected = set(case.get('nets',[b['net'] for b in blocks]))
            result = solve_circuit(case, [b for b in blocks if b['net'] in selected])
            result['fields'] = {}; cases.append(result)
        progress('circuits_solved',spacing_mm=spacing,cases=len(cases))
        if cases:
            for network in ledger['networks']:
                relevant = [r for r in cases if any(p['net']==network['net'] for p in r['port_injections'])]
                if not relevant:
                    continue
                mesh = make_mesh(network,spacing)
                for result in relevant:
                    port = next(p for p in result['port_injections'] if p['net'] == network['net'])
                    result['fields'][network['net']] = mesh.solve(port['injections_A'])
                del mesh
                progress('loaded_fields_solved',net=network['net'],spacing_mm=spacing,cases=len(relevant))
        for result in cases:
            loss = sum(x['copper_loss_W'] for x in result['fields'].values())
            if abs(loss-result['power_W']['copper_loss']) > max(1e-8,abs(loss)*1e-6):
                raise Refused('Finite-port/direct-field energy cross-check failed')
        runs.append({'spacing_mm': spacing, 'ports': blocks, 'unit_transfers': unit_rows, 'loops': loops, 'cases': cases})
    coarse, fine = runs[-2:]; sensitivity = []; tol = ledger['convergence']
    for a,b in zip(coarse['ports'], fine['ports']):
        za,zb = np.asarray(a['impedance_ohm']),np.asarray(b['impedance_ohm'])
        delta = float(np.max(abs(za-zb))); scale = float(np.max(abs(zb)))
        allowed = max(tol['absolute_impedance_ohm'],tol['relative_impedance']*scale)
        sensitivity.append({'net':b['net'],'max_impedance_change_ohm':delta,'allowed_ohm':allowed,'pass':delta<=allowed})
    margins = []
    for a,b in zip(coarse['cases'],fine['cases']):
        for pa,pb in zip(a['probes'],b['probes']):
            delta = abs(pa['voltage_V']-pb['voltage_V'])
            margin = min(pb['voltage_V']-pb.get('minimum_V',-math.inf),pb.get('maximum_V',math.inf)-pb['voltage_V'])
            guard = max(delta,tol['absolute_voltage_V'])
            margins.append({'case':b['case'],'probe':pb['name'],'change_V':delta,'margin_V':margin,
                            'numerical_guard_V':guard,'pass':delta<=tol['absolute_voltage_V'] and margin>=guard})
    resistance_margins = []
    for category in ['unit_transfers','loops']:
        for a,b in zip(coarse[category],fine[category]):
            if b.get('maximum_ohm') is not None:
                delta=abs(a['resistance_ohm']-b['resistance_ohm']); guard=max(delta,tol['absolute_impedance_ohm'])
                margin=b['maximum_ohm']-b['resistance_ohm']
                resistance_margins.append({'name':b['name'],'change_ohm':delta,'margin_ohm':margin,
                                          'numerical_guard_ohm':guard,'pass':margin>=guard})
    passed = all(x['pass'] for x in sensitivity+margins+resistance_margins)
    passed &= all(case['static_probe_pass'] for run in runs for case in run['cases'])
    passed &= all(row.get('pass') is not False for run in runs for category in ['unit_transfers','loops'] for row in run[category])
    # TOCTOU guard covers all evidence files, not only the PCB.
    for name,path in context['files'].items():
        if sha256(path) != context['manifest']['files'][name]['sha256']:
            raise Refused(f'{name} changed during analysis; no result qualifies')
    if sha256(context['freeze_path']) != context['freeze_sha256'] or sha256(context['ledger_path']) != context['ledger_sha256']:
        raise Refused('Freeze or case ledger changed during analysis; no result qualifies')
    for name,expected in context['manifest'].get('analysis_source_sha256',{}).items():
        if sha256(Path(__file__).parent/name)!=expected:
            raise Refused('Analysis source changed during the run: '+name)
    return {'schema':'f722-scoped-static-result/v1','board_sha256':context['board_sha256'],
            'freeze_sha256':context['freeze_sha256'],'ledger_sha256':context['ledger_sha256'],
            'scope':context['manifest']['scope'],'conditional_static_screen_pass':bool(passed),
            'scope_is_final_board':context['manifest']['scope']=='final-board','thermal_or_flight_qualification':False,
            'material':material,'stackup':context['stackup'],'drc':context['drc'],
            'impedance_sensitivity':sensitivity,'voltage_margin_checks':margins,'resistance_margin_checks':resistance_margins,
            'runs':runs,'software':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'shapely':shapely.__version__,
              'source_sha256':{name:sha256(Path(__file__).parent/name) for name in ['copper_fem.py','dc_circuit.py','validate_static.py']}},
            'geometry_certificates':context['geometry_certificates'],'mesh_cache_receipts':context['mesh_cache_receipts'],
            'limitations':['New explicitly enumerated cases only; no historical result reuse.',
              'Two-grid sensitivity is not a rigorous discretization or manufacturing error bound.',
              'Finite lands and annuli omit within-land, pin, solder and contact heating; external contact/harness resistors belong in each ledger.',
              'Fixed-temperature DC loss/density is not ampacity or thermal prediction; 105 C copper does not override X5R/servo temperature limits.',
              'No startup, reverse blocking, handover, ESD, switching ripple, VCAP AC stability, KST signal-level, production or flight qualification.']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze',type=Path,required=True); parser.add_argument('--ledger',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--run',action='store_true',help='Run only after the power owner grants the compute slot; otherwise preflight only')
    parser.add_argument('--mesh-cache',type=Path,help='Private source-bound numerical checkpoints; never a substitute for source checks')
    args=parser.parse_args()
    try:
        guard_output(args.freeze,args.ledger,args.out)
    except Refused as exc:
        print(json.dumps({'status':'REFUSED','reason':str(exc),'conditional_static_screen_pass':False}))
        return 2
    context=None
    try:
        context=preflight(args.freeze,args.ledger)
        context['mesh_cache_dir']=args.mesh_cache
        if args.run:
            context['progress']=lambda row:print(json.dumps({'progress':row}),file=sys.stderr,flush=True)
        result=run_screen(context) if args.run else {'status':'PREFLIGHT ONLY; NO BOARD MESH RUN','board_sha256':context['board_sha256'],'scope':context['manifest']['scope'],'drc':context['drc']}
        code=0 if not args.run or result['conditional_static_screen_pass'] else 1
    except (Refused,KeyError,TypeError,ValueError,MemoryError,shapely.errors.GEOSException) as exc:
        result={'status':'REFUSED','reason':str(exc)or type(exc).__name__,'conditional_static_screen_pass':False}; code=2
        if context is not None:result.update(board_sha256=context['board_sha256'],freeze_sha256=context['freeze_sha256'],ledger_sha256=context['ledger_sha256'])
        if hasattr(exc,'geometry_reproduction'):result['geometry_reproduction']=exc.geometry_reproduction
        if hasattr(exc,'linear_solver_diagnostics'):result['linear_solver_diagnostics']=exc.linear_solver_diagnostics
        if context is not None:
            result['geometry_certificates']=context.get('geometry_certificates',{})
            result['mesh_cache_receipts']=context.get('mesh_cache_receipts',[])
            result['partial_runs_unqualified']=context.get('partial_runs',[])
            result['partial_runs_are_converged']=False
    # Repeat after a potentially long run in case a destination symlink changed.
    try:
        guard_output(args.freeze,args.ledger,args.out)
    except Refused as exc:
        print(json.dumps({'status':'REFUSED','reason':str(exc),'conditional_static_screen_pass':False}))
        return 2
    try:
        result=compact_result_evidence(result)
    except (Refused,TypeError,ValueError,KeyError) as exc:
        # An unverifiable evidence reference must never be published as a pass.
        # Leave both the full in-memory evidence and any existing output intact.
        refusal={'status':'REFUSED','reason':str(exc),'conditional_static_screen_pass':False,
                 'output_written':False}
        refusal.update({key:result[key] for key in ['board_sha256','freeze_sha256','ledger_sha256'] if key in result})
        print(json.dumps(refusal))
        return 2
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k in ['status','reason','board_sha256','scope','conditional_static_screen_pass']}))
    return code


if __name__=='__main__':
    raise SystemExit(main())
