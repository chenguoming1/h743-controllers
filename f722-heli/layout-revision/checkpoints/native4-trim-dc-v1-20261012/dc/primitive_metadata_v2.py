"""Exact metadata helpers for a future leased official-native sidecar.

No native import or execution at module import. Custom geometry is preserved as
actual stored polygons; unsupported primitives refuse rather than approximate.
"""
from decimal import Decimal
import json
import re


def require(value, message):
    if not value:
        raise RuntimeError(message)


def iu(value):
    exact = Decimal(str(value)) * 1000000
    require(exact == exact.to_integral_value(), "Source coordinate is not exact native IU")
    return int(exact)


def xy(point):
    return [int(point.x), int(point.y)]


def polygon_rows(shape):
    return [{"outer": [xy(shape.Outline(i).CPoint(j)) for j in range(shape.Outline(i).PointCount())],
             "holes": [[xy(shape.Hole(i, h).CPoint(j)) for j in range(shape.Hole(i, h).PointCount())]
                       for h in range(shape.HoleCount(i))]} for i in range(shape.OutlineCount())]


def millimetres(rows):
    return [{"outer": [[x/1e6, y/1e6] for x, y in row['outer']],
             "holes": [[[x/1e6, y/1e6] for x, y in hole] for hole in row['holes']]} for row in rows]


def canonical_ring(points):
    points = list(map(tuple, points))
    if len(points) > 1 and points[0] == points[-1]:
        points.pop()
    require(len(points) >= 3, "Degenerate stored polygon")
    variants = []
    for ring in [points, points[::-1]]:
        first = min(range(len(ring)), key=lambda i: ring[i])
        variants.append(tuple(ring[first:] + ring[:first]))
    return min(variants)


def child(form, name, optional=False):
    matches = [x for x in form[1:] if isinstance(x, list) and x and x[0] == name]
    require(len(matches) == 1 or (optional and not matches), "Missing/duplicate source field: " + name)
    return matches[0] if matches else None


def parse_form(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)
    stack, root = [], None
    for token in tokens:
        if token == '(':
            form = []
            if stack:
                stack[-1].append(form)
            else:
                require(root is None, "Multiple source forms")
                root = form
            stack.append(form)
        elif token == ')':
            require(stack, "Unbalanced source form")
            stack.pop()
        else:
            require(stack, "Source atom outside form")
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    require(not stack and root is not None, "Incomplete source form")
    return root


def source_pad_forms(text):
    result = {}
    for match in re.finditer(r'\(pad\s', text):
        depth, quoted, escaped, end = 0, False, False, None
        for index in range(match.start(), len(text)):
            char = text[index]
            if quoted:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        require(end is not None, "Unterminated source pad")
        raw = text[match.start():end]
        form = parse_form(raw)
        uid = child(form, 'uuid')[1]
        require(uid not in result, "Duplicate PCB source pad UUID")
        result[uid] = {"form": form, "raw": raw}
    return result


def source_custom(form):
    require(form[3] == 'custom', "Custom pad source shape differs")
    require(child(form, 'padstack', optional=True) is None, "Custom per-layer padstack needs explicit source parser")
    options = child(form, 'options')
    anchor = child(options, 'anchor')[1]
    require(anchor in {'circle', 'rect'}, "Unsupported custom anchor")
    rows = []
    for primitive in child(form, 'primitives')[1:]:
        require(isinstance(primitive, list) and primitive[0] == 'gr_poly', "Unsupported custom primitive; no omission/approximation")
        require(iu(child(primitive, 'width')[1]) == 0 and child(primitive, 'fill')[1] == 'yes',
                "Only exact zero-width filled custom polygons are supported")
        points = child(primitive, 'pts')[1:]
        require(all(p[0] == 'xy' and len(p) == 3 for p in points), "Unsupported custom polygon point")
        rows.append([[iu(p[1]), iu(p[2])] for p in points])
    require(rows, "Empty custom primitive list")
    return {"anchor": anchor, "size_IU": [iu(x) for x in child(form, 'size')[1:]], "polygons_IU": rows}


