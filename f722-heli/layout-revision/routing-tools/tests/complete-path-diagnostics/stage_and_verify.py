"""Stage diagnostics only; never write the live sources or build outputs."""
from pathlib import Path
import difflib
import hashlib
import json

stage = Path(__file__).resolve().parent
root = stage.parent
relative = Path('src/app/freerouting/autoroute/InsertFoundConnectionAlgo.java')
live = root / relative

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def identity():
    paths = sorted((root / 'src').rglob('*.java'))
    paths += sorted((root / 'build').rglob('*.class'))
    paths += [root / 'vendor/freerouting-2.1.0.jar', root / 'run_local.sh']
    return {str(path.relative_to(root)): digest(path) for path in paths}

before = identity()
original = live.read_text()
helpers = '''  /** Snapshot only: a located path is neither inserted copper nor a native validation result. */
  private Object diagnosticEndpoint(Item item, int layer, Point point)
  {
    java.util.Map<String,Object> endpoint = new java.util.LinkedHashMap<>();
    endpoint.put("layer_index",layer);
    endpoint.put("layer",board.layer_structure.arr[layer].name);
    endpoint.put("point_mm",diagnosticPoint(point));
    if (item != null)
    {
      endpoint.put("engine_id",item.get_id_no());
      endpoint.put("class",item.getClass().getName());
      endpoint.put("fixed",item.get_fixed_state().name());
      if (item instanceof ObstacleArea area) endpoint.put("label",area.name);
      if (item instanceof NativePadContactArea contact)
      {
        endpoint.put("native_uuid",contact.nativeId);
        endpoint.put("native_group",contact.nativeGroup);
        endpoint.put("contact_label",contact.name);
      }
    }
    return endpoint;
  }

  private Object diagnosticViaTransition(int before_trace_index, Point point, int from_layer, int to_layer)
  {
    java.util.Map<String,Object> transition = new java.util.LinkedHashMap<>();
    transition.put("before_trace_index",before_trace_index);
    transition.put("point_mm",diagnosticPoint(point));
    transition.put("from_layer_index",from_layer);
    transition.put("from_layer",board.layer_structure.arr[from_layer].name);
    transition.put("to_layer_index",to_layer);
    transition.put("to_layer",board.layer_structure.arr[to_layer].name);
    return transition;
  }

  /** Dump the whole target-to-start connection before any forced insertion can refuse. */
  private void diagnosticLocatedConnection(LocateFoundConnectionAlgo connection)
  {
    if (!"1".equals(System.getenv("F722_INSERT_DIAGNOSTICS"))) return;
    java.util.Map<String,Object> record = new java.util.LinkedHashMap<>();
    record.put("stage","located_connection");
    record.put("status","located_only");
    record.put("net",board.rules.nets.get(ctrl.net_no).name);
    record.put("net_no",ctrl.net_no);
    record.put("traversal","target_to_start");
    java.util.List<Object> traces = new java.util.ArrayList<>();
    java.util.List<Object> transitions = new java.util.ArrayList<>();
    Point target_point = null;
    Point start_point = null;
    int previous_layer = connection.target_layer;
    int trace_index = 0;
    for (LocateFoundConnectionAlgoAnyAngle.ResultItem trace : connection.connection_items)
    {
      Point first = trace.corners.length == 0 ? null : trace.corners[0];
      Point last = trace.corners.length == 0 ? null : trace.corners[trace.corners.length - 1];
      if (trace_index == 0) target_point = first;
      java.util.Map<String,Object> polyline = new java.util.LinkedHashMap<>();
      polyline.put("trace_index",trace_index);
      polyline.put("layer_index",trace.layer);
      polyline.put("layer",board.layer_structure.arr[trace.layer].name);
      polyline.put("half_width_mm",ctrl.trace_half_width[trace.layer] / 100000.0);
      java.util.List<Object> corners = new java.util.ArrayList<>();
      for (Point point : trace.corners) corners.add(diagnosticPoint(point));
      polyline.put("requested_corners_mm",corners);
      traces.add(polyline);
      if (previous_layer != trace.layer)
        transitions.add(diagnosticViaTransition(trace_index,first,previous_layer,trace.layer));
      previous_layer = trace.layer;
      start_point = last;
      ++trace_index;
    }
    if (previous_layer != connection.start_layer)
      transitions.add(diagnosticViaTransition(trace_index,start_point,previous_layer,connection.start_layer));
    record.put("target_endpoint",diagnosticEndpoint(connection.target_item,connection.target_layer,target_point));
    record.put("start_endpoint",diagnosticEndpoint(connection.start_item,connection.start_layer,start_point));
    record.put("traces",traces);
    record.put("via_transitions",transitions);
    System.out.println("INSERT_DIAGNOSTIC " + new com.google.gson.Gson().toJson(record));
    System.out.flush();
  }

'''
anchor = '  /**\n   * Creates a new instance of InsertFoundConnectionAlgo\n'
assert original.count(anchor) == 1
constructor = '    InsertFoundConnectionAlgo new_instance = new InsertFoundConnectionAlgo(p_board, p_ctrl);\n'
call = '    new_instance.diagnosticLocatedConnection(p_connection);\n'
assert original.count(constructor) == 1
updated = original.replace(anchor, helpers + anchor).replace(constructor, constructor + call)

