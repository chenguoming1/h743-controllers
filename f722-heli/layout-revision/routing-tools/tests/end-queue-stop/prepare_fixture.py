#!/usr/bin/env python3
"""Prepare a tiny synthetic LocalRouter model; never read or modify a native PCB."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
OUT = ROOT / "fixture"
OUT.mkdir(exist_ok=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

# Reuse the already audited two-contact synthetic state fixture, with six layers
# because the production LocalRouter intentionally expects the real stack count.
seed = PROJECT / "tests/failed-search-state/fixture/model.json"
model = json.loads(seed.read_text())
layers = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]
dsn = '''(pcb "end-queue-stop-control"
(parser (string_quote ") (space_in_quoted_tokens on) (host_cad "KiCad") (host_version "10.0.6"))
(resolution mm 100000) (unit mm)
(structure
'''
dsn += "\n".join(f'(layer {layer} (type signal) (property (index {i})))' for i, layer in enumerate(layers))
dsn += '''
(boundary (rect pcb 0 -10 10 0))
(via "VIA_450_200") (rule (width 0.127) (clearance 0.127)))
(placement)
(library (padstack "VIA_450_200"
'''
dsn += " ".join(f'(shape (circle {layer} 0.45))' for layer in layers)
dsn += ''' (attach off)))
(network (net "TEST" (pins)) (net "FIXED_OTHER" (pins))
(class "ordinary" "TEST" "FIXED_OTHER" (circuit (use_via "VIA_450_200")) (rule (width 0.127) (clearance 0.127))))
(wiring
(wire (path F.Cu 0.127 2 -2 3 -2) (net "FIXED_OTHER") (type fix))
(via "VIA_450_200" 3 -2 (net "FIXED_OTHER") (type fix))))
'''
(OUT / "routing.dsn").write_text(dsn)
for filename, text in [("synthetic-board-identity.txt", "Synthetic test identity only; this is not a native PCB.\n"),
                       ("synthetic-native-identity.txt", "Synthetic native-export identity only; no production layout.\n")]:
    (OUT / filename).write_text(text)
model.update({
    "schema": "synthetic-end-queue-stop/v1", "synthetic_only": True,
    "purpose": "One successful connection followed by natural queue exhaustion; fixed trace, via, contacts and guards must survive.",
    "seed_model": str(seed), "seed_model_sha256": sha(seed),
    "dsn_sha256": sha(OUT / "routing.dsn"),
    "physical_board": str(OUT / "synthetic-board-identity.txt"),
    "board_sha256": sha(OUT / "synthetic-board-identity.txt"),
    "physical_native": str(OUT / "synthetic-native-identity.txt"),
    "native_sha256": sha(OUT / "synthetic-native-identity.txt"),
    "ordinary_nets": ["TEST"], "aliases": {"TEST": "TEST", "FIXED_OTHER": "FIXED_OTHER"},
    "support_ready": True,
    "adapter_sources": {str(p): sha(p) for p in sorted((PROJECT / "src").rglob("*.java"))},
})
(OUT / "model.json").write_text(json.dumps(model, indent=2) + "\n")
print(OUT)
