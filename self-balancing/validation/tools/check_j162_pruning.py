#!/usr/bin/python3
"""Independent local current-path proof for the exact approved J162 pruning."""
import os,json,hashlib,argparse
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
D=Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--packet',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();SRC=a.source;PACK=a.packet;sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();expected=a.sha256;assert sha(SRC)==expected;doc=json.loads(PACK.read_text());assert doc['source_sha256']==expected;b=p.LoadBoard(str(SRC));tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};uid=lambda t:t.m_Uuid.AsString();xy=lambda q:[round(p.ToMM(q.x),6),round(p.ToMM(q.y),6)];record=lambda t:{'id':uid(t),'net':t.GetNetname(),'layer':t.GetLayerName(),'start':xy(t.GetStart()),'end':xy(t.GetEnd()),'width_mm':round(p.ToMM(t.GetWidth()),6)};errors=[]
pad=next(q for f in b.GetFootprints() for q in f.Pads() if uid(q)==doc['pad_id']);l=p.B_Cu;ps=pad.GetEffectiveShape(l);removed=[tracks[r['id']] for r in doc['delta']['removed']];assert [record(t) for t in removed]==doc['delta']['removed'];assert doc['delta']['added']==[]
feeds=[]
for r in doc['retained_original_contact_edges']:
 t=tracks[r['id']];assert record(t)==r;ok=t.GetEffectiveShape(l).Collide(ps,0);feeds.append({'record':r,'directly_contacts_retained_pad':ok})
 if not ok:errors.append('Declared retained feed does not physically contact J162 pad')
ids={uid(t) for t in removed};boundary=[]
for obj in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]:
 if uid(obj) in ids or obj.GetNetname()!=pad.GetNetname() or not obj.IsOnLayer(l):continue
 shape=obj.GetEffectiveShape(l)
 if not any(t.GetEffectiveShape(l).Collide(shape,0) for t in removed):continue
 contact=uid(obj)==uid(pad) or shape.Collide(ps,0);row={'uuid':uid(obj),'kind':obj.GetClass(),'directly_contacts_retained_pad':contact}
 if isinstance(obj,p.PAD):row.update(ref=obj.GetParentFootprint().GetReference(),pin=obj.GetNumber())
 boundary.append(row)
 if not contact:errors.append('Removed route has external current-path contact outside native J162 pad: '+uid(obj))
poly=p.SHAPE_POLY_SET();pad.TransformShapeToPolygon(poly,l,0,100,p.ERROR_OUTSIDE);deleted=p.SHAPE_POLY_SET()
for t in removed:
 q=p.SHAPE_POLY_SET();t.TransformShapeToPolygon(q,l,0,100,p.ERROR_OUTSIDE);deleted.BooleanAdd(q)
outside=p.SHAPE_POLY_SET(deleted);outside.BooleanSubtract(poly)
report={'status':'PASS EXACT LOCAL J162 PAD/FEED REDUNDANCY PROOF; FINAL CANDIDATE MUST PRESERVE FEED RECORDS' if not errors else 'NOT PASSED','source_path':str(SRC),'source_sha256':expected,'proposal_path':str(PACK),'proposal_sha256':sha(PACK),'errors':errors,'pad_uuid':uid(pad),'pad_reference':pad.GetParentFootprint().GetReference()+'.'+pad.GetNumber(),'deleted_tracks':len(removed),'deleted_widths_mm':sorted({r['width_mm'] for r in doc['delta']['removed']}),'deleted_copper_outside_native_pad_mm2':outside.Area()/1e12,'retained_feeds':feeds,'all_external_contacts':boundary,'reason':'Every connection between deleted branch copper and retained conductors directly overlaps the same unchanged native J162 copper pad; all declared original feed segments physically touch that pad and remain independently frozen. The protruding redundant branch does not supply any separate terminal.','limits':'Final physical all-net connectivity, feed record equality, unchanged native pad, and no width-reduced replacements remain mandatory.'};a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert sha(SRC)==expected;raise SystemExit(bool(errors))
