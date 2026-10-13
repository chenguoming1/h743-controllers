from collections import defaultdict
from types import SimpleNamespace
def require(ok, message):
    if not ok: raise ValueError(message)
imp=SimpleNamespace(require=require)

def geometry_modules():
    from shapely.geometry import Polygon, LineString, Point
    from shapely.ops import unary_union
    from shapely.strtree import STRtree
    return Polygon, LineString, Point, unary_union, STRtree

def polygon_parts(shape):
    if shape.is_empty:
        return []
    if shape.geom_type == 'Polygon':
        return [shape]
    return [p for child in getattr(shape, 'geoms', ()) for p in polygon_parts(child)]

def native_polygons(rows):
    Polygon, _, _, unary_union, _ = geometry_modules()
    shapes = [Polygon(row['outer'], row.get('holes', [])) for row in rows]
    imp.require(all(p.is_valid and not p.is_empty and p.area > 0 for p in shapes), 'Invalid/degenerate native polygon; no repair permitted')
    return unary_union(shapes)

def hole_map(records, copper_layers):
    """A physical drill removes copper from every intersecting object/net."""
    _, _, _, unary_union, _ = geometry_modules()
    rows = defaultdict(list)
    for record in records:
        if not record.get('drill'):
            continue
        hole = native_polygons(record['drill']['outside'])
        layers = copper_layers if record.get('npth') else record.get('barrel_layers', [])
        imp.require(bool(layers), 'Drilled object lacks physical drill-layer evidence')
        for layer in layers:
            rows[layer].append(hole)
    return {layer: unary_union(shapes) for layer, shapes in rows.items()}

def conductive_shapes(record, global_holes=None):
    """Boolean drill subtraction only; original native contours remain untouched."""
    hole = native_polygons(record['drill']['outside']) if record.get('drill') else None
    copper = {layer: native_polygons(rows) for layer, rows in record['copper'].items() if rows}
    shapes = {layer: shape.difference(hole) if hole is not None else shape for layer, shape in copper.items()}
    if global_holes:
        shapes = {layer: shape.difference(global_holes[layer]) if layer in global_holes else shape
                  for layer, shape in shapes.items()}
    imp.require(all(p.is_valid for p in shapes.values()), 'Invalid drill-subtracted native geometry')
    return shapes, hole

def line_parts(shape):
    if shape.is_empty:
        return []
    if shape.geom_type in ('LineString', 'LinearRing'):
        return [shape]
    return [p for child in getattr(shape, 'geoms', ()) for p in line_parts(child)]

def native_records_with_fills(native):
    rows = list(native['objects'])
    rows.extend({'uuid': z['uuid'], 'net': z['net'], 'kind': 'saved_native_zone',
                 'copper': z['filled'], 'drill': None, 'plated': False, 'barrel_layers': []}
                for z in native['zones'] if not z['rule'] and any(z['filled'].values()))
    return rows
