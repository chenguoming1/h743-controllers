"""Source-bound adapter controls for the TP5/NRST checkpoint; no native/field solve."""
from pathlib import Path
import json
import tempfile
from verify_reference_runtime_indices import verify

ROOT = Path(__file__).resolve().parents[1]
D = ROOT/'ordinary-routing/candidate45'
O = ROOT/'ordinary-routing/candidate44'
S = ROOT/'checkpoint34-review'
receipt = D/'reference-runtime-index-proof.json'
args = [O/'f722-heli.kicad_pcb', D/'f722-heli.kicad_pcb',
        S/'comparison-35-to-34.json', O/'reference-snapshot', S/'snapshot']
result = verify(receipt, *args)
controls = []
for key, value in [('board_sha256','0'*64), ('raw_comparison_sha256','0'*64),
                   ('before_native_sha256','0'*64), ('critical_record_count',152),
                   ('negative_controls',[])]:
    changed = json.loads(receipt.read_text())
    changed[key] = value
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)/'changed.json'
        path.write_text(json.dumps(changed))
        try:
            verify(path, *args)
        except AssertionError:
            controls.append({'mutation': key, 'rejected': True})
        else:
            raise AssertionError('Accepted mutation: '+key)
result['binding_negative_controls'] = controls
(S/'owner-runtime-index-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
