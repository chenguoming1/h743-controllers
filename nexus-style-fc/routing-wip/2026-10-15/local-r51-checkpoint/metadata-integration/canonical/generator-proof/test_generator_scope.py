"""Pure-Python scope/idempotence test; native footprint validation is separate."""
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
source = (ROOT / 'before-pcbutil.py').read_text()
candidate = (ROOT / 'tools/pcbutil.py').read_text()
tree = ast.parse(candidate)
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
          and n.name == 'clear_main_u10_donor_metadata')
namespace = {}
exec(compile(ast.Module(body=[fn], type_ignores=[]), '<scoped-helper>', 'exec'), namespace)
helper = namespace[fn.name]

class Field:
    def __init__(self, name):
        self.name = name

class Footprint:
    def __init__(self):
        self.fields = {'Value': 'TPS70933DBVR', 'LCSC': 'C89347',
                       'Description': 'approved note', 'LCSC Part': 'C82942',
                       'Other': 'preserve'}
        self.description = 'ME6211C33M5G-N'
    def HasField(self, name):
        return name in self.fields
    def GetField(self, name):
        return Field(name)
    def Remove(self, field):
        del self.fields[field.name]
    def SetLibDescription(self, text):
        self.description = text

part = {'ref': 'U10', 'value': 'TPS70933DBVR', 'lcsc': 'C89347'}
fp = Footprint()
before = copy.deepcopy(fp.__dict__)
helper(fp, part, 'nexus-style-fc')
assert fp.fields == {k: v for k, v in before['fields'].items() if k != 'LCSC Part'}
assert fp.description == 'SOT-23-5 footprint; selected part TPS70933DBVR, LCSC C89347'
once = copy.deepcopy(fp.__dict__)
helper(fp, part, 'nexus-style-fc')
assert fp.__dict__ == once
cases = []
for project, delta in [('nexus-style-fc-power-module', {}), ('nexus-header-board', {}),
                       ('nexus-style-fc', {'ref': 'U11'}),
                       ('nexus-style-fc', {'value': 'different'}),
                       ('nexus-style-fc', {'lcsc': 'different'})]:
    fp = Footprint()
    before = copy.deepcopy(fp.__dict__)
    changed_part = {**part, **delta}
    helper(fp, changed_part, project)
    assert fp.__dict__ == before
    cases.append({'project': project, 'part': changed_part, 'unchanged': True})
lines = candidate.splitlines(keepends=True)
block = ''.join(lines[fn.lineno-1:fn.end_lineno])
recovered = candidate.replace('\n\n' + block, '', 1).replace(
    '        clear_main_u10_donor_metadata(fp, part, project)\n', '')
assert recovered == source
report = {'status': 'PASS: exact main-U10 scope and idempotence; native checks separate',
          'candidate_sha256': hashlib.sha256(candidate.encode()).hexdigest(),
          'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
          'only_helper_and_single_invocation_added': True,
          'actual_selected_fields_unchanged': True, 'unaffected_cases': cases}
(ROOT / 'scope-test-result.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
