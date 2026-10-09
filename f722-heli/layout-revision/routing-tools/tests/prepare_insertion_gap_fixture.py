#!/usr/bin/env python3
"""Extract the exact candidate06 D2.1 guard for an isolated insertion check."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'model-candidate06-diagnostic/model.json'
OUT = ROOT / 'tests/insertion-gap-fixture'
source = SOURCE.read_bytes()
model = json.loads(source)
expected_board = '221ee94c9a936be959dc89b7c7050a20b5f795af6a86921fb44c01a2e9dbecc3'
assert model['board_sha256'] == expected_board
label = 'bb8b4c11-7c2b-4747-9ddb-b3d98cb0dec9:copper'
guards = [g for g in model['guards'] if g['label'] == label and g['layer'] == 'F.Cu']
assert len(guards) == 1 and guards[0]['kind'] == 'foreign' and guards[0]['owners'] == ['LED_RED_K']
layers = model['layers']
dsn = ['(pcb "native-insertion-gap-control"',
       '(parser (string_quote ") (space_in_quoted_tokens on) (host_cad "KiCad") (host_version "10.0.6"))',
       '(resolution mm 100000) (unit mm) (structure']
dsn += [f'(layer {l} (type signal) (property (index {i})))' for i, l in enumerate(layers)]
dsn += ['(boundary (rect pcb 38 -25 44 -18))',
        '(via "VIA_450_200") (rule (width 0.127) (clearance 0.127)))',
        '(placement) (library (padstack "VIA_450_200"']
dsn += [f'(shape (circle {l} 0.45))' for l in layers]
dsn += ['(attach off)))', '(network (net "D2_A" (pins)) (net "LED_RED_K" (pins))',
        '(class "ordinary" "D2_A" "LED_RED_K" (circuit (use_via "VIA_450_200"))',
        '(rule (width 0.127) (clearance 0.127))))', '(wiring))']
dsn_bytes = ('\n'.join(dsn) + '\n').encode()
fixture = {
    'schema': 'f722-insertion-gap-fixture/v1', 'fixture_only': True,
    'source_model_sha256': hashlib.sha256(source).hexdigest(),
    'source_board_sha256': expected_board,
    'dsn_sha256': hashlib.sha256(dsn_bytes).hexdigest(),
    'guards': guards, 'contacts': [],
    'trace_net': 'D2_A', 'layer': 'F.Cu', 'trace_half_width': 6350,
    'nominal_clearance': 12700,
    'segment_mm': [[41.16554, 20.84683], [41.16554, 21.88273]],
    'native_guard_max_x_mm': max(p[0] for polygon in guards[0]['polygons'] for p in polygon['outer']),
    'shifts_engine_units': list(range(33)) + [50, 100, 1000],
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'model.json').write_text(json.dumps(fixture, indent=2) + '\n')
(OUT / 'routing.dsn').write_bytes(dsn_bytes)
print(json.dumps({'fixture': str(OUT), 'guard_convex_pieces': len(guards[0]['convex']),
                  'source_model_sha256': fixture['source_model_sha256']}))
