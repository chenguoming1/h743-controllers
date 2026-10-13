import ast,difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;original=Path('@ORIGINAL_EXPORTER@');old=original.read_text();assert hashlib.sha256(original.read_bytes()).hexdigest()=='d571a9763c3134d1995bf8a192cfdddcb4991dc637f9a20bfd7119877a6ecdfa'
function='''def match_drill_features(expected, actual):
    """Unique drill census match at the emitted metric 0.001 mm precision.

    Coordinates may differ by half one output unit. The additional bound is
    only 16 binary64 ulps for native unit conversion/rotated-slot arithmetic;
    it is not a drill, placement, or fabrication tolerance.
    """
    require(len(expected) == len(actual), 'Drill feature census mismatch')
    half_grid = Decimal('0.0005')

    def canonical(item):
        plating, kind, diameter, *coords = item
        require(kind in ('round', 'slot'), 'Unknown drill feature kind')
        require(len(coords) == (2 if kind == 'round' else 4), 'Malformed drill coordinates')
        if kind == 'slot':
            ends = sorted([coords[:2], coords[2:]])
            coords = ends[0] + ends[1]
        values = [Decimal(str(v)) for v in [diameter, *coords]]
        require(all(v.is_finite() for v in values), 'Non-finite drill feature')
        return (plating, kind, values[0]), values[1:]

    source = [canonical(item) for item in expected]
    used, maximum_delta, maximum_roundoff = set(), Decimal(0), Decimal(0)
    for item in actual:
        key, coordinates = canonical(item)
        matches = []
        for index, (source_key, source_coordinates) in enumerate(source):
            if key != source_key:
                continue
            deltas = [abs(a-b) for a, b in zip(coordinates, source_coordinates)]
            roundoff = [Decimal(str(16 * math.ulp(max(1.0, abs(float(a)), abs(float(b))))))
                        for a, b in zip(coordinates, source_coordinates)]
            if all(d <= half_grid+r for d, r in zip(deltas, roundoff)):
                matches.append((index, deltas, roundoff))
        require(len(matches) == 1, 'Drill feature has missing or ambiguous native match')
        index, deltas, roundoff = matches[0]
        require(index not in used, 'Duplicate exported drill feature')
        used.add(index)
        maximum_delta = max(maximum_delta, *deltas)
        maximum_roundoff = max(maximum_roundoff, *roundoff)
    require(len(used) == len(source), 'Native drill feature left unmatched')
    return {'unique_one_to_one_feature_match': True,
            'coordinate_resolution_mm': 0.001,
            'coordinate_half_grid_mm': float(half_grid),
            'maximum_absolute_coordinate_delta_mm': float(maximum_delta),
            'maximum_binary64_roundoff_bound_mm': float(maximum_roundoff),
            'plating_kind_diameter_exact': True}


'''
new=old.replace('from datetime import datetime, timezone\n','from datetime import datetime, timezone\nfrom decimal import Decimal\n');new=new.replace('def parse_drill(path, plating):\n',function+'def parse_drill(path, plating):\n')
needle="        require(Counter(map(drill_key, features)) == Counter(map(drill_key, expected)), f'{plating} native/Excellon hole or slot mismatch at 0.001 mm')"
assert old.count(needle)==1;new=new.replace(needle,'        precision_match = match_drill_features(expected, features)')
new=new.replace("'native_coordinate_and_size_match_at_0_001mm': True}","'native_coordinate_and_size_match_at_0_001mm': True,\n                                            'precision_aware_matching': precision_match}")
ast.parse(new);(P/'native_export.py').write_text(new);(P/'native_export.py.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/f722-heli/layout-revision/export-tools/native_export.py',tofile='b/f722-heli/layout-revision/export-tools/native_export.py')))
oldtree=ast.parse(old);newtree=ast.parse(new);oldnodes={n.name:ast.dump(n) for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};newnodes={n.name:ast.dump(n) for n in newtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};changed=[n for n in oldnodes if oldnodes[n]!=newnodes[n]];assert changed==['verify_fabrication'];assert set(newnodes)-set(oldnodes)=={'match_drill_features'}
report={'schema':'f722-drill-precision-proposed-patch/v1','status':'PROPOSED_SEPARATE_VERSION_NOT_FINAL_EXPORT_EXECUTED','original_path':str(original),'original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'patched_sha256':hashlib.sha256(new.encode()).hexdigest(),'patch_sha256':hashlib.sha256((P/'native_export.py.patch').read_bytes()).hexdigest(),'changed_existing_functions':changed,'added_function':'match_drill_features','final_receipt_source_native_checks_AST_unchanged':True,'source_CAD_parts_modified':False,'old_tool_modified':False,'finalrelease':False};(P/'PATCH-PROVENANCE.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2))