def merged_custom_polygon(p, item, layer, stored_polygons):
    """Supported native output-parameter accessor, guarded by exact source data.

    The shared_ptr<PCB_SHAPE> vector is not wrapped by this KiCad Python build.
    Only the observed single exact polygon case is supported; no primitive is
    omitted, reconstructed as a curve, or accepted through approximate equality.
    """
    require(len(stored_polygons) == 1, "Multiple custom primitives need explicit reviewed union metadata")
    merged = p.SHAPE_POLY_SET()
    item.MergePrimitivesAsPolygon(layer, merged, p.ERROR_INSIDE)
    local = polygon_rows(merged)
    require(len(local) == 1 and not local[0]['holes'] and
            canonical_ring(local[0]['outer']) == canonical_ring(stored_polygons[0]),
            "Native merged custom polygon differs from exact PCB source")
    return merged, local


def native_rotation_matrix(p, angle):
    shape = p.SHAPE_POLY_SET()
    shape.NewOutline()
    for x, y in [(0, 0), (1, 0), (0, 1)]:
        shape.Append(x, y)
    shape.Rotate(angle)
    points = polygon_rows(shape)[0]['outer']
    require(points[0] == [0, 0] and len(points) == 3, "Native rotation basis differs")
    a, b = points[1], points[2]
    require(all(v in {-1, 0, 1} for v in a+b) and sum(v*v for v in a) == sum(v*v for v in b) == 1 and
            a[0]*b[1] - a[1]*b[0] == 1, "Only exact orthogonal native rotation is supported")
    return [a, b]


def transform(point, matrix, origin):
    return [origin[0] + point[0]*matrix[0][0] + point[1]*matrix[1][0],
            origin[1] + point[0]*matrix[0][1] + point[1]*matrix[1][1]]


