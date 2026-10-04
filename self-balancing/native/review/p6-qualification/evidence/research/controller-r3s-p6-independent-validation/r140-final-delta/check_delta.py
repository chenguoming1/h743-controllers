#!/usr/bin/python3
"""Exact bounded R140 delta; preserve every completed proof outside this run."""
import argparse,collections,copy,hashlib,json,os,re
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
BASE='3c80eba2e6dfd7161f875436aff8c64bcaee0ad8d6cc94a55b24bfc5e2014e47'
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();uid=lambda q:q.m_Uuid.AsString()
def parse(path):
 stack=[];root=None
 for t in re.findall(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]',path.read_text()):
  if t=='(':
   x=[]
   if stack:stack[-1].append(x)
   stack.append(x)
  elif t==')':root=stack.pop()
  else:stack[-1].append(t)
 assert not stack;return root
def stable(root):
 root=copy.deepcopy(root)
 for n in list(root):
  if not isinstance(n,list) or not n:continue
  if n[0] in ['segment','arc']:root.remove(n)
  if n[0]=='zone':n[:]=[q for q in n if not(isinstance(q,list) and q and q[0] in ['filled_polygon','fill_segments'])]
 return root
def rec(t):return {'id':uid(t),'net':t.GetNetname(),'layer':t.GetLayerName(),'start':[round(t.GetStart().x/1e6,6),round(t.GetStart().y/1e6,6)],'end':[round(t.GetEnd().x/1e6,6),round(t.GetEnd().y/1e6,6)],'width_mm':t.GetWidth()/1e6}
def geom(t):return t['net'],t['layer'],tuple(t['start']),tuple(t['end']),t['width_mm']
def poly(ts,l):
 out=p.SHAPE_POLY_SET()
 for t in ts:
  q=p.SHAPE_POLY_SET();t.TransformShapeToPolygon(q,l,0,50,p.ERROR_OUTSIDE);out.BooleanAdd(q)
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--packet',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert sha(a.baseline)==BASE and sha(a.candidate)==a.sha256;packet=json.loads(a.packet.read_text());assert packet['source_sha256']==BASE;ch=packet['operation'];old=p.LoadBoard(str(a.baseline));new=p.LoadBoard(str(a.candidate));A={uid(q):q for q in old.GetTracks() if not isinstance(q,p.PCB_VIA)};B={uid(q):q for q in new.GetTracks() if not isinstance(q,p.PCB_VIA)};ar={u:rec(q) for u,q in A.items()};br={u:rec(q) for u,q in B.items()};removed={u:r for u,r in ar.items() if br.get(u)!=r};added={u:r for u,r in br.items() if ar.get(u)!=r};errors=[]
 def check(x,msg):
  if not x:errors.append(msg)
 check(removed=={q['id']:q for q in ch['removed']},'Actual removed tracks exceed exact five source records');check(collections.Counter(geom(q) for q in added.values())==collections.Counter(geom(q) for q in ch['added']),'Added copper differs from exact three authorized routes');check(stable(parse(a.baseline))==stable(parse(a.candidate)),'Native non-route fields, via, component or zone definition changed');check(len(ar)==3180 and len(br)==3178,'Expected exact3180 to3178 track delta')
 l=p.B_Cu;ats=[A[u] for u in removed];bts=[B[u] for u in added];land_checks=[]
 for q in list(old.GetTracks())+[pd for f in old.GetFootprints() for pd in f.Pads()]:
  if not isinstance(q,(p.PAD,p.PCB_VIA)) or q.GetNetname()!='UART3_TX' or not q.IsOnLayer(l):continue
  ca=any(t.GetEffectiveShape(l).GetClearance(q.GetEffectiveShape(l))<=0 for t in ats);cb=any(t.GetEffectiveShape(l).GetClearance(q.GetEffectiveShape(l))<=0 for t in bts)
  if not(ca or cb):continue
  check(ca==cb,'Changed terminal contact set');check(isinstance(q,p.PCB_VIA),'Unexpected direct pad involvement');apoly=poly(ats,l);bpoly=poly(bts,l);land=poly([q],l);apoly.BooleanIntersection(land);bpoly.BooleanIntersection(land);loss=p.SHAPE_POLY_SET(apoly);loss.BooleanSubtract(bpoly);gain=p.SHAPE_POLY_SET(bpoly);gain.BooleanSubtract(apoly);ea=p.SHAPE_POLY_SET(apoly);ea.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);eb=p.SHAPE_POLY_SET(bpoly);eb.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);lr=p.SHAPE_POLY_SET(apoly);lr.BooleanSubtract(eb);gr=p.SHAPE_POLY_SET(bpoly);gr.BooleanSubtract(ea);check(lr.Area()==gr.Area()==0,'Within-land approach copper changed beyond2nm');land_checks.append({'uuid':uid(q),'raw_loss_mm2':loss.Area()/1e12,'raw_gain_mm2':gain.Area()/1e12,'loss_beyond2nm_mm2':lr.Area()/1e12,'gain_beyond2nm_mm2':gr.Area()/1e12})
 check(len(land_checks)==2,'Expected two unchanged via approaches')
 zones=[];oldzones={uid(z):z for z in old.Zones()}
 for z in new.Zones():
  if z.GetIsRuleArea():continue
  for layer in new.GetEnabledLayers().CuStack():
   if not z.IsOnLayer(layer):continue
   a_poly=oldzones[uid(z)].GetFilledPolysList(layer);b_poly=z.GetFilledPolysList(layer);loss=p.SHAPE_POLY_SET(a_poly);loss.BooleanSubtract(b_poly);gain=p.SHAPE_POLY_SET(b_poly);gain.BooleanSubtract(a_poly);check(loss.Area()==gain.Area()==0,'Filled zone copper changed');zones.append({'uuid':uid(z),'layer':new.GetLayerName(layer),'loss_mm2':loss.Area()/1e12,'gain_mm2':gain.Area()/1e12})
 out={'status':'PASS EXACT R140-ONLY DELTA' if not errors else 'NOT PASSED','baseline_sha256':BASE,'candidate_sha256':a.sha256,'errors':errors,'packet_sha256':sha(a.packet),'audit_script_sha256':sha(Path(__file__)),'removed':list(removed.values()),'added':list(added.values()),'all_other_native_semantics_unchanged':stable(parse(a.baseline))==stable(parse(a.candidate)),'direct_pad_attachment_geometry_unchanged':True,'unchanged_via_approaches':land_checks,'filled_zone_deltas':zones,'track_count':len(br),'scope':__doc__};assert sha(a.baseline)==BASE and sha(a.candidate)==a.sha256;a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'errors':errors,'tracks':len(br)},indent=2));return bool(errors)
if __name__=='__main__':raise SystemExit(main())
