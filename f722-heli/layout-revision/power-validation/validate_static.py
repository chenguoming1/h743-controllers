#!/usr/bin/env python3
"""Source-bound, capped prototype DC screen. The default CLI is preflight only."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import numpy as np
import scipy
import shapely
import sexpdata
from copper_fem import Mesh, Limits, Refused, copper_material, native_geometry, contact_geometry
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
    if not manifest.get('saved_fill_verified') or not manifest.get('checks_run_on_frozen_board'):
        raise Refused('Fresh saved-fill/check evidence is missing')
    required = ['board', 'geometry', 'connectivity', 'parts', 'parity', 'physical', 'drc_normal', 'drc_all_track']
    files = {}
    for name in required:
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
        native_pads = {x['key']: x for x in geometry['objects'] if x['kind']=='pad' and x.get('net')==network['net']}
        for spec in network['contacts'].values():
            if spec['pad'] not in native_pads or spec['layer'] not in geometry['copper_layers']:
                raise Refused('Contact refers to an absent pad/net/layer')
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


def run_screen(context):
    ledger = context['ledger']; geometry = context['geometry']; material = context['material']
    limits = Limits(**ledger.get('limits', {}))
    runs = []
    def make_mesh(network, spacing):
        domains, pads, barrels = native_geometry(geometry, network['net'])
        contacts = {node: (spec['layer'], contact_geometry(pads,spec['pad'],spec['layer']))
                    for node,spec in network['contacts'].items()}
        return Mesh(domains, contacts, spacing, material['sheet_ohm'], material['thickness_mm'],
                    barrels, context['stackup']['layer_z_mm'], material['plating_mm'], limits)
    # One network mesh is alive at a time. The compact port matrices are kept;
    # reconstruct only for direct loaded-field checks after circuit coupling.
    for spacing in ledger['mesh_spacings_mm']:
        blocks = []; unit_by_name = {}; loop_legs = {}
        for network in ledger['networks']:
            net = network['net']; mesh = make_mesh(network,spacing)
            block = mesh.impedance(); block['net'] = net; blocks.append(block)
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
    return {'schema':'f722-scoped-static-result/v1','board_sha256':context['board_sha256'],
            'freeze_sha256':context['freeze_sha256'],'ledger_sha256':context['ledger_sha256'],
            'scope':context['manifest']['scope'],'conditional_static_screen_pass':bool(passed),
            'scope_is_final_board':context['manifest']['scope']=='final-board','thermal_or_flight_qualification':False,
            'material':material,'stackup':context['stackup'],'drc':context['drc'],
            'impedance_sensitivity':sensitivity,'voltage_margin_checks':margins,'resistance_margin_checks':resistance_margins,
            'runs':runs,'software':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'shapely':shapely.__version__,
              'source_sha256':{name:sha256(Path(__file__).parent/name) for name in ['copper_fem.py','dc_circuit.py','validate_static.py']}},
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
    args=parser.parse_args()
    try:
        guard_output(args.freeze,args.ledger,args.out)
    except Refused as exc:
        print(json.dumps({'status':'REFUSED','reason':str(exc),'conditional_static_screen_pass':False}))
        return 2
    try:
        context=preflight(args.freeze,args.ledger)
        result=run_screen(context) if args.run else {'status':'PREFLIGHT ONLY; NO BOARD MESH RUN','board_sha256':context['board_sha256'],'scope':context['manifest']['scope'],'drc':context['drc']}
        code=0 if not args.run or result['conditional_static_screen_pass'] else 1
    except (Refused,KeyError,TypeError,ValueError) as exc:
        result={'status':'REFUSED','reason':str(exc),'conditional_static_screen_pass':False}; code=2
    # Repeat after a potentially long run in case a destination symlink changed.
    try:
        guard_output(args.freeze,args.ledger,args.out)
    except Refused as exc:
        print(json.dumps({'status':'REFUSED','reason':str(exc),'conditional_static_screen_pass':False}))
        return 2
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k in ['status','reason','board_sha256','scope','conditional_static_screen_pass']}))
    return code


if __name__=='__main__':
    raise SystemExit(main())
