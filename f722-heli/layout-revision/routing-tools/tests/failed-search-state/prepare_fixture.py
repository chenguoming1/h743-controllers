#!/usr/bin/env python3
"""Create a two-pad synthetic state-lifecycle fixture, without any native PCB."""
import hashlib
import json
from pathlib import Path

out = Path(__file__).resolve().parent / 'fixture'
out.mkdir(exist_ok=True)
dsn = '''(pcb "failed-search-state-control"
(parser (string_quote ") (space_in_quoted_tokens on) (host_cad "KiCad") (host_version "10.0.6"))
(resolution mm 100000) (unit mm)
(structure
(layer F.Cu (type signal) (property (index 0)))
(layer B.Cu (type signal) (property (index 1)))
(boundary (rect pcb 0 -10 10 0))
(via "VIA_450_200") (rule (width 0.127) (clearance 0.127)))
(placement)
(library (padstack "VIA_450_200" (shape (circle F.Cu 0.45)) (shape (circle B.Cu 0.45)) (attach off)))
(network (net "TEST" (pins))
(class "ordinary" "TEST" (circuit (use_via "VIA_450_200")) (rule (width 0.127) (clearance 0.127))))
(wiring))
'''
contacts = []
guards = []
for label, x in [('SYNTHETIC_A', 1), ('SYNTHETIC_B', 8)]:
    polygon = [[x, 5], [x + .25, 5], [x + .25, 5.25], [x, 5.25]]
    contacts.append({'uuid': label, 'key': label, 'layer': 'F.Cu', 'net': 'TEST',
                     'owners': ['TEST'], 'plated': False, 'native_group': label,
                     'native_group_multi': False, 'convex': [polygon]})
    guards.append({'label': label + ':copper', 'layer': 'F.Cu', 'kind': 'foreign',
                   'owners': ['TEST'], 'clearance': .127, 'convex': [polygon]})
model = {'schema': 'synthetic-failed-search-state/v1', 'synthetic_only': True,
         'dsn_sha256': hashlib.sha256(dsn.encode()).hexdigest(), 'contacts': contacts,
         'guards': guards, 'purpose': 'Temporary search-room lifecycle only; no routing deliverable or native PCB.'}
(out / 'routing.dsn').write_text(dsn)
(out / 'model.json').write_text(json.dumps(model, indent=2) + '\n')
print(out)
