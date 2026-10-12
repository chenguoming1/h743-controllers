"""Exact single-polygon native checks with portable declaration lookup."""
import hashlib,json,uuid
from decimal import Decimal
from pathlib import Path
def load_bound_declaration(path,expected_sha):
    path=Path(path)
    root=Path(__file__).resolve().parent.parent
    provenance=json.loads((root/'SOURCE-PROVENANCE.json').read_text())
    row=next(r for r in provenance['files'] if r['path']=='runtime/polygon-declaration.json')
    require(expected_sha==row['original']['sha256'] and sha(path)==row['publication']['sha256'],'Polygon declaration changed')
    value=json.loads(path.read_text());recipe=json.loads((root/'recipe/compiled-additive-recipe-v1.json').read_text())
    validate_row(value['primitive'])
    require(recipe['proposed_add_copper_polygons']==[value['primitive']] and CUT in recipe['remove_source_records'],'Polygon recipe differs')
    return value


SCHEMA='f722-single-VX-SCK-copper-polygon/v1'


SOURCE_NATIVE_SHA='53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505'


CURRENT_NATIVE_SHA='46d0b78c82003a3042e68ea2258fa40e5032499b3c3dc864594519c9178821ea'


CUT='14057d3c-d767-4d99-943d-4bb2d23fa0ac'


OUTER_NM_SHA='d479ad76aedc67431e95e91ca98b676b4928fc8dcd2e24cd001a4a3394a1c2c2'


def require(value,message):
 if not value:raise ValueError(message)


def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()


def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def nm(v):
 n=Decimal(str(v))*1000000;require(n.is_finite() and n==n.to_integral_value(),'Non-integer native vertex');return int(n)


def ring_id(v):
 rows=tuple(tuple(x) for x in v)
 require(len(rows)>=3,'Empty polygon ring')
 return min(r[i:]+r[:i] for r in [rows,rows[::-1]] for i in range(len(r)))


def polygon_id(v):
 require(len(v)==1 and v[0]['holes']==[],'Expected exactly one contour without holes')
 return ring_id([[nm(x),nm(y)] for x,y in v[0]['outer']])


def validate_row(row):
 require(set(row)=={'kind','uuid','net','layer','outer_nm','holes_nm','filled','stroke_width_nm','replaces_source_uuid'},'Polygon primitive schema differs')
 require(row['kind']=='copper_polygon' and row['net']=='VX_PROTECTED' and row['layer']=='In2.Cu','Only the exact VX In2 polygon type is supported')
 require(row['filled'] is True and type(row['stroke_width_nm']) is int and row['stroke_width_nm']==0 and row['holes_nm']==[],'Only one solid zero-stroke hole-free polygon is supported')
 require(row['replaces_source_uuid']==CUT and str(uuid.UUID(row['uuid']))==row['uuid'] and row['uuid']!=CUT,'Wrong replaced source or new polygon UUID')
 points=row['outer_nm'];require(len(points)==586 and len({tuple(v) for v in points})==586,'Exact planned 586 unique vertices required')
 require(all(len(v)==2 and all(type(x) is int for x in v) and 24600000<=v[0]<=28700000 and 8300000<=v[1]<=11600000 for v in points),'Polygon coordinates must be sealed native integers within the fixed VX region')
 require(digest(points)==OUTER_NM_SHA,'Polygon differs from the exact whitelisted quantized VX contour')
 require(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:]+points[:1]))!=0,'Zero-area polygon')
 return row


def verify_record(record,row):
 validate_row(row)
 require(set(record)=={'kind','uuid','net','net_code','layer','outer_nm','holes_nm','filled','stroke_width_nm','copper','inside','mask','drill','barrel_layers','plated'},'Exported polygon record schema differs')
 require(all(record[k]==row[k] for k in ['kind','uuid','net','layer','holes_nm','filled','stroke_width_nm']),'Native polygon identity/net/settings differ')
 require(type(record['net_code']) is int and record['net_code']>0,'Native polygon must have an assigned net')
 require(ring_id(record['outer_nm'])==ring_id(row['outer_nm']),'Native integer polygon contour changed')
 require(set(record['copper'])==set(record['inside'])=={'In2.Cu'},'Native polygon layer changed')
 for key in ['copper','inside']:require(polygon_id(record[key]['In2.Cu'])==ring_id(row['outer_nm']),'Native '+key+' polygon differs from the exact sealed contour')
 require(record['mask']=={} and record['drill'] is None and record['barrel_layers']==[] and record['plated'] is False,'Polygon gained mask/drill/barrel geometry')
 return {'uuid':row['uuid'],'contour_sha256':digest(row['outer_nm']),'native_record_sha256':digest(record),'exact_inside_and_outside_contours':True,'maximum_vertex_displacement_nm':0}


def extract_shape(shape,board,row,pcb,base_exporter):
 validate_row(row)
 require(isinstance(shape,pcb.PCB_SHAPE) and shape.GetShape()==pcb.SHAPE_T_POLY,'Expected native PCB_SHAPE POLY')
 require(not shape.GetParentFootprint() and shape.IsConnected(),'Polygon must be a native connectable board copper item')
 require(shape.IsSolidFill() and not shape.IsHatchedFill() and not shape.IsProxyItem(),'Native polygon must be plain solid fill')
 require(shape.GetWidth()==0 and not shape.HasSolderMask(),'Native polygon stroke or mask differs')
 poly=shape.GetPolyShape();require(poly.OutlineCount()==1 and poly.HoleCount(0)==0,'Native polygon topology differs')
 outline=poly.Outline(0);require(outline.IsClosed(),'Native polygon is open')
 points=[[outline.CPoint(i).x,outline.CPoint(i).y] for i in range(outline.PointCount())]
 layer=shape.GetLayer();require(board.GetLayerName(layer)=='In2.Cu','Wrong native polygon layer')
 record={'kind':'copper_polygon','uuid':shape.m_Uuid.AsString(),'net':shape.GetNetname(),'net_code':shape.GetNetCode(),'layer':'In2.Cu','outer_nm':points,'holes_nm':[],'filled':True,'stroke_width_nm':0,'copper':{'In2.Cu':base_exporter.shape_polygons(shape,layer,pcb.ERROR_OUTSIDE,clearance=0)},'inside':{'In2.Cu':base_exporter.shape_polygons(shape,layer,pcb.ERROR_INSIDE,clearance=0)},'mask':{},'drill':None,'barrel_layers':[],'plated':False}
 verify_record(record,row);return record


def add_shape(board,declaration_path,declaration_sha256,pcb):
 """Add the exact source-bound polygon; does not save or refill."""
 declaration=load_bound_declaration(declaration_path,declaration_sha256)
 row=validate_row(declaration['primitive'])
 require(pcb.GetBuildVersion()=='10.0.6+dfsg-1','Pinned native version required')
 require(not [x for x in board.GetDrawings() if x.IsOnCopperLayer()],'Source must contain zero board-level copper graphics')
 net=board.FindNet(row['net']);require(net is not None,'Existing VX net required')
 poly=pcb.SHAPE_POLY_SET();poly.NewOutline()
 for x,y in row['outer_nm']:poly.Append(x,y)
 poly.Outline(0).SetClosed(True)
 shape=pcb.PCB_SHAPE(board);shape.SetShape(pcb.SHAPE_T_POLY);shape.SetPolyShape(poly);shape.SetFilled(True);shape.SetWidth(0);shape.SetLayer(board.GetLayerID('In2.Cu'));shape.SetNet(net);shape.SetHasSolderMask(False);shape.SetUuid(pcb.KIID(row['uuid']));board.Add(shape)
 return shape

