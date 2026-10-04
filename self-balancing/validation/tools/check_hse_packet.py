#!/usr/bin/python3
"""Independent read-only HSE proposal review on exact P5 source."""
import os,json,hashlib,collections,math
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
D=Path(__file__).resolve().parent;SRC=Path('/workspace/shared/storm32-redesign/controller-r3s-p5/controller.kicad_pcb');PACK=Path('/workspace/shared/storm32-redesign/research/controller-r3s-p6-critical-shapes/hse-approved-proposal-packet.json');sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();expected='6e2031b040ce8f3a534c2f73abb0091e25b3e6adcab982463264ad8898d65cf8';assert sha(SRC)==expected;packet=json.loads(PACK.read_text());assert packet['source_sha256']==expected;b=p.LoadBoard(str(SRC));objects=list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()];tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};uid=lambda t:t.m_Uuid.AsString();mm=lambda q:round(p.ToMM(q),6);xy=lambda q:[mm(q.x),mm(q.y)];errors=[];out=[];keep=[]
def rec(t):return {'id':uid(t),'net':t.GetNetname(),'layer':t.GetLayerName(),'start':xy(t.GetStart()),'end':xy(t.GetEnd()),'width_mm':mm(t.GetWidth())}
def copper(ts,l,thin=False):
 out=p.SHAPE_POLY_SET()
 for t in ts:
  if thin:
   q=p.PCB_TRACK(b);q.SetLayer(l);q.SetStart(t.GetStart());q.SetEnd(t.GetEnd());q.SetWidth(100)
  else:q=t
  poly=p.SHAPE_POLY_SET();q.TransformShapeToPolygon(poly,l,0,100,p.ERROR_OUTSIDE);out.BooleanAdd(poly)
 return out
holes=p.SHAPE_POLY_SET()
for q in objects:
 if isinstance(q,p.PCB_VIA) or isinstance(q,p.PAD) and q.HasHole():
  poly=p.SHAPE_POLY_SET();q.GetEffectiveHoleShape().TransformToPolygon(poly,100,p.ERROR_OUTSIDE);holes.BooleanAdd(poly)
