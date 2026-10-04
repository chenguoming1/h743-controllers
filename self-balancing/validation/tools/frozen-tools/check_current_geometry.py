#!/usr/bin/python3
"""Read-only current native orientation, pad-map and via-rule evidence."""
import os
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import argparse,collections,csv,hashlib,json,pathlib
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('--project',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--approved-small-vias',type=pathlib.Path,help='Explicitly owner-approved seven-via allowance JSON; exact hash/UUID/geometry only');a=ap.parse_args();D=a.project.resolve();O=a.out.resolve();O.mkdir(exist_ok=True,parents=True);src=D/'controller.kicad_pcb';h=hashlib.sha256(src.read_bytes()).hexdigest();project_path=D/'controller.kicad_pro';project_hash=hashlib.sha256(project_path.read_bytes()).hexdigest();rules=json.loads(project_path.read_text())['board']['design_settings']['rules'];b=p.LoadBoard(str(src));fps={f.GetReference():f for f in b.GetFootprints()};errors=[]
def xy(pt):return [round(p.ToMM(pt.x),6),round(p.ToMM(pt.y),6)]
def check(ok,why):
 if not ok:errors.append(why)
def polygons(poly):
 out=[]
 for i in range(poly.OutlineCount()):
  outline=poly.Outline(i);outer=[xy(outline.CPoint(j)) for j in range(outline.PointCount())];holes=[]
  for k in range(poly.HoleCount(i)):
   hole=poly.Hole(i,k);holes.append([xy(hole.CPoint(j)) for j in range(hole.PointCount())])
  out.append({'outer':outer,'holes':holes})
 return out
geo={'native_path':str(src),'native_sha256':h,'fab':[],'silk':[],'copper_pads':[]}
for ref,f in fps.items():
 side='Bottom' if f.GetLayer()==p.B_Cu else 'Top';cu=p.B_Cu if side=='Bottom' else p.F_Cu
 for name,layer in [('fab',p.B_Fab if side=='Bottom' else p.F_Fab),('silk',p.B_SilkS if side=='Bottom' else p.F_SilkS)]:
  for g in f.GraphicalItems():
   if g.GetClass()!='PCB_SHAPE' or g.GetLayer()!=layer:continue
   poly=p.SHAPE_POLY_SET();g.TransformShapeToPolygon(poly,layer,0,1000,p.ERROR_OUTSIDE);geo[name].append({'ref':ref,'side':side,'polygons':polygons(poly)})
 for pad in f.Pads():
  if not pad.IsOnLayer(cu):continue
  poly=p.SHAPE_POLY_SET();pad.TransformShapeToPolygon(poly,cu,0,1000,p.ERROR_OUTSIDE);geo['copper_pads'].append({'ref':ref,'side':side,'pad':pad.GetNumber(),'position':xy(pad.GetPosition()),'polygons':polygons(poly)})
q=fps['Q2'];check(xy(q.GetPosition())==[18.75,26.425] and q.GetLayer()==p.B_Cu and q.GetOrientationDegrees()%360==90,'Q2 placement drift');check(str(q.GetFPID().GetLibNickname())+':'+str(q.GetFPID().GetLibItemName())=='Controller_R3:DMN2310UW_SOT323','Q2 footprint drift');check(q.GetValue()=='DMN2310UW-7' and q.GetFieldByName('LCSC').GetText()=='C7264627','Q2 identity drift')
q2pads={x.GetNumber():x for x in q.Pads()};expected={'1':([19.4,27.375],'USB_SOURCE_DISABLE'),'2':([18.1,27.375],'GND'),'3':([18.75,25.475],'/power/USB_SWITCH_ON')}
for n,(pos,net) in expected.items():
 pad=q2pads[n];check(xy(pad.GetPosition())==pos and pad.GetNetname()==net,'Q2 pad'+n+' G/S/D position or net drift');check(xy(pad.GetSize())==[.6,.47] and pad.GetShape()==p.PAD_SHAPE_RECT,'Q2 official land geometry drift')
check(fps['Q1'].GetValue()=='2N7002' and fps['Q1'].GetFieldByName('LCSC').GetText()=='C8545','Q1 unexpected substitution');check(fps['R43'].GetValue()=='10k' and fps['R43'].GetFieldByName('LCSC').GetText()=='C25804','R43 identity drift')
wire=list(csv.DictReader((D/'review/pad-wiring-map.csv').open()));check(len(wire)==67,'Expected67 wire-pad map rows');check(len({q['Reference'] for q in wire})==67,'Duplicate wire-pad map references');moved={}
for w in wire:
 f=fps[w['Reference']];pad=list(f.Pads())[0];pos=xy(pad.GetPosition());side='Bottom' if f.GetLayer()==p.B_Cu else 'Top';check(pos==[float(w['Native X mm']),float(w['Native Y mm'])] and side==w['Side'] and pad.GetNetname().split('/')[-1]==w['Net'],'Pad-map/native mismatch: '+w['Reference'])
 if w['Net'] in ['ADC1_RAW','ADC2_RAW','ADC3_RAW','SWDIO','SWCLK','NRST']:moved[w['Net']]={'reference':w['Reference'],'position':pos,'side':side}
for net,x in [('ADC1_RAW',12),('ADC2_RAW',14),('ADC3_RAW',16),('SWDIO',24),('SWCLK',26),('NRST',28)]:check(moved.get(net,{}).get('position')==[x,36.5] and moved.get(net,{}).get('side')=='Bottom','Moved pad wrong: '+net)
legend=json.loads((D/'review/printed-pad-legend.json').read_text());check(legend['native_sha256']==h and legend['identified_pad_count']==67,'Printed-pad legend not current')
approved_doc=json.loads(a.approved_small_vias.read_text()) if a.approved_small_vias else None
approved={q['uuid']:q for q in approved_doc['small_vias']} if approved_doc else {}
if approved_doc:
 check(approved_doc['board_sha256']==h,'Approved via inventory source hash differs');check(approved_doc.get('project_sha256')==project_hash,'Approved via project hash differs');check(len(approved)==approved_doc['small_via_count']==7,'Approved via inventory must contain exactly seven unique vias');check(approved_doc['all_vias_are_through'] is True,'Approved inventory contains non-through vias')
required_rules={'min_clearance':.15,'min_hole_to_hole':.25,'min_through_hole_diameter':.2,'min_track_width':.13,'min_copper_edge_clearance':.25,'min_via_diameter':.35 if approved_doc else .4,'min_via_annular_width':.075 if approved_doc else .1}
for name,value in required_rules.items():check(rules.get(name)==value,'Unexpected project manufacturing rule: '+name)
if approved_doc:check(approved_doc.get('required_project_rules')==required_rules,'Approved via rule declaration differs')
vias=[];seen_small=set()
for v in b.GetTracks():
 if isinstance(v,p.PCB_VIA):
  diameter=p.ToMM(v.GetWidth(p.F_Cu));drill=p.ToMM(v.GetDrillValue());uuid=v.m_Uuid.AsString();vias.append({'uuid':uuid,'position':xy(v.GetPosition()),'diameter_mm':diameter,'drill_mm':drill,'net':v.GetNetname()})
  if diameter<.4:
   seen_small.add(uuid);q=approved.get(uuid,{});check(q.get('xy_mm')==xy(v.GetPosition()) and q.get('net')==v.GetNetname() and q.get('diameter_mm')==diameter==.35 and q.get('drill_mm')==drill==.2 and q.get('annulus_mm')==.075 and q.get('through_via') is True and v.GetViaType()==p.VIATYPE_THROUGH,'Unapproved or changed small via: '+uuid)
  else:check(drill>=.2 and diameter-drill>=.15-1e-8,'Via violates minimum drill or annulus')
check(seen_small==set(approved),'Actual small-via set differs from explicitly approved inventory')
check(hashlib.sha256(src.read_bytes()).hexdigest()==h and hashlib.sha256(project_path.read_bytes()).hexdigest()==project_hash,'Source changed during extraction')
(O/'geometry.json').write_text(json.dumps(geo)+'\n');report={'status':'PASS NATIVE GEOMETRY CONSISTENCY' if not errors else 'NOT PASSED','native_sha256':h,'project_sha256':project_hash,'required_project_rules':required_rules,'errors':errors,'q2':{'identity':'DMN2310UW-7/C7264627','native_position_mm':[18.75,26.425],'side':'Bottom','angle_deg':90,'cpl_mm':[18.75,11.575],'pad_order':['1 Gate','2 Source','3 Drain'],'pad_positions':{n:pos for n,(pos,net) in expected.items()},'human_component_face_pin1':'lower-left','cue':'No dedicated silk/Fab pin1 marker in custom rectangle; use explicit numbered assembly drawing','supplier_zero_angle':'Native pose unchanged; supplier CPL0deg user correction; supplier model/pin1 qualification pending'},'wire_pad_count':len(wire),'moved_wire_pads':moved,'approved_small_via_inventory':'approved-small-vias.json' if approved_doc else None,'approved_small_via_count':len(approved),'approved_small_via_inventory_sha256':hashlib.sha256(a.approved_small_vias.read_bytes()).hexdigest() if a.approved_small_vias else None,'via_count':len(vias),'via_diameter_drill_counts':dict(collections.Counter(str((v['diameter_mm'],v['drill_mm'])) for v in vias)),'minimum_via_diameter_mm':min(v['diameter_mm'] for v in vias),'minimum_via_drill_mm':min(v['drill_mm'] for v in vias),'minimum_radial_annulus_mm':min((v['diameter_mm']-v['drill_mm'])/2 for v in vias),'scope':'Native geometry and recorded maps only; supplier rotation, process acceptance and physical performance pending'};(O/'current-geometry-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(errors))