def capture_pad(p, item, footprint, board, layers, original, source_form):
    uid = item.m_Uuid.AsString()
    position = xy(item.GetPosition())
    angle = item.GetOrientationDegrees()
    require(angle % 90 == 0, "Nonorthogonal pad needs a separately reviewed exact transform")
    require(uid == original['uuid'] and footprint.m_Uuid.AsString() == original['footprint_uuid'] and
            item.GetNumber() == original['number'] and footprint.GetReference() == original['ref'] and
            item.GetNetname() == original['net'], "Actual pad UUID/name/net differs")
    require(item.GetAttribute() == original['attribute'] and
            [board.GetLayerName(layer) for layer in item.GetLayerSet().Seq()] == original['all_layers'],
            "Actual pad plating/physical layer declaration differs")
    hole = item.GetEffectiveHoleShape()
    actual_drill = ({'start': [v/1e6 for v in xy(hole.GetStart())],
                     'end': [v/1e6 for v in xy(hole.GetEnd())], 'width': hole.GetWidth()/1e6}
                    if hole and hole.GetWidth() > 0 else None)
    expected_drill = ({key: original['drill'][key] for key in ['start', 'end', 'width']}
                      if original.get('drill') else None)
    require(actual_drill == expected_drill, "Actual physical pad drill primitive differs")
    require([x/1e6 for x in position] == original['xy'] and angle == original['angle'] and
            [x/1e6 for x in xy(item.GetSize())] == original['size'] and
            [x/1e6 for x in xy(item.GetOffset())] == original['offset'], "Actual pad pose/default size/offset differs")
    matrix = native_rotation_matrix(p, item.GetOrientation())
    constants = {'circle': p.PAD_SHAPE_CIRCLE, 'rectangle': p.PAD_SHAPE_RECTANGLE, 'oval': p.PAD_SHAPE_OVAL,
                 'roundrect': p.PAD_SHAPE_ROUNDRECT, 'custom': p.PAD_SHAPE_CUSTOM,
                 'trapezoid': p.PAD_SHAPE_TRAPEZOID, 'chamfered_rect': p.PAD_SHAPE_CHAMFERED_RECT}
    by_code = {int(value): name for name, value in constants.items()}
    actual_layers = {board.GetLayerName(layer) for layer in layers if item.IsOnLayer(layer) and item.FlashLayer(layer)}
    require(actual_layers == set(original['copper']), "Actual flashed copper layer inventory differs")
    captured = {}
    for layer in layers:
        name = board.GetLayerName(layer)
        if name not in original['copper']:
            continue
        require(item.IsOnLayer(layer) and item.FlashLayer(layer), "Actual flashed layer differs")
        code = int(item.GetShape(layer))
        require(code == original['shape_by_layer'][name] and code in by_code, "Actual per-layer shape differs")
        size, offset = xy(item.GetSize(layer)), xy(item.GetOffset(layer))
        require(offset == [0, 0], "Nonzero copper offset needs an explicit reviewed transform")
        shape_name = by_code[code]
        require(shape_name in {'circle', 'rectangle', 'oval', 'roundrect', 'custom'}, "Unsupported pad shape preserved as blocker")
        raw_outer, raw_inner = p.SHAPE_POLY_SET(), p.SHAPE_POLY_SET()
        item.TransformShapeToPolygon(raw_outer, layer, 0, 10, p.ERROR_OUTSIDE)
        item.TransformShapeToPolygon(raw_inner, layer, 0, 10, p.ERROR_INSIDE)
        require(millimetres(polygon_rows(raw_outer)) == original['copper'][name] and
                millimetres(polygon_rows(raw_inner)) == original['inside'][name], "Original pad contours were not exactly reproduced")
        row = {'shape': shape_name, 'shape_code': code, 'size_IU': size, 'offset_IU': offset,
               'copper_center_IU': position, 'corner_radius_IU': None, 'custom': None,
               'original_inner_and_outer_contours_reproduced': True}
        if shape_name == 'roundrect':
            radius = item.GetRoundRectCornerRadius(layer)
            require(type(radius) is int and radius > 0 and 2*radius <= min(size), "Invalid per-layer integer roundrect radius")
            row['corner_radius_IU'] = radius
            row['corner_radius_ratio'] = item.GetRoundRectRadiusRatio(layer)
        if shape_name == 'custom':
            source = source_custom(source_form)
            require(source['size_IU'] == size, "Custom anchor per-layer size differs from PCB source")
            anchor_code = int(item.GetAnchorPadShape(layer))
            expected_anchor = int(p.PAD_SHAPE_CIRCLE if source['anchor'] == 'circle' else p.PAD_SHAPE_RECTANGLE)
            require(anchor_code == expected_anchor, "Actual native custom anchor differs")
            native_local, local = merged_custom_polygon(p, item, layer, source['polygons_IU'])
            world = p.SHAPE_POLY_SET(native_local)
            world.Rotate(item.GetOrientation())
            world.Move(item.GetPosition())
            world_rows = polygon_rows(world)
            predicted = [transform(point, matrix, position) for point in local[0]['outer']]
            require(len(world_rows) == 1 and not world_rows[0]['holes'] and
                    world_rows[0]['outer'] == predicted, "Official and exact integer custom transforms differ")
            raw_primitives = [{'type': 'filled_polygon', 'width_IU': 0, 'filled': True,
                               'raw_PCB_source_pad_local_IU': source['polygons_IU'][0],
                               'native_merged_pad_local_IU': local, 'native_world_IU': world_rows,
                               'native_accessor': 'PAD.MergePrimitivesAsPolygon(actual_layer, output, ERROR_INSIDE)',
                               'native_merged_polygon_equals_exact_stored_polygon': True}]
            row['custom'] = {'anchor_shape': source['anchor'], 'anchor_shape_code': anchor_code,
                             'anchor_size_IU': size, 'anchor_center_IU': position,
                             'raw_primitives': raw_primitives, 'exact_source_primitive_equality': True,
                             'anchor_containment_claimed': False}
        captured[name] = row
    require(set(captured) == set(original['copper']), "Actual pad copper layer coverage differs")
    return {'uuid': uid, 'key': original['key'], 'net': original['net'], 'position_IU': position,
            'absolute_angle_degrees': angle, 'official_integer_rotation_matrix_columns': matrix,
            'footprint_uuid': original['footprint_uuid'], 'footprint_side': footprint.GetLayerName(),
            'layers': captured, 'actual_drill_primitive_mm': actual_drill,
            'plated': original['plated'], 'npth': original['npth'], 'barrel_layers': original['barrel_layers'],
            'topology_or_anchor_containment_claimed': False}