for i,ch in enumerate(packet['changes']):
 old=[tracks[q['id']] for q in ch['removed']];assert [rec(t) for t in old]==ch['removed'];l=old[0].GetLayer();new=[]
 for r in ch['added']:
  t=p.PCB_TRACK(b);t.SetLayer(l);t.SetNetCode(old[0].GetNetCode());t.SetStart(p.VECTOR2I(*[round(v*1e6) for v in r['start']]));t.SetEnd(p.VECTOR2I(*[round(v*1e6) for v in r['end']]));t.SetWidth(round(r['width_mm']*1e6));new.append(t);keep.append(t)
 assert all(t.GetWidth()==150000 for t in old+new)
 ref={p.F_Cu:p.In1_Cu,p.B_Cu:p.In4_Cu}[l];plane=p.SHAPE_POLY_SET()
 for z in b.Zones():
  if not z.GetIsRuleArea() and z.GetNetname()=='GND' and z.IsOnLayer(ref):plane.BooleanAdd(z.GetFilledPolysList(ref))
 originalplane=p.SHAPE_POLY_SET(plane);plane.BooleanSubtract(holes)
 before=copper(old,l);after=copper(new,l);before.BooleanSubtract(plane);after.BooleanSubtract(plane);added=p.SHAPE_POLY_SET(after);added.BooleanSubtract(before)
 bc=copper(old,l,True);ac=copper(new,l,True);bc.BooleanSubtract(plane);ac.BooleanSubtract(plane);delta_c=p.SHAPE_POLY_SET(ac);delta_c.BooleanSubtract(bc)
 allowed=p.SHAPE_POLY_SET();named_envelope=p.SHAPE_POLY_SET();isolated_named_envelope=p.SHAPE_POLY_SET();voids=[]
 for vid in ch['same_net_reference_void_via_ids']:
  via=tracks[vid];assert via.GetNetname()==ch['net']
  vp=p.SHAPE_POLY_SET();via.TransformShapeToPolygon(vp,ref,150000,b.GetDesignSettings().m_MaxError,p.ERROR_OUTSIDE);named_envelope.BooleanAdd(vp)
  for oi in range(originalplane.OutlineCount()):
   for hi in range(originalplane.HoleCount(oi)):
    hole=p.SHAPE_POLY_SET(originalplane.CHole(oi,hi))
    if not hole.Contains(via.GetPosition()):continue
    contained=[{'id':uid(v),'net':v.GetNetname(),'xy':xy(v.GetPosition())} for v in objects if isinstance(v,p.PCB_VIA) and hole.Contains(v.GetPosition())]
    voids.append({'via_uuid':vid,'hole_area_mm2':hole.Area()/1e12,'contained_vias':contained});allowed.BooleanAdd(hole)
 # Obtain an isolated, already-filled antipad with identical via geometry,
 # clearance, and netclass, then translate its exact native contour.
 for vid in ch['same_net_reference_void_via_ids']:
  target=tracks[vid]
  for sample in [tracks['060b047c-d688-49da-9f40-03b3572d6506']]:
   assert sample.GetWidth(ref)==target.GetWidth(ref) and sample.GetOwnClearance(ref)==target.GetOwnClearance(ref) and sample.GetNetClassName()==target.GetNetClassName()
   for oi in range(originalplane.OutlineCount()):
    for hi in range(originalplane.HoleCount(oi)):
     hp=p.SHAPE_POLY_SET(originalplane.CHole(oi,hi))
     if hp.Contains(sample.GetPosition()):
      residents=[v for v in objects if isinstance(v,p.PCB_VIA) and hp.Contains(v.GetPosition())];assert len(residents)==1
      hp.Move(target.GetPosition()-sample.GetPosition());isolated_named_envelope.BooleanAdd(hp)
 isolated_foreign=p.SHAPE_POLY_SET(added);isolated_foreign.BooleanSubtract(isolated_named_envelope)
 isolated_foreign_c=p.SHAPE_POLY_SET(delta_c);isolated_foreign_c.BooleanSubtract(isolated_named_envelope)
 foreign=p.SHAPE_POLY_SET(added);foreign.BooleanSubtract(allowed);foreign_c=p.SHAPE_POLY_SET(delta_c);foreign_c.BooleanSubtract(allowed)
 outside_named=p.SHAPE_POLY_SET(added);outside_named.BooleanSubtract(named_envelope);outside_named_c=p.SHAPE_POLY_SET(delta_c);outside_named_c.BooleanSubtract(named_envelope)
 if isolated_foreign.Area()>=1 or isolated_foreign_c.Area()>=1:errors.append('New exposure outside translated exact isolated native antipad: '+str(i))
 if foreign.Area()>=1 or foreign_c.Area()>=1:errors.append('New reference exposure outside named via hole: '+str(i))
 # Confirm changed copper remains within a .15mm neighborhood of original.
 vicinity=copper(old,l);vicinity.Inflate(150000,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,100);outside=copper(new,l);outside.BooleanSubtract(vicinity)
 if outside.Area()>=1:errors.append('Proposal extends beyond local .15mm corridor: '+str(i))
 old_ids={uid(t) for t in old};lost=[];near=[]
 for obj in objects:
  if uid(obj) in old_ids or not obj.IsOnLayer(l):continue
  shape=obj.GetEffectiveShape(l)
  if obj.GetNetname()==ch['net']:
   touched=any(t.GetEffectiveShape(l).Collide(shape,0) for t in old);retained=any(t.GetEffectiveShape(l).Collide(shape,0) for t in new)
   if touched and not retained:lost.append({'uuid':uid(obj),'class':obj.GetClass()})
  else:
   gap=min(t.GetEffectiveShape(l).GetClearance(shape) for t in new);required=160000 if isinstance(obj,p.PCB_TRACK) and not isinstance(obj,p.PCB_VIA) else 150000
   if gap<required:near.append({'uuid':uid(obj),'net':obj.GetNetname(),'gap_mm':mm(gap),'required_mm':mm(required)})
 if lost:errors.append('Lost original same-net external copper contacts: '+str(i))
 if near:errors.append('New copper below declared foreign spacing: '+str(i))
 out.append({'operation_index':i,'net':ch['net'],'layer':ch['layer'],'old_count':len(old),'new_count':len(new),'width_mm':.15,'old_length_mm':sum(t.GetLength() for t in old)/1e6,'new_length_mm':sum(t.GetLength() for t in new)/1e6,'new_reference_edge_area_mm2':added.Area()/1e12,'new_reference_centerline_tube_area_mm2':delta_c.Area()/1e12,'new_foreign_edge_area_mm2':foreign.Area()/1e12,'new_foreign_centerline_tube_area_mm2':foreign_c.Area()/1e12,'new_edge_outside_translated_isolated_antipad_mm2':isolated_foreign.Area()/1e12,'new_centerline_outside_translated_isolated_antipad_mm2':isolated_foreign_c.Area()/1e12,'new_edge_outside_named_via_clearance_mm2':outside_named.Area()/1e12,'new_centerline_outside_named_via_clearance_mm2':outside_named_c.Area()/1e12,'isolated_reference_via_uuid':'060b047c-d688-49da-9f40-03b3572d6506','isolated_reference_conditions':'Same reference plane, .450mm via copper, .150mm local clearance, Default netclass; native sample hole contains only source HSE_IN via','named_via_clearance_polygon_error_mm':b.GetDesignSettings().m_MaxError/1e6,'named_via_holes':voids,'outside_original_0150mm_corridor_mm2':outside.Area()/1e12,'lost_external_contacts':lost,'foreign_spacing_violations':near})
assert sha(SRC)==expected
report={'status':'PASS LOCAL HSE PROPOSAL GEOMETRY; FINAL NATIVE GATE STILL REQUIRED' if not errors else 'NOT PASSED','source_sha256':expected,'proposal_path':str(PACK),'proposal_sha256':sha(PACK),'errors':errors,'operations':out,'limits':'Independent local reference and geometry check. Masks/drills/full topology/native ERC/DRC are still required on the frozen integrated candidate. No physical oscillator performance or SI claim.'};(D/'hse-proposal-independent.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(errors))
