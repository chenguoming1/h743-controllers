"""Inert narrow exact-polygon support; does not grant any execution lease."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / 'recovery-negotiated-routing-20261011/source7-native5-sck-red-polygon-native-preparation-v3'
BOARD = ROOT / 'recovery-negotiated-routing-20261011/native4-return-stitch-native-preparation-v1/outputs/native4-return-stitch-v1/diagnostic-board/f722-heli.kicad_pcb'
BOARD_SHA = '8f9d4be2fc97633bd9d83b2bc44be7cd4359eb45b90c14fbd410187292136029'
NATIVE_SHA = '02c72e195b5c2cde307ec83ed587b07dc0c18565892afd2b7bf16f6602986034'
RECORD_SHA = '1967c500863506c0080afe83b234c7f7a4e93c387d1be7f4f74fa76b28179e3c'
DECLARATION_SHA = 'ad95d4f083ca2890905878237139317c633a565ff57f595bcfea044236bad2e3'

def require(value, message):
    if not value:
        raise ValueError(message)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def validate_source(record):
    """Bind native contour independently to the exact source PCB's gr_poly AST."""
    require(hashlib.sha256(BOARD.read_bytes()).hexdigest() == BOARD_SHA, 'Native4 board bytes changed')
    declaration_path = CANDIDATE / 'polygon-declaration.json'
    require(hashlib.sha256(declaration_path.read_bytes()).hexdigest() == DECLARATION_SHA, 'Polygon declaration changed')
    declaration = json.loads(declaration_path.read_bytes())
    poly = load('native4_polygon_seal', CANDIDATE / 'polygon_native.py')
    poly.verify_record(record, declaration['primitive'])
    require(digest(record) == RECORD_SHA, 'Exact native4 polygon record changed')
    parser = load('native4_board_parser', ROOT / 'power-recovery-prep/prepare_final_power.py')
    tree = parser.parse_board(BOARD.read_text())
    copper_graphics = [node for node in tree if isinstance(node, list) and node and node[0].startswith('gr_')
                       and any(field[1].endswith('.Cu') for field in parser.children(node, 'layer'))]
    require(len(copper_graphics) == 1, 'Unexpected source copper graphic inventory')
    node = copper_graphics[0]
    require(node[0] == 'gr_poly' and parser.one(node, 'uuid')[1] == record['uuid'], 'Source polygon identity differs')
    require(parser.one(node, 'net')[1] == 'VX_PROTECTED' and parser.one(node, 'layer')[1] == 'In2.Cu', 'Source polygon net/layer differs')
    require(parser.one(node, 'fill')[1] == 'yes' and parser.one(parser.one(node, 'stroke'), 'width')[1] == '0', 'Source polygon fill/stroke differs')
    points = [[poly.nm(x), poly.nm(y)] for _, x, y in parser.one(node, 'pts')[1:]]
    require(poly.ring_id(points) == poly.ring_id(record['outer_nm']), 'PCB AST integer polygon differs from native contour')
    return declaration['primitive']

def bounds(record, layer):
    validate_source(record)
    require(layer == 'In2.Cu', 'Unexpected polygon layer')
    # A sealed zero-stroke filled integer polygon is its exact own inner/outer
    # bound. No capsule, convex hull, buffer, epsilon, or track substitution.
    rows = [{'outer': copy.deepcopy(record['outer_nm']), 'holes': []}]
    return copy.deepcopy(rows), copy.deepcopy(rows), {'schema': 'exact-native4-filled-polygon/v1'}