# The baseline body, including every predicate, mutation and existing diagnostic,
# is byte-for-byte restored after removing only the new helpers and call.
assert updated.replace(helpers, '', 1).replace(call, '', 1) == original
body = updated[updated.index('  public static InsertFoundConnectionAlgo get_instance'):]
assert body.index(call) < body.index('for (LocateFoundConnectionAlgoAnyAngle.ResultItem')
assert body.index(call) < body.index('new_instance.insert_via(')
assert body.index(call) < body.index('new_instance.insert_trace(')

# Bounded lexical check: all helper-side collection mutations target fresh local
# JSON containers; route/board fields never appear on an assignment LHS.
import re
assert not re.search(r'(?:connection|trace|item|board|ctrl)\.[\w.\[\]]+\s*(?:=(?!=)|\+=|-=|\+\+|--)', helpers)
mutators = re.findall(r'\b(\w+)\.(put|add|remove|clear|set|insert|normalize|sort)\s*\(', helpers)
assert all(receiver in {'endpoint', 'transition', 'record', 'polyline', 'corners', 'traces', 'transitions'}
           and method in {'put', 'add'} for receiver, method in mutators)
assert not re.search(r'\b(insert_via|insert_trace|ForcedViaAlgo|set_fixed_state|is_obstacle|is_trace_obstacle|cutout)\b', helpers)

baseline = stage / 'baseline' / relative
staged = stage / 'staged' / relative
baseline.parent.mkdir(parents=True, exist_ok=True)
staged.parent.mkdir(parents=True, exist_ok=True)
baseline.write_text(original)
staged.write_text(updated)
patch = ''.join(difflib.unified_diff(original.splitlines(True), updated.splitlines(True),
               fromfile='a/' + str(relative), tofile='b/' + str(relative)))
(stage / 'complete-located-connection.patch').write_text(patch)
after = identity()
assert before == after, 'Live source/build identity changed during staging'
(stage / 'baseline-identity.json').write_text(json.dumps(before, indent=2) + '\n')
verification = {
    'live_identity_unchanged': before == after,
    'baseline_source_sha256': before[str(relative)],
    'staged_source_sha256': digest(staged),
    'existing_body_exactly_preserved': True,
    'new_call_before_any_insertion': True,
    'helper_mutations_only_fresh_json_containers': True,
    'java_compiled': False, 'engine_run': False, 'native_validation_run': False,
    'source_files_hashed': len(list((root / 'src').rglob('*.java'))),
    'build_classes_hashed': len(list((root / 'build').rglob('*.class'))),
}
(stage / 'static-verification.json').write_text(json.dumps(verification, indent=2) + '\n')
print(json.dumps(verification, indent=2))
