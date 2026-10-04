import os,json,hashlib
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
D=Path(__file__).resolve().parents[1];A=D.parent/'controller-r3s-p6-route-cleanup/freeze-repairs/controller.kicad_pcb';B=D.parent/'controller-r3s-p6-route-cleanup/freeze-retirement/controller.kicad_pcb';sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();H='3c80eba2e6dfd7161f875436aff8c64bcaee0ad8d6cc94a55b24bfc5e2014e47';assert sha(B)==H;old=p.LoadBoard(str(A));new=p.LoadBoard(str(B));l=p.In2_Cu

def plane(b):
 out=p.SHAPE_POLY_SET()
 for z in b.Zones():
  if z.GetNetname()=='GND' and z.IsOnLayer(l) and z.HasFilledPolysForLayer(l):out.BooleanAdd(z.GetFilledPolysList(l))
 return out
P,Q=plane(old),plane(new);loss=p.SHAPE_POLY_SET(P);loss.BooleanSubtract(Q);gain=p.SHAPE_POLY_SET(Q);gain.BooleanSubtract(P);expanded=p.SHAPE_POLY_SET(Q);expanded.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);residual=p.SHAPE_POLY_SET(P);residual.BooleanSubtract(expanded);polys=[]
for i in range(residual.OutlineCount()):
 poly=p.SHAPE_POLY_SET(residual.COutline(i));bb=poly.BBox();box=[bb.GetLeft()/1e6,bb.GetTop()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6];assert 27.32<=box[0]<=box[2]<=27.41 and 14.23<=box[1]<=box[3]<=14.38;polys.append({'area_mm2':poly.Area()/1e12,'bbox_mm':box})
a=json.loads((D/'ground-plane-attachments-fafa9c3f.json').read_text());b=json.loads((D/'ground-plane-attachments-3c80eba2.json').read_text());checks=[]
for q in b['plane_results']:
 prior=next(x for x in a['plane_results'] if x['layer']==q['layer']);before={t['uuid']:t['connected_to_main_broad_plane_at_01302mm'] for t in prior['terminals']};after={t['uuid']:t['connected_to_main_broad_plane_at_01302mm'] for t in q['terminals']};assert before==after;checks.append({'layer':q['layer'],'all101_terminal_attachment_results_unchanged':True})
assert not b['errors'] and b['verified_reference_plane_terminal_attachments']==303
out={'status':'PASS BOUNDED SUPPLEMENTAL In2 GND FILL DISPOSITION','candidate_sha256':H,'source_sha256':sha(A),'audit_script_sha256':sha(Path(__file__)),'raw_loss_mm2':loss.Area()/1e12,'raw_gain_mm2':gain.Area()/1e12,'loss_beyond2nm_mm2':residual.Area()/1e12,'loss_polygons':polys,'bound_region_mm':[27.32,14.23,27.41,14.38],'ground_terminal_attachment_checks':checks,'reference_plane_terminal_checks':303,'disposition':'Only local native-fill fillets beside the actual FDCAN1_RX planar join change in supplemental In2 GND. All101 ground terminals retain identical broad-component attachment results on every filled layer, and all303 actual solid reference-plane attachments pass. The adjacent In3 reference is independently reproduced by the exact six-via-only refill proof; no new ordinary trace reference loss is allowed. In2 remains supplemental copper, not a claimed continuous reference plane.','limits':'Bounded native geometry and attachment evidence; not measured current, thermal or EMI certification.'};assert sha(B)==H;(D/'supplemental-In2-fill-3c80eba2.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
