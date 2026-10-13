"""Host-only explicit proof of the proposed matcher's arithmetic boundary."""
import ast, hashlib, json, math, sys
from decimal import Decimal
from pathlib import Path

patch, fixture, output = map(Path, sys.argv[1:])
class GateError(Exception): pass
def require(condition, message):
    if not condition: raise GateError(message)
tree = ast.parse(patch.read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'match_drill_features'], type_ignores=[]), str(patch), 'exec'))
data = json.loads(fixture.read_text())
rows = [r for section in data['drills'].values() for r in section['all_matches']]
maximum = max(((16 * math.ulp(max(1.0, abs(float(a)), abs(float(b)))), r, index)
              for r in rows for index, (a, b) in enumerate(zip(r['exact_native_feature'][3:], r['actual_export_feature'][3:]), 3)), key=lambda item: item[0])
bound_float, row, index = maximum
source = list(row['exact_native_feature'])
base = Decimal(str(source[index]))
half = Decimal('0.0005')
bound = Decimal(str(bound_float))
threshold = base + half + bound
# Find adjacent binary64 coordinates bracketing the actual predicate boundary.
inside = float(threshold)
while Decimal(str(inside)) > threshold: inside = math.nextafter(inside, -math.inf)
outside = math.nextafter(inside, math.inf)
assert Decimal(str(inside)) <= threshold < Decimal(str(outside))
inside_feature = source.copy(); inside_feature[index] = inside
outside_feature = source.copy(); outside_feature[index] = outside
positive = match_drill_features([source], [inside_feature])
try: match_drill_features([source], [outside_feature])
except GateError as exc: rejection = str(exc)
else: raise AssertionError('Just-outside-bound control unexpectedly accepted')
result = {
    'schema': 'f722-proposed-drill-matcher-explicit-boundary/v1',
    'proposed_tool_sha256': hashlib.sha256(patch.read_bytes()).hexdigest(),
    'actual_fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
    'independent_decimal_diagnostic_extra_epsilon_mm': '0',
    'proposed_reusable_matcher_arithmetic_rule': '16 * math.ulp(max(1.0, abs(actual), abs(native))) per coordinate',
    'maximum_added_arithmetic_bound_over_actual_331_features_mm': str(bound),
    'maximum_total_coordinate_allowance_over_actual_331_features_mm': str(half + bound),
    'half_grid_mm': str(half), 'selected_actual_source_uuid': row['uuid'],
    'selected_coordinate_index': index, 'native_coordinate_mm': str(base),
    'last_accepted_binary64_coordinate_mm': str(inside),
    'last_accepted_coordinate_delta_mm': str(Decimal(str(inside)) - base),
    'first_rejected_binary64_coordinate_mm': str(outside),
    'first_rejected_coordinate_delta_mm': str(Decimal(str(outside)) - base),
    'rejected_excess_over_total_allowance_mm': str(Decimal(str(outside)) - threshold),
    'adjacent_binary64_values': math.nextafter(inside, math.inf) == outside,
    'inside_boundary_positive_result': positive,
    'just_outside_boundary_correctly_rejected': True, 'rejection': rejection,
    'not_a_physical_or_process_tolerance': True, 'finalrelease': False,
    'native_export_commands_executed': False,
}
output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, indent=2, sort_keys=True))
