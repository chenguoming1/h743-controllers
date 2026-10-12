"""Exact exporter overlay; original base exporter remains unchanged."""
import importlib.util,sys
from pathlib import Path
import polygon_native as poly
BASE=Path(__file__).resolve().parent/'export_native_copper.py'


BASE_SHA='d6f989ad9d7dc7e1264944cc2f334f70c5cae474b48843c3d1d6ee182716f19a'


SOURCE_BOARDS={'a7355c26018a7bea66b77ccdc5201c2042a96b8e6820179fc5684dc72e170b4f','01b115302e079c6c7a2b1370ef4a089c19c7c2b54fd13e73cf2341db2dffc133'}


def export(board_path,declaration_path=None,declaration_sha256=None):
 import pcbnew as pcb
 poly.require(pcb.GetBuildVersion()=='10.0.6+dfsg-1' and poly.sha(BASE)==BASE_SHA,'Pinned native exporter/runtime required')
 before=poly.sha(board_path)
 declaration=poly.load_bound_declaration(declaration_path,declaration_sha256) if declaration_path is not None else None
 poly.require(declaration is not None or before in SOURCE_BOARDS,'Unbound candidate export forbidden')
 sys.path.insert(0,str(BASE.parent))
 spec=importlib.util.spec_from_file_location('pinned_track_pad_zone_exporter',BASE);base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
 result=base.export(board_path);board=pcb.LoadBoard(str(board_path));graphics=[g for g in board.GetDrawings() if g.IsOnCopperLayer()]
 poly.require(result['board_sha256']==before,'Native board binding differs')
 if declaration is None:poly.require(not graphics,'Source board copper graphic inventory is not empty')
 else:
  poly.require(len(graphics)==1,'Exactly one whitelisted copper polygon required')
  record=poly.extract_shape(graphics[0],board,declaration['primitive'],pcb,base)
  poly.require(record['uuid'] not in {r['uuid'] for r in result['objects']} and record['uuid'] not in {r['uuid'] for r in result['zones']},'Polygon UUID collision')
  result['objects'].append(record);result['objects'].sort(key=lambda r:r['uuid'])
  result['single_copper_polygon_export']={'declaration_sha256':declaration_sha256,'recipe_sha256':declaration['complete_recipe_sha256'],'record_sha256':poly.digest(record),'original_exporter_sha256':BASE_SHA,'inside_and_outside_exact':True,'native_board_unchanged':True}
 poly.require(poly.sha(board_path)==before,'Read-only polygon export changed board')
 return result

